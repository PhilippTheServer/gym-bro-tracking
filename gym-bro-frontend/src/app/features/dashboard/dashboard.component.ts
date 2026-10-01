import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../core/api/api.service';
import { sessionFromTemplate } from '../../core/workouts/template-logic';
import { ActiveWorkoutStore } from '../../core/store/active-workout.store';
import { KeycloakService } from '../../core/auth/keycloak.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import type { ProgressOverview, WorkoutTemplate } from '../../core/api/models';

@Component({
  selector: 'gb-dashboard',
  standalone: true,
  imports: [PageHeaderComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <gb-page-header [title]="greeting()" subtitle="Ready to train?" />

      <div class="content">
        <!-- Quick Start -->
        <section class="section">
          <h2 class="section-title">Quick Start</h2>
          <button class="start-card primary" (click)="startEmptyWorkout()">
            <span class="start-icon">⚡</span>
            <div>
              <div class="start-title">Empty Workout</div>
              <div class="start-sub">Add exercises on the fly</div>
            </div>
            <span class="chevron">›</span>
          </button>
        </section>

        <!-- Recent Templates -->
        @if (templates().length > 0) {
          <section class="section">
            <div class="section-header">
              <h2 class="section-title">My Templates</h2>
              <button class="see-all" (click)="nav.navigate(['/templates'])">See all</button>
            </div>
            @for (tmpl of templates().slice(0, 3); track tmpl.id) {
              <button class="template-card" (click)="startFromTemplate(tmpl)">
                <div class="tmpl-info">
                  <div class="tmpl-name">{{ tmpl.name }}</div>
                  <div class="tmpl-meta">
                    {{ tmpl.exercises.length }} exercises
                    @if (tmpl.estimated_duration_minutes) {
                      · {{ tmpl.estimated_duration_minutes }} min
                    }
                  </div>
                </div>
                <span class="chevron">›</span>
              </button>
            }
          </section>
        }

        <!-- Stats Overview -->
        @if (overview()) {
          <section class="section">
            <h2 class="section-title">This Week</h2>
            <div class="stats-grid">
              <div class="stat-card">
                <span class="stat-value">{{ overview()!.total_workouts }}</span>
                <span class="stat-label">Total Sessions</span>
              </div>
              <div class="stat-card">
                <span class="stat-value accent-orange">{{ overview()!.current_streak }}</span>
                <span class="stat-label">Day Streak</span>
              </div>
              <div class="stat-card">
                <span class="stat-value">{{ formatVolume(overview()!.total_volume) }}</span>
                <span class="stat-label">Total Volume</span>
              </div>
              <div class="stat-card">
                <span class="stat-value accent-green">{{ overview()!.personal_records.length }}</span>
                <span class="stat-label">PRs Set</span>
              </div>
            </div>
          </section>
        }
      </div>
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }

    .section { margin-bottom: 28px; }
    .section-header {
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;
    }
    .section-title {
      font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0 0 12px;
    }
    .see-all {
      background: none; border: none; color: var(--accent-blue);
      font-size: 15px; cursor: pointer; padding: 0;
    }

    .start-card {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 18px 16px;
      border-radius: var(--radius-lg);
      border: none;
      cursor: pointer;
      text-align: left;
      -webkit-tap-highlight-color: transparent;
      transition: transform 0.15s ease, opacity 0.15s ease;
    }
    .start-card:active { transform: scale(0.98); opacity: 0.85; }
    .start-card.primary { background: var(--accent-orange); }

    .start-icon { font-size: 28px; }
    .start-title { font-size: 17px; font-weight: 700; color: #000; }
    .start-sub { font-size: 13px; color: rgba(0,0,0,0.6); margin-top: 2px; }
    .start-card .chevron { margin-left: auto; font-size: 24px; color: rgba(0,0,0,0.5); }

    .template-card {
      width: 100%;
      display: flex;
      align-items: center;
      padding: 16px;
      background: var(--surface-1);
      border-radius: var(--radius-md);
      border: none;
      cursor: pointer;
      text-align: left;
      margin-bottom: 8px;
      -webkit-tap-highlight-color: transparent;
      transition: opacity 0.15s ease;
    }
    .template-card:active { opacity: 0.7; }
    .tmpl-info { flex: 1; }
    .tmpl-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
    .tmpl-meta { font-size: 13px; color: var(--text-secondary); margin-top: 3px; }
    .chevron { font-size: 22px; color: var(--text-tertiary); }

    .stats-grid {
      display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    }
    .stat-card {
      background: var(--surface-1);
      border-radius: var(--radius-md);
      padding: 16px;
      display: flex; flex-direction: column; gap: 4px;
    }
    .stat-value {
      font-size: 28px; font-weight: 700; color: var(--text-primary);
      font-variant-numeric: tabular-nums;
    }
    .stat-value.accent-orange { color: var(--accent-orange); }
    .stat-value.accent-green { color: var(--accent-green); }
    .stat-label { font-size: 12px; color: var(--text-secondary); }
  `],
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly nav = inject(Router);
  readonly activeWorkout = inject(ActiveWorkoutStore);
  private readonly kc = inject(KeycloakService);

  readonly templates = signal<WorkoutTemplate[]>([]);
  readonly overview = signal<ProgressOverview | null>(null);

  ngOnInit(): void {
    this.api.getTemplates().subscribe((t) => this.templates.set(t));
    this.api.getProgressOverview().subscribe((o) => this.overview.set(o));
    this.api.getActiveSession().subscribe((s) => {
      if (s) this.activeWorkout.setSession(s);
    });
  }

  greeting(): string {
    const h = new Date().getHours();
    const name = this.kc.displayName.split(' ')[0];
    if (h < 12) return `Morning, ${name}`;
    if (h < 17) return `Hey, ${name}`;
    return `Evening, ${name}`;
  }

  formatVolume(v: number): string {
    return v >= 1000 ? `${(v / 1000).toFixed(1)}t` : `${Math.round(v)}kg`;
  }

  startEmptyWorkout(): void {
    this.api
      .startSession({ name: `Workout ${new Date().toLocaleDateString('de-DE')}` })
      .subscribe((s) => {
        this.activeWorkout.setSession(s);
        this.nav.navigate(['/workouts', s.id]);
      });
  }

  startFromTemplate(tmpl: WorkoutTemplate): void {
    this.api.startSession(sessionFromTemplate(tmpl)).subscribe((s) => {
      this.activeWorkout.setSession(s);
      this.nav.navigate(['/workouts', s.id]);
    });
  }
}
