import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/api/api.service';
import { ActiveWorkoutStore } from '../../../core/store/active-workout.store';
import { duplicateOf, sessionFromTemplate } from '../../../core/workouts/template-logic';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import type { WorkoutTemplate } from '../../../core/api/models';

@Component({
  selector: 'gb-template-list',
  standalone: true,
  imports: [PageHeaderComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <gb-page-header title="Templates" actionLabel="New" (action)="create()" />
      <div class="content">
        @if (templates().length === 0) {
          <div class="empty-state">
            <span class="empty-icon">📐</span>
            <p>No templates yet. Create one to get started!</p>
            <button class="cta" (click)="create()">Create Template</button>
          </div>
        }
        @for (tmpl of templates(); track tmpl.id) {
          <div class="tmpl-card">
            <div class="tmpl-body" (click)="startFrom(tmpl)">
              <div class="tmpl-name">{{ tmpl.name }}</div>
              @if (tmpl.description) {
                <div class="tmpl-desc">{{ tmpl.description }}</div>
              }
              <div class="tmpl-meta">
                {{ tmpl.exercises.length }} exercises
                @if (tmpl.estimated_duration_minutes) {
                  · ~{{ tmpl.estimated_duration_minutes }} min
                }
              </div>
              <div class="exercise-chips">
                @for (ex of tmpl.exercises.slice(0, 4); track ex.id) {
                  <span class="chip">{{ ex.exercise.name }}</span>
                }
                @if (tmpl.exercises.length > 4) {
                  <span class="chip muted">+{{ tmpl.exercises.length - 4 }}</span>
                }
              </div>
            </div>
            <div class="tmpl-actions">
              <button class="action-btn edit" (click)="edit(tmpl.id)" aria-label="Edit">✎</button>
              <button
                class="action-btn copy"
                (click)="duplicate(tmpl)"
                aria-label="Duplicate"
              >⧉</button>
              <button class="action-btn delete" (click)="delete(tmpl)" aria-label="Delete">🗑</button>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }

    .empty-state {
      display: flex; flex-direction: column; align-items: center;
      padding: 60px 20px; gap: 16px; color: var(--text-secondary); text-align: center;
    }
    .empty-icon { font-size: 48px; }
    .cta {
      background: var(--accent-orange); color: #000;
      font-size: 16px; font-weight: 700; padding: 14px 28px;
      border: none; border-radius: var(--radius-lg); cursor: pointer;
    }

    .tmpl-card {
      background: var(--surface-1); border-radius: var(--radius-lg);
      margin-bottom: 12px; overflow: hidden;
      display: flex;
    }
    .tmpl-body {
      flex: 1; padding: 16px; cursor: pointer; -webkit-tap-highlight-color: transparent;
    }
    .tmpl-body:active { opacity: 0.7; }
    .tmpl-name { font-size: 18px; font-weight: 700; color: var(--text-primary); }
    .tmpl-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
    .tmpl-meta { font-size: 13px; color: var(--text-tertiary); margin-top: 6px; }

    .exercise-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
    .chip {
      font-size: 11px; color: var(--text-secondary);
      background: var(--surface-3); padding: 3px 8px; border-radius: 20px;
    }
    .chip.muted { color: var(--text-tertiary); }

    .tmpl-actions {
      display: flex; flex-direction: column;
      border-left: 1px solid var(--separator);
    }
    .action-btn {
      flex: 1; background: none; border: none; cursor: pointer;
      font-size: 18px; padding: 0 16px;
      -webkit-tap-highlight-color: transparent;
    }
    .action-btn:active { opacity: 0.5; }
    .action-btn.delete { color: var(--accent-red); }
    .action-btn.copy { color: var(--accent-blue); }
  `],
})
export class TemplateListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly activeWorkout = inject(ActiveWorkoutStore);
  readonly templates = signal<WorkoutTemplate[]>([]);

  ngOnInit(): void {
    this.api.getTemplates().subscribe((t) => this.templates.set(t));
  }

  create(): void { this.router.navigate(['/templates/new']); }
  edit(id: string): void { this.router.navigate(['/templates', id, 'edit']); }

  /** Starts the workout this template describes, with its targets already filled in. */
  startFrom(tmpl: WorkoutTemplate): void {
    this.api.startSession(sessionFromTemplate(tmpl)).subscribe((session) => {
      this.activeWorkout.setSession(session);
      this.router.navigate(['/workouts', session.id]);
    });
  }

  duplicate(tmpl: WorkoutTemplate): void {
    this.api.createTemplate(duplicateOf(tmpl)).subscribe((created) => {
      this.templates.update((list) => [...list, created]);
      this.router.navigate(['/templates', created.id, 'edit']);
    });
  }

  delete(tmpl: WorkoutTemplate): void {
    if (!confirm(`Delete "${tmpl.name}"?`)) return;
    this.api.deleteTemplate(tmpl.id).subscribe(() =>
      this.templates.update((list) => list.filter((t) => t.id !== tmpl.id))
    );
  }
}
