"""Domain tests for the pure training calculations."""

from datetime import date, timedelta

from app.domain.calculations import calculate_streaks, epley_one_rep_max


def test_single_rep_max_is_the_weight_itself() -> None:
    assert epley_one_rep_max(100.0, 1) == 100.0


def test_epley_estimates_above_the_lifted_weight_for_multiple_reps() -> None:
    assert epley_one_rep_max(100.0, 5) == 116.7


def test_epley_rounds_to_one_decimal() -> None:
    assert epley_one_rep_max(62.5, 7) == 77.1


def test_no_workouts_means_no_streak() -> None:
    assert calculate_streaks([]) == (0, 0)


def test_workout_today_starts_a_streak_of_one() -> None:
    assert calculate_streaks([date.today()]) == (1, 1)


def test_consecutive_days_extend_the_current_streak() -> None:
    today = date.today()
    days = [today - timedelta(days=offset) for offset in range(3)]
    assert calculate_streaks(days) == (3, 3)


def test_streak_survives_a_rest_day_yesterday_but_not_a_gap() -> None:
    today = date.today()
    # Trained yesterday and the day before, but not today: the streak still counts.
    assert calculate_streaks([today - timedelta(days=1), today - timedelta(days=2)]) == (2, 2)


def test_gap_breaks_the_current_streak_but_longest_is_remembered() -> None:
    today = date.today()
    old_block = [today - timedelta(days=offset) for offset in (10, 11, 12, 13)]
    current, longest = calculate_streaks([today, *old_block])
    assert current == 1
    assert longest == 4


def test_duplicate_days_count_once() -> None:
    today = date.today()
    assert calculate_streaks([today, today, today - timedelta(days=1)]) == (2, 2)
