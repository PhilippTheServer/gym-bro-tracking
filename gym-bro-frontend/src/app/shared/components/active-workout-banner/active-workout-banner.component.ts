import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ActiveWorkoutStore } from '../../../core/store/active-workout.store';

@Component({
  selector: 'gb-active-workout-banner',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="banner" (click)="goToWorkout()">
      <div class="banner-left">
        <div class="pulse-dot"></div>
        <span class="banner-name">{{ store.session()?.name }}</span>
      </div>
      <span class="banner-time">{{ store.formatElapsed() }}</span>
    </div>
  `,
  styles: [`
    .banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: var(--accent-green);
      padding: 10px 20px;
      cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }

    .banner:active { opacity: 0.85; }

    .banner-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #fff;
      animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(0.85); }
    }

    .banner-name {
      font-size: 14px;
      font-weight: 600;
      color: #000;
    }

    .banner-time {
      font-size: 14px;
      font-weight: 700;
      color: #000;
      font-variant-numeric: tabular-nums;
    }
  `],
})
export class ActiveWorkoutBannerComponent {
  readonly store = inject(ActiveWorkoutStore);
  private readonly router = inject(Router);

  goToWorkout(): void {
    const id = this.store.session()?.id;
    if (id) this.router.navigate(['/workouts', id]);
  }
}
