"""Domain tests for how child rows get their order."""

from app.domain.ordering import resolve_order


def test_explicit_order_wins() -> None:
    assert resolve_order(7, 2) == 7


def test_missing_order_falls_back_to_position() -> None:
    assert resolve_order(None, 3) == 3


def test_explicit_zero_is_honoured_rather_than_treated_as_missing() -> None:
    # The regression this guards: `order or position` would silently return 5 here.
    assert resolve_order(0, 5) == 0
