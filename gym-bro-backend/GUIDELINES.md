# FastAPI Repository Coding Guidelines for AI Coding Agents

## Purpose

These guidelines define how code should be structured, where things belong, and how implementation decisions should be made across all FastAPI repositories.

The goal is to produce code that is:

* consistent
* easy to review
* easy to maintain
* easy to extend
* safe for automated and human collaboration

## 1. Core Principles

### 1.1 Follow SOLID

All code must follow the SOLID principles.

* **Single Responsibility Principle**
  Every module, class, and function should have one clear responsibility.
* **Open/Closed Principle**
  Prefer extension over modification.
* **Liskov Substitution Principle**
  Subtypes must behave like their base types.
* **Interface Segregation Principle**
  Keep interfaces small and focused.
* **Dependency Inversion Principle**
  Depend on abstractions, not concrete implementations.

### 1.2 One Function, One Job

A function should do exactly one thing, and do it very well.

Rules:

* A function must have a single, clear purpose.
* If a function performs validation, transformation, persistence, and logging together, it must be split.
* Avoid `manager`, `helper`, or `utils` functions that mix responsibilities.

### 1.3 Prefer Explicitness

Code must be explicit over clever.

Rules:

* Use clear names.
* Prefer readable flow over compact code.
* Avoid hidden side effects.
* Avoid implicit dependencies.

## 2. Tooling Standards

### 2.1 Python Version

* Use **Python 3.14 or newer**.

### 2.2 Package Manager

* Use **uv** for dependency management and environment handling.
* Do not use pip, poetry, or pipenv unless explicitly required by the repository.

### 2.3 Formatting and Linting

* Use **ruff** for both formatting and linting.
* Code must be formatted before completion.
* Lint issues must be fixed, not ignored, unless there is a documented reason.

## 3. General Coding Rules

### 3.1 Type Hints Are Required

* Every function must use full type annotations.
* Public APIs must always be fully typed.
* Avoid `Any` unless absolutely necessary and justified.

### 3.2 Docstrings Are Required

Every function must have a docstring.

Required format:

```python
def create_user(user_in: UserCreate) -> User:
    """
    Arg: user_in - input data for creating a user.
    Operation: validates input and creates a new user record.
    Return: the created user entity.
    """
```

Docstring rules:

* Use exactly these three sections:

  * `Arg`
  * `Operation`
  * `Return`
* Keep docstrings short and practical.
* Describe what the function does, not the implementation details.
* If a function raises important exceptions, mention them in `Operation`.

### 3.3 Naming

* Use descriptive names.
* Names must reflect intent.
* Avoid abbreviations unless they are industry standard.
* Boolean variables must read like predicates:

  * `is_active`
  * `has_access`
  * `can_delete`

### 3.4 Avoid Large Functions

* Prefer small functions with focused behavior.
* A function that needs internal section comments is usually too large.
* Extract logic into dedicated functions or services.

### 3.5 Avoid Shared Mutable State

* Keep state local where possible.
* Avoid global variables.
* Configuration must come from dedicated settings objects.

## 5. API Layer Rules

### 5.1 Keep Route Handlers Thin

Route handlers should only:

* accept request data
* resolve dependencies
* call one application use case
* return the response

Route handlers must not:

* contain business rules
* contain SQL
* orchestrate complex workflows
* perform multi-step transformations inline

### 5.2 Use Schemas for Input and Output

* Use explicit request and response schemas.
* Do not return ORM entities directly from endpoints.
* Separate transport models from domain models where useful.

### 5.3 Dependency Injection

* Use FastAPI dependency injection for request-scoped concerns.
* Do not construct infrastructure dependencies directly inside routes.

Bad:

```python
@router.get("/users/{user_id}")
def get_user(user_id: UUID):
    repo = UserRepository()
    return repo.get(user_id)
```

Good:

```python
@router.get("/users/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID,
    use_case: GetUserUseCase = Depends(get_user_use_case),
) -> UserRead:
    return use_case.execute(user_id)
```

