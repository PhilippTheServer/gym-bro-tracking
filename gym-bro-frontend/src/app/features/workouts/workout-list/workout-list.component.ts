import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { DatePipe } from '@angular/common';
import { ApiService } from '../../../core/api/api.service';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import type { WorkoutSession } from '../../../core/api/models';

@Component({
  selector: 'gb-workout-list',
  standalone: true,
  imports: [PageHeaderComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <gb-page-header title="History" />
      <div class="content">
        @if (loading()) {
          <div class="empty-state">
            <span class="empty-icon">⏳</span>
            <p>Loading…</p>
          </div>
        } @else if (sessions().length === 0) {
          <div class="empty-state">
            <span class="empty-icon">🏋️</span>
            <p>No workouts yet. Start one from the Dashboard!</p>
          </div>
        } @else {
          @for (session of sessions(); track session.id) {
            <div class="session-card" (click)="go(session.id)">
              <div class="session-header">
                <span class="session-name">{{ session.name }}</span>
                <span class="session-date">{{ session.started_at | date:'EEE, dd MMM' }}</span>
              </div>
              <div class="session-meta">
                <span class="meta-chip">{{ session.exercises.length }} exercises</span>
                <span class="meta-chip">{{ totalSets(session) }} sets</span>
                <span class="meta-chip">{{ duration(session) }}</span>
              </div>
              @if (session.exercises.length > 0) {
                <div class="exercise-list">
                  @for (ex of session.exercises.slice(0, 4); track ex.id) {
                    <span class="exercise-tag">{{ ex.exercise.name }}</span>
                  }
                  @if (session.exercises.length > 4) {
                    <span class="exercise-tag muted">+{{ session.exercises.length - 4 }}</span>
                  }
                </div>
              }
            </div>
          }
        }
      </div>
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }

    .empty-state {
      display: flex; flex-direction: column; align-items: center;
      padding: 60px 20px; gap: 12px; color: var(--text-secondary);
    }
    .empty-icon { font-size: 48px; }

    .session-card {
      background: var(--surface-1);
      border-radius: var(--radius-lg);
      padding: 16px;
      margin-bottom: 12px;
      cursor: pointer;
      -webkit-tap-highlight-color: transparent;
      transition: opacity 0.15s ease;
    }
    .session-card:active { opacity: 0.7; }

    .session-header {
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
    }
    .session-name { font-size: 17px; font-weight: 600; color: var(--text-primary); }
    .session-date { font-size: 13px; color: var(--text-secondary); }

    .session-meta {
      display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;
    }
    .meta-chip {
      font-size: 12px; color: var(--text-tertiary);
      background: var(--surface-2);
      padding: 3px 8px; border-radius: 20px;
    }

    .exercise-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .exercise-tag {
      font-size: 12px; color: var(--text-secondary);
      background: var(--surface-3); padding: 4px 10px; border-radius: 20px;
    }
    .exercise-tag.muted { color: var(--text-tertiary); }
  `],
})
export class WorkoutListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  readonly sessions = signal<WorkoutSession[]>([]);
  readonly loading = signal(true);

  ngOnInit(): void {
    this.api.getSessions().subscribe((s) => {
      this.sessions.set(s);
      this.loading.set(false);
    });
  }

  go(id: string): void {
    this.router.navigate(['/workouts', id]);
  }

  totalSets(session: WorkoutSession): number {
    return session.exercises.reduce((acc, ex) => acc + ex.sets.length, 0);
  }

  duration(session: WorkoutSession): string {
    if (!session.completed_at) return 'In progress';
    const ms = new Date(session.completed_at).getTime() - new Date(session.started_at).getTime();
    const m = Math.floor(ms / 60000);
    return m < 60 ? `${m} min` : `${Math.floor(m / 60)}h ${m % 60}m`;
  }
}
