import { ChangeDetectionStrategy, Component, Input, OnInit, inject, signal } from '@angular/core';
import { ApiService } from '../../../core/api/api.service';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { ProgressChartComponent } from '../../../shared/components/progress-chart/progress-chart.component';
import type { ExerciseProgress } from '../../../core/api/models';

@Component({
  selector: 'gb-exercise-progress',
  standalone: true,
  imports: [PageHeaderComponent, ProgressChartComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      @if (progress()) {
        <gb-page-header
          [title]="progress()!.exercise_name"
          [subtitle]="progress()!.muscle_group"
          [showBack]="true"
        />
        <div class="content">
          @if (progress()!.points.length < 2) {
            <div class="empty-state">
              <span>📊</span>
              <p>Log at least two sessions to see progress charts.</p>
            </div>
          } @else {
            <div class="card">
              <h3 class="card-title">Max Weight</h3>
              <div class="chart-wrapper">
                <gb-progress-chart [points]="progress()!.points" metric="max_weight" label="Max Weight (kg)" />
              </div>
            </div>
            <div class="card">
              <h3 class="card-title">Estimated 1RM (Epley)</h3>
              <div class="chart-wrapper">
                <gb-progress-chart [points]="progress()!.points" metric="estimated_1rm" label="Est. 1RM (kg)" />
              </div>
            </div>
            <div class="card">
              <h3 class="card-title">Total Volume</h3>
              <div class="chart-wrapper">
                <gb-progress-chart [points]="progress()!.points" metric="total_volume" label="Volume (kg)" />
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }
    .card { background: var(--surface-1); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 14px; }
    .card-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 14px; }
    .chart-wrapper { height: 200px; }
    .empty-state {
      display: flex; flex-direction: column; align-items: center;
      padding: 60px 20px; gap: 14px; color: var(--text-secondary);
      font-size: 40px; text-align: center;
    }
    .empty-state p { font-size: 15px; }
  `],
})
export class ExerciseProgressComponent implements OnInit {
  @Input() id!: string;
  private readonly api = inject(ApiService);
  readonly progress = signal<ExerciseProgress | null>(null);

  ngOnInit(): void {
    this.api.getExerciseProgress(this.id).subscribe((p) => this.progress.set(p));
  }
}