## 6. Business Logic Rules

### 6.1 Business Logic Does Not Belong in Routes

All business rules must live in:

* domain services
* use cases
* dedicated service classes

### 6.2 Use Cases Represent Actions

Use cases should model business actions.

Examples:

* `CreateUserUseCase`
* `DeactivateSubscriptionUseCase`
* `GenerateInvoiceUseCase`

A use case should:

* receive input
* coordinate domain/infrastructure calls
* return a result

### 6.3 Repositories Hide Persistence Details

Repositories expose data access through clear interfaces.

Rules:

* Business logic should not know SQL details.
* Repositories should not contain unrelated business rules.
* One repository should focus on one aggregate or entity family.

## 7. Error Handling

### 7.1 Raise Meaningful Exceptions

* Use clear, specific exception types.
* Avoid broad `except Exception` unless re-raising or boundary logging.

### 7.2 Translate Errors at the API Boundary

* Domain and application layers should raise meaningful internal exceptions.
* API layer translates them into HTTP responses.

### 7.3 Do Not Swallow Errors

* Never silently ignore failures.
* Log with context when appropriate.
* Preserve root cause when re-raising.

## 8. Configuration Rules

### 8.1 Centralize Configuration

* All configuration must be defined in a dedicated settings module.
* Read from environment variables through a typed settings object.

### 8.2 No Hardcoded Secrets

* Never hardcode secrets, tokens, passwords, or API keys.
* Use environment variables or secret managers.

## 9. Testing Rules

### 9.1 Test by Layer

* Domain tests for domain logic
* Application tests for use cases
* API tests for endpoint contracts
* Infrastructure tests for adapters and repository behavior

### 9.2 Prefer Small, Focused Tests

* One test should validate one behavior.
* Test names must describe expected behavior.

### 9.3 Avoid Over-Mocking

* Mock external boundaries, not every internal function.
* Prefer realistic integration tests where valuable.

## 11. Rules for AI Coding Agents

When creating or modifying code, always follow these rules:

1. Do not place business logic in route handlers.
2. Do not create large multi-purpose functions.
3. Always add full type hints.
4. Always add a docstring in the required format.
5. Prefer dependency injection over direct instantiation.
6. Keep domain logic independent from FastAPI and infrastructure.
7. Use ruff-compatible formatting and lint-clean code.
8. Use uv-compatible project commands and dependency assumptions.
9. Extend existing structure instead of inventing new patterns.
10. When unsure where code belongs, choose the most responsibility-focused layer.

## 12. Preferred Examples

### Function Example

```python
def normalize_email(email: str) -> str:
    """
    Arg: email - raw email address string.
    Operation: trims whitespace and converts the email to lowercase.
    Return: normalized email string.
    """
    return email.strip().lower()
```

### Use Case Example

```python
class CreateUserUseCase:
    """Application use case for creating a user."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, user_in: UserCreate) -> User:
        """
        Arg: user_in - validated user creation input.
        Operation: creates a domain user entity and persists it through the repository.
        Return: created user entity.
        """
        user = User.create(user_in.email, user_in.name)
        return self._repository.save(user)
```

### Route Example

```python
@router.post("/users", response_model=UserRead)
def create_user(
    payload: UserCreate,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> UserRead:
    """
    Arg: payload - validated request body for user creation.
    Operation: delegates user creation to the application use case.
    Return: serialized created user response.
    """
    return UserRead.model_validate(use_case.execute(payload))
```

## 13. Non-Goals

The following are not allowed unless explicitly justified:

* fat controllers
* god services
* hidden side effects
* mixed responsibilities in one function
* direct database access from routes
* untyped public functions
* missing docstrings
* ad hoc folder structures

## 14. Default Decision Rule

If there is uncertainty, choose the option that:

* reduces responsibility per unit
* improves readability
* improves testability
* keeps framework concerns separate from business concerns
* preserves SOLID design
