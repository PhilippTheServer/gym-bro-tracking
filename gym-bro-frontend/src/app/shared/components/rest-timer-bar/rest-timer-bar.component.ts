import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RestTimerStore } from '../../../core/workouts/rest-timer.store';

/** The rest countdown, pinned above the bottom navigation while it runs. */
@Component({
  selector: 'gb-rest-timer-bar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (timer.isRunning()) {
      <div class="bar">
        <span class="label">Rest</span>
        <span class="clock">{{ timer.label() }}</span>
        <button class="action" (click)="timer.addSeconds(30)">+30s</button>
        <button class="action skip" (click)="timer.stop()">Skip</button>
      </div>
    }
  `,
  styles: [`
    .bar {
      position: fixed; left: 12px; right: 12px; bottom: calc(68px + env(safe-area-inset-bottom, 0));
      z-index: 150;
      display: flex; align-items: center; gap: 10px;
      background: var(--accent-blue); color: #fff;
      border-radius: var(--radius-lg); padding: 12px 14px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.45);
    }
    .label { font-size: 13px; font-weight: 600; opacity: 0.85; }
    .clock {
      flex: 1; font-size: 22px; font-weight: 800; font-variant-numeric: tabular-nums;
      letter-spacing: 0.5px;
    }
    .action {
      background: rgba(255,255,255,0.22); border: none; color: #fff;
      font-size: 14px; font-weight: 700; padding: 8px 12px; border-radius: 10px;
      cursor: pointer; -webkit-tap-highlight-color: transparent;
    }
    .action.skip { background: rgba(0,0,0,0.25); }
  `],
})
export class RestTimerBarComponent {
  readonly timer = inject(RestTimerStore);
}
