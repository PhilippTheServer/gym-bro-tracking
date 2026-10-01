import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { BottomNavComponent } from './shared/components/bottom-nav/bottom-nav.component';
import { ActiveWorkoutBannerComponent } from './shared/components/active-workout-banner/active-workout-banner.component';
import { ActiveWorkoutStore } from './core/store/active-workout.store';

@Component({
  selector: 'gb-root',
  standalone: true,
  imports: [RouterOutlet, BottomNavComponent, ActiveWorkoutBannerComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="app-shell">
      <main class="app-content">
        <router-outlet />
      </main>
      @if (activeWorkout.isActive()) {
        <gb-active-workout-banner />
      }
      <gb-bottom-nav />
    </div>
  `,
  styles: [`
    .app-shell {
      display: flex;
      flex-direction: column;
      height: 100dvh;
      overflow: hidden;
      background: var(--bg-primary);
    }

    .app-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      -webkit-overflow-scrolling: touch;
      padding-top: env(safe-area-inset-top);
      overscroll-behavior-y: contain;
    }
  `],
})
export class AppComponent {
  readonly activeWorkout = inject(ActiveWorkoutStore);
}
