"""Ordering rules for the child rows that make up templates and sessions."""


def resolve_order(explicit_order: int | None, position: int) -> int:
    """
    Arg: explicit_order - order supplied by the client, or None to let the server decide;
         position - the item's index in the incoming list, used as the fallback.
    Operation: prefers the client's explicit order and otherwise falls back to the
               item's position, so a client may omit ordering entirely.
    Return: the order value to persist.
    """
    return position if explicit_order is None else explicit_order
