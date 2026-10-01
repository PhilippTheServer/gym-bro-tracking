import { ChangeDetectionStrategy, Component, Input, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/api/api.service';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { ProgressChartComponent } from '../../../shared/components/progress-chart/progress-chart.component';
import type { Exercise, ExerciseProgress } from '../../../core/api/models';

@Component({
  selector: 'gb-exercise-detail',
  standalone: true,
  imports: [PageHeaderComponent, ProgressChartComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      @if (exercise()) {
        <gb-page-header
          [title]="exercise()!.name"
          [subtitle]="exercise()!.muscle_group"
          [showBack]="true"
        />
        <div class="content">
          <!-- Meta chips -->
          <div class="meta-row">
            <span class="chip">{{ exercise()!.equipment }}</span>
            <span class="chip">{{ exercise()!.muscle_group }}</span>
            @if (exercise()!.is_custom) {
              <span class="chip custom">Custom</span>
            }
          </div>

          <!-- Instructions -->
          @if (exercise()!.instructions) {
            <div class="card">
              <h3 class="card-title">How to</h3>
              <p class="instructions">{{ exercise()!.instructions }}</p>
            </div>
          }

          <!-- Progress chart -->
          @if (progress()?.points?.length) {
            <div class="card">
              <h3 class="card-title">Weight Progress</h3>
              <div class="chart-wrapper">
                <gb-progress-chart
                  [points]="progress()!.points"
                  metric="max_weight"
                  label="Max Weight (kg)"
                />
              </div>
            </div>
            <div class="card">
              <h3 class="card-title">Estimated 1RM</h3>
              <div class="chart-wrapper">
                <gb-progress-chart
                  [points]="progress()!.points"
                  metric="estimated_1rm"
                  label="Est. 1RM (kg)"
                />
              </div>
            </div>
          } @else {
            <div class="empty-progress">
              <span>📊</span>
              <p>Complete workouts with this exercise to see your progress.</p>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }

    .meta-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
    .chip {
      background: var(--surface-1); color: var(--text-secondary);
      font-size: 13px; padding: 5px 12px; border-radius: 20px; text-transform: capitalize;
    }
    .chip.custom { background: var(--accent-orange); color: #000; font-weight: 700; }

    .card {
      background: var(--surface-1); border-radius: var(--radius-lg);
      padding: 16px; margin-bottom: 14px;
    }
    .card-title { font-size: 15px; font-weight: 700; color: var(--text-secondary); margin: 0 0 12px; text-transform: uppercase; letter-spacing: 0.4px; }
    .instructions { font-size: 15px; color: var(--text-primary); line-height: 1.6; margin: 0; }
    .chart-wrapper { height: 200px; }

    .empty-progress {
      display: flex; flex-direction: column; align-items: center; gap: 12px;
      padding: 40px 20px; color: var(--text-secondary); text-align: center;
      font-size: 40px;
    }
    .empty-progress p { font-size: 15px; }
  `],
})
export class ExerciseDetailComponent implements OnInit {
  @Input() id!: string;

  private readonly api = inject(ApiService);

  readonly exercise = signal<Exercise | null>(null);
  readonly progress = signal<ExerciseProgress | null>(null);

  ngOnInit(): void {
    this.api.getExercise(this.id).subscribe((e) => this.exercise.set(e));
    this.api.getExerciseProgress(this.id).subscribe((p) => this.progress.set(p));
  }
}
