"""Pure domain calculation functions — no I/O, no framework dependencies."""

from datetime import date


def epley_one_rep_max(weight: float, reps: int) -> float:
    """
    Arg: weight - lifted weight in kg; reps - number of repetitions performed.
    Operation: applies the Epley formula to estimate the one-rep maximum.
    Return: estimated 1RM in kg, rounded to one decimal place.
    """
    if reps == 1:
        return weight
    return round(weight * (1 + reps / 30), 1)


def calculate_streaks(workout_dates: list[date]) -> tuple[int, int]:
    """
    Arg: workout_dates - list of dates on which workouts were completed.
    Operation: computes the current consecutive-day streak and the all-time longest streak.
              A streak counts consecutive calendar days with at least one workout.
    Return: tuple of (current_streak, longest_streak).
    """
    if not workout_dates:
        return 0, 0

    unique_dates = sorted(set(workout_dates), reverse=True)
    today = date.today()

    current_streak = 0
    longest_streak = 0
    running = 0
    previous: date | None = None

    for day in unique_dates:
        if previous is None:
            running = 1
            if (today - day).days <= 1:
                current_streak = 1
        elif (previous - day).days == 1:
            running += 1
            if previous == today or (today - previous).days <= 1:
                current_streak = running
        else:
            running = 1

        longest_streak = max(longest_streak, running)
        previous = day

    return current_streak, longest_streak
