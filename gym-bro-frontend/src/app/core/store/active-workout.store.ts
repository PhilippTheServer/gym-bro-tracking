import { Injectable, computed, effect, signal } from '@angular/core';
import type { SessionSet, SetType, WorkoutSession } from '../api/models';

const STORAGE_KEY = 'gym-bro:active-workout';

@Injectable({ providedIn: 'root' })
export class ActiveWorkoutStore {
  readonly session = signal<WorkoutSession | null>(this._restore());
  readonly isActive = computed(() => this.session() !== null);
  readonly elapsedSeconds = signal(0);

  private _timer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    effect(() => {
      const s = this.session();
      if (s) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
        this._startTimer(s.started_at);
      } else {
        localStorage.removeItem(STORAGE_KEY);
        this._stopTimer();
      }
    });
  }

  setSession(session: WorkoutSession): void {
    this.session.set(session);
  }

  clearSession(): void {
    this.session.set(null);
    this.elapsedSeconds.set(0);
  }

  private _startTimer(startedAt: string): void {
    this._stopTimer();
    const start = new Date(startedAt).getTime();
    const tick = () => {
      const elapsed = Math.floor((Date.now() - start) / 1000);
      this.elapsedSeconds.set(elapsed);
    };
    tick();
    this._timer = setInterval(tick, 1000);
  }

  private _stopTimer(): void {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  private _restore(): WorkoutSession | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  formatElapsed(): string {
    const total = this.elapsedSeconds();
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    const pad = (n: number) => n.toString().padStart(2, '0');
    return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
  }
}
