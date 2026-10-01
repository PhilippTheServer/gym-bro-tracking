import { Injectable, computed, signal } from '@angular/core';

/** Rest defaults to 90 seconds until an exercise is given its own. */
export const DEFAULT_REST_SECONDS = 90;
const STORAGE_KEY = 'gym-bro.rest-seconds';

/**
 * The rest countdown between sets.
 *
 * Lives at the root so it keeps running while you look at the exercise library mid-rest.
 * Per-exercise durations are remembered in localStorage rather than on the server: it is a
 * preference of this device, and putting it in the schema would buy nothing.
 */
@Injectable({ providedIn: 'root' })
export class RestTimerStore {
  private readonly endsAt = signal<number | null>(null);
  private readonly now = signal(Date.now());
  private ticker?: ReturnType<typeof setInterval>;
  private exerciseId: string | null = null;

  readonly secondsRemaining = computed(() => {
    const endsAt = this.endsAt();
    if (endsAt === null) return 0;
    return Math.max(0, Math.ceil((endsAt - this.now()) / 1000));
  });

  readonly isRunning = computed(() => this.endsAt() !== null);

  readonly label = computed(() => {
    const total = this.secondsRemaining();
    const minutes = Math.floor(total / 60);
    const seconds = total % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  });

  /** The rest this exercise uses, falling back to the default. */
  restSecondsFor(exerciseId: string): number {
    try {
      const stored = localStorage.getItem(`${STORAGE_KEY}.${exerciseId}`);
      const parsed = stored === null ? NaN : Number.parseInt(stored, 10);
      return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_REST_SECONDS;
    } catch {
      return DEFAULT_REST_SECONDS;
    }
  }

  private remember(exerciseId: string, seconds: number): void {
    try {
      localStorage.setItem(`${STORAGE_KEY}.${exerciseId}`, String(seconds));
    } catch {
      // A browser with storage blocked still gets a working timer, just no memory of it.
    }
  }

  /** Starts (or restarts) the countdown for an exercise. */
  start(exerciseId: string): void {
    this.exerciseId = exerciseId;
    this.run(this.restSecondsFor(exerciseId));
  }

  /** Extends the current rest, and remembers the longer rest for this exercise. */
  addSeconds(seconds: number): void {
    const endsAt = this.endsAt();
    if (endsAt === null) return;
    this.endsAt.set(endsAt + seconds * 1000);
    if (this.exerciseId) {
      this.remember(this.exerciseId, this.restSecondsFor(this.exerciseId) + seconds);
    }
  }

  stop(): void {
    this.endsAt.set(null);
    this.exerciseId = null;
    if (this.ticker !== undefined) {
      clearInterval(this.ticker);
      this.ticker = undefined;
    }
  }

  private run(seconds: number): void {
    this.endsAt.set(Date.now() + seconds * 1000);
    this.now.set(Date.now());
    if (this.ticker !== undefined) clearInterval(this.ticker);
    this.ticker = setInterval(() => {
      this.now.set(Date.now());
      if (this.secondsRemaining() === 0) {
        this.buzz();
        this.stop();
      }
    }, 250);
  }

  private buzz(): void {
    try {
      navigator.vibrate?.([200, 100, 200]);
    } catch {
      // Vibration is a nicety; a desktop browser without it still ends the rest.
    }
  }
}
