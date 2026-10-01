"""Bearer-token authentication against the Keycloak realm backing this deployment."""

import time
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=True)

_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 300


async def _fetch_jwks() -> dict[str, Any]:
    """
    Arg: none.
    Operation: fetches the realm's JSON Web Key Set from Keycloak and refreshes the cache.
               Raises httpx.HTTPError if Keycloak is unreachable or returns an error status.
    Return: the JWKS document.
    """
    global _jwks_cache, _jwks_fetched_at
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.keycloak_jwks_uri, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_fetched_at = time.monotonic()
        return _jwks_cache


async def _get_jwks(force_refresh: bool = False) -> dict[str, Any]:
    """
    Arg: force_refresh - bypass the cache, used when a token references an unknown key.
    Operation: returns the cached JWKS while it is fresh, otherwise fetches a new one.
    Return: the JWKS document.
    """
    is_fresh = _jwks_cache and (time.monotonic() - _jwks_fetched_at) < _JWKS_TTL
    if is_fresh and not force_refresh:
        return _jwks_cache
    return await _fetch_jwks()


def _decode(token: str, jwks: dict[str, Any]) -> dict[str, Any]:
    """
    Arg: token - raw bearer token; jwks - key set to verify the signature against.
    Operation: verifies signature, expiry and issuer. The audience is checked separately
               because Keycloak issues 'account' as the default audience for public
               clients. Raises JWTError when any check fails.
    Return: the decoded token claims.
    """
    return jwt.decode(
        token,
        jwks,
        algorithms=["RS256"],
        issuer=settings.keycloak_issuer,
        options={"verify_aud": False},
    )


def _assert_intended_for_this_client(claims: dict[str, Any]) -> None:
    """
    Arg: claims - decoded token claims.
    Operation: confirms the token was issued for this application, accepting either an
               'aud' entry or the 'azp' (authorised party) claim Keycloak sets to the
               client that requested the token. Raises HTTPException 401 otherwise.
    Return: None.
    """
    expected = settings.keycloak_client_id
    audience = claims.get("aud", [])
    audiences = [audience] if isinstance(audience, str) else list(audience)

    if expected == claims.get("azp") or expected in audiences:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token was not issued for this application.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _decode_with_retry(token: str) -> dict[str, Any]:
    """
    Arg: token - raw bearer token extracted from the Authorization header.
    Operation: verifies the token against the realm's JWKS, retrying once with a refreshed
               key set so signing-key rotation does not cause a 401 storm. Raises
               HTTPException 401 when the token is invalid, 503 if Keycloak is unreachable.
    Return: the decoded token claims.
    """
    try:
        try:
            return _decode(token, await _get_jwks())
        except JWTError:
            return _decode(token, await _get_jwks(force_refresh=True))
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity provider unreachable.",
        ) from exc


def _assert_export_client(claims: dict[str, Any]) -> None:
    """
    Arg: claims - decoded token claims.
    Operation: confirms the caller is daily's configured Keycloak service-account client
               via the 'azp' (authorised party) claim. Raises HTTPException 403 when the
               export_client_id setting is empty or does not match.
    Return: None.
    """
    expected = settings.export_client_id
    if expected and claims.get("azp") == expected:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Caller is not the configured export client.",
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict[str, Any]:
    """
    Arg: credentials - bearer credentials extracted from the Authorization header.
    Operation: validates the access token, then confirms it was issued for this
               application. Raises HTTPException 401 when the token is invalid or was not
               issued for this client.
    Return: the decoded token claims, whose 'sub' identifies the user.
    """
    claims = await _decode_with_retry(credentials.credentials)
    _assert_intended_for_this_client(claims)
    return claims


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


async def get_export_caller(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict[str, Any]:
    """
    Arg: credentials - bearer credentials extracted from the Authorization header.
    Operation: validates the access token the same way as get_current_user, but skips the
               audience check performed there since daily authenticates as a separate
               Keycloak client; asserts the caller is that configured export client
               instead. Raises HTTPException 403 when the caller is not the export client.
    Return: the decoded token claims.
    """
    claims = await _decode_with_retry(credentials.credentials)
    _assert_export_client(claims)
    return claims


ExportCaller = Annotated[dict[str, Any], Depends(get_export_caller)]


def realm_roles(claims: dict[str, Any]) -> list[str]:
    """
    Arg: claims - decoded token claims.
    Operation: reads the realm roles Keycloak nests under the 'realm_access' claim.
    Return: list of realm role names, empty when the claim is absent.
    """
    return list(claims.get("realm_access", {}).get("roles", []))


def require_role(role: str):
    """
    Arg: role - realm role the caller must hold.
    Operation: builds a FastAPI dependency that rejects users lacking the role with 403.
    Return: a Depends() marker usable in route signatures.
    """

    async def _check(user: CurrentUser) -> dict[str, Any]:
        """
        Arg: user - authenticated user claims.
        Operation: verifies the required realm role is present. Raises HTTPException 403.
        Return: the unchanged user claims.
        """
        if role not in realm_roles(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return Depends(_check)
