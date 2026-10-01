import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/api/api.service';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { ProgressChartComponent } from '../../../shared/components/progress-chart/progress-chart.component';
import type { ExerciseProgressPoint, PersonalRecord, ProgressOverview } from '../../../core/api/models';

@Component({
  selector: 'gb-progress-overview',
  standalone: true,
  imports: [PageHeaderComponent, ProgressChartComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <gb-page-header title="Progress" />
      <div class="content">
        @if (overview()) {
          <!-- Streaks & totals -->
          <div class="stats-grid">
            <div class="stat-card accent-orange">
              <div class="stat-big">{{ overview()!.current_streak }}</div>
              <div class="stat-sub">Day Streak 🔥</div>
            </div>
            <div class="stat-card">
              <div class="stat-big">{{ overview()!.longest_streak }}</div>
              <div class="stat-sub">Best Streak</div>
            </div>
            <div class="stat-card">
              <div class="stat-big">{{ overview()!.total_workouts }}</div>
              <div class="stat-sub">Workouts</div>
            </div>
            <div class="stat-card">
              <div class="stat-big">{{ formatVolume(overview()!.total_volume) }}</div>
              <div class="stat-sub">Total Volume</div>
            </div>
          </div>

          <!-- Volume chart -->
          @if (overview()!.recent_volume.length > 1) {
            <div class="card">
              <h3 class="card-title">Training Volume (last 30 days)</h3>
              <div class="chart-wrapper">
                <gb-progress-chart
                  [points]="volumePoints()"
                  metric="total_volume"
                  label="Volume (kg)"
                />
              </div>
            </div>
          }

          <!-- Personal Records -->
          @if (overview()!.personal_records.length > 0) {
            <div class="card">
              <h3 class="card-title">Personal Records 🏆</h3>
              @for (pr of overview()!.personal_records; track pr.exercise_id) {
                <div class="pr-row" (click)="goExercise(pr.exercise_id)">
                  <div class="pr-name">{{ pr.exercise_name }}</div>
                  <div class="pr-right">
                    <div class="pr-weight">{{ pr.weight }}kg × {{ pr.reps }}</div>
                    <div class="pr-1rm">1RM ≈ {{ pr.estimated_1rm }}kg</div>
                  </div>
                </div>
              }
            </div>
          }

          <!-- Weekly Frequency -->
          @if (overview()!.weekly_frequency.length > 0) {
            <div class="card">
              <h3 class="card-title">Weekly Frequency</h3>
              <div class="freq-bars">
                @for (w of overview()!.weekly_frequency; track w.date) {
                  <div class="freq-col">
                    <div
                      class="freq-bar"
                      [style.height.px]="barHeight(w.count)"
                      [style.background]="barColor(w.count)"
                    ></div>
                    <div class="freq-label">{{ formatWeek(w.date) }}</div>
                  </div>
                }
              </div>
            </div>
          }

        } @else {
          <div class="loading">
            <span>⏳</span><p>Loading your stats…</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }

    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
    .stat-card {
      background: var(--surface-1); border-radius: var(--radius-lg); padding: 18px;
    }
    .stat-card.accent-orange { background: color-mix(in srgb, var(--accent-orange) 15%, var(--surface-1)); }
    .stat-big { font-size: 34px; font-weight: 800; color: var(--text-primary); line-height: 1; }
    .stat-sub { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

    .card {
      background: var(--surface-1); border-radius: var(--radius-lg);
      padding: 16px; margin-bottom: 14px;
    }
    .card-title {
      font-size: 13px; font-weight: 600; color: var(--text-secondary);
      text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 14px;
    }
    .chart-wrapper { height: 180px; }

    .pr-row {
      display: flex; align-items: center; padding: 12px 0;
      border-bottom: 1px solid var(--separator); cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }
    .pr-row:last-child { border-bottom: none; }
    .pr-row:active { opacity: 0.7; }
    .pr-name { flex: 1; font-size: 15px; font-weight: 600; color: var(--text-primary); }
    .pr-right { text-align: right; }
    .pr-weight { font-size: 15px; font-weight: 700; color: var(--accent-orange); }
    .pr-1rm { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }

    .freq-bars {
      display: flex; align-items: flex-end; gap: 6px; height: 80px;
    }
    .freq-col {
      flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%;
      justify-content: flex-end;
    }
    .freq-bar {
      width: 100%; border-radius: 4px 4px 0 0;
      min-height: 4px; transition: height 0.3s ease;
    }
    .freq-label { font-size: 9px; color: var(--text-tertiary); }

    .loading {
      display: flex; flex-direction: column; align-items: center;
      padding: 80px 20px; gap: 12px; color: var(--text-secondary);
      font-size: 40px;
    }
    .loading p { font-size: 15px; }
  `],
})
export class ProgressOverviewComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  readonly overview = signal<ProgressOverview | null>(null);

  ngOnInit(): void {
    this.api.getProgressOverview().subscribe((o) => this.overview.set(o));
  }

  volumePoints(): ExerciseProgressPoint[] {
    return (this.overview()?.recent_volume ?? []).map((v) => ({
      date: v.date,
      max_weight: 0,
      max_reps: 0,
      total_volume: v.total_volume,
      estimated_1rm: 0,
    }));
  }

  formatVolume(v: number): string {
    return v >= 1000 ? `${(v / 1000).toFixed(1)}t` : `${Math.round(v)}kg`;
  }

  formatWeek(dateStr: string): string {
    const d = new Date(dateStr);
    return d.toLocaleDateString('de-DE', { month: 'numeric', day: 'numeric' });
  }

  barHeight(count: number): number {
    const max = Math.max(
      1, ...((this.overview()?.weekly_frequency ?? []).map((w) => w.count))
    );
    return Math.max(4, (count / max) * 60);
  }

  barColor(count: number): string {
    if (count >= 5) return 'var(--accent-green)';
    if (count >= 3) return 'var(--accent-orange)';
    return 'var(--accent-blue)';
  }

  goExercise(id: string): void {
    this.router.navigate(['/exercises', id]);
  }
}
