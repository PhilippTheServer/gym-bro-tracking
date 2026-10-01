import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import { CdkDrag, CdkDragHandle } from '@angular/cdk/drag-drop';
import { SetRowComponent } from '../../../shared/components/set-row/set-row.component';
import { ghostFor, isExerciseComplete } from '../../../core/workouts/session-logic';
import { MUSCLE_GROUP_LABELS } from '../../../core/api/exercise-taxonomy';
import type { LastPerformance, SessionExercise, SessionSet } from '../../../core/api/models';

/**
 * One exercise in a running session. Finished exercises fold down to a single line so the
 * one being worked on is the thing on screen, rather than the eighth card down.
 */
@Component({
  selector: 'gb-session-exercise-card',
  standalone: true,
  imports: [SetRowComponent, CdkDrag, CdkDragHandle],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div cdkDrag class="wrapper">
      @if (collapsed()) {
        <button class="collapsed" (click)="expanded.emit()">
          @if (interactive()) {
            <span class="handle" cdkDragHandle aria-label="Reorder">⠿</span>
          }
          <span class="collapsed-name">
            @if (done()) { <span class="done-tick">✓</span> }
            {{ exercise().exercise.name }}
          </span>
          <span class="collapsed-meta">{{ summary() }}</span>
        </button>
      } @else {
        <div class="card" [class.active]="active()">
          <div class="card-header">
            @if (interactive()) {
              <span class="handle" cdkDragHandle aria-label="Reorder">⠿</span>
            }
            <div class="titles">
              <div class="name">{{ exercise().exercise.name }}</div>
              <div class="muscle">{{ muscleLabel() }}</div>
            </div>
            @if (interactive()) {
              <button class="menu-btn" (click)="menuOpened.emit()" aria-label="Exercise options">⋯</button>
            }
          </div>

          @if (lastPerformance(); as performance) {
            <button class="last-time" (click)="fillFromLastTime.emit()">
              Last time · {{ lastTimeLabel(performance) }}
              <span class="fill-hint">tap to fill</span>
            </button>
          }

          <div class="set-labels">
            <span></span><span>Weight (kg)</span><span>Reps</span><span></span>
          </div>

          @for (set of exercise().sets; track set.id; let i = $index) {
            <gb-set-row
              [set]="set"
              [ghost]="ghostFor(lastPerformance(), i)"
              [showDelete]="editing()"
              (changed)="setChanged.emit({ setId: set.id, changes: $event })"
              (completedToggled)="setCompleted.emit({ setId: set.id, completed: $event })"
              (deleted)="setDeleted.emit(set.id)"
            />
          }

          @if (interactive()) {
            <button class="add-set" (click)="addSet.emit()">+ Set</button>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .wrapper { display: block; }

    .collapsed {
      display: flex; align-items: center; gap: 10px; width: 100%; text-align: left;
      background: var(--surface-1); border: none; border-radius: var(--radius-lg);
      padding: 12px 14px; margin-bottom: 8px; cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }
    .collapsed-name {
      flex: 1; font-size: 15px; font-weight: 600; color: var(--text-secondary);
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .done-tick { color: var(--accent-green); font-weight: 800; margin-right: 4px; }
    .collapsed-meta { font-size: 12px; color: var(--text-tertiary); white-space: nowrap; }

    .card {
      background: var(--surface-1); border-radius: var(--radius-lg);
      margin-bottom: 12px; overflow: hidden;
      border: 1px solid transparent;
    }
    .card.active { border-color: var(--accent-orange); }

    .card-header {
      display: flex; align-items: center; gap: 10px;
      padding: 12px 14px 10px; border-bottom: 1px solid var(--separator);
    }
    .titles { flex: 1; min-width: 0; }
    .name {
      font-size: 17px; font-weight: 700; color: var(--text-primary);
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .muscle { font-size: 12px; color: var(--accent-orange); margin-top: 2px; }
    .handle {
      color: var(--text-tertiary); font-size: 16px; cursor: grab;
      letter-spacing: -2px; touch-action: none; padding: 4px 2px;
    }
    .menu-btn {
      background: var(--surface-3); border: none; color: var(--text-secondary);
      width: 30px; height: 30px; border-radius: 50%; font-size: 16px; font-weight: 700;
      cursor: pointer; line-height: 1;
    }

    .last-time {
      display: flex; align-items: center; gap: 8px; width: 100%; text-align: left;
      background: none; border: none; border-bottom: 1px solid var(--separator);
      color: var(--text-secondary); font-size: 12.5px; padding: 8px 14px; cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }
    .fill-hint {
      margin-left: auto; color: var(--accent-blue); font-weight: 600; white-space: nowrap;
    }

    .set-labels {
      display: grid; grid-template-columns: 28px 1fr 1fr 40px; gap: 6px;
      padding: 8px 12px 2px; font-size: 10px; color: var(--text-tertiary);
      text-transform: uppercase; letter-spacing: 0.5px; text-align: center;
    }

    gb-set-row { display: block; padding: 0 12px; }

    .add-set {
      display: block; width: 100%; padding: 11px;
      background: none; border: none; border-top: 1px solid var(--separator);
      color: var(--accent-blue); font-size: 15px; font-weight: 600; cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }

    .cdk-drag-preview { box-shadow: 0 8px 24px rgba(0,0,0,0.6); }
    .cdk-drag-placeholder { opacity: 0.35; }
  `],
})
export class SessionExerciseCardComponent {
  readonly exercise = input.required<SessionExercise>();
  readonly active = input(false);
  readonly collapsed = input(false);
  readonly editing = input(false);
  /** False for a finished workout: it is a record, not something to restructure. */
  readonly interactive = input(true);
  readonly lastPerformance = input<LastPerformance | null>(null);

  readonly setChanged = output<{ setId: string; changes: Partial<SessionSet> }>();
  readonly setCompleted = output<{ setId: string; completed: boolean }>();
  readonly setDeleted = output<string>();
  readonly addSet = output<void>();
  readonly menuOpened = output<void>();
  readonly expanded = output<void>();
  readonly fillFromLastTime = output<void>();

  protected readonly ghostFor = ghostFor;

  readonly done = computed(() => isExerciseComplete(this.exercise()));

  readonly muscleLabel = computed(() => MUSCLE_GROUP_LABELS[this.exercise().exercise.muscle_group]);

  readonly summary = computed(() => {
    const sets = this.exercise().sets;
    const completed = sets.filter((set) => set.completed);
    if (!completed.length) return `0 / ${sets.length}`;
    const topWeight = Math.max(...completed.map((set) => set.weight ?? 0));
    const setCount = `${completed.length} set${completed.length === 1 ? '' : 's'}`;
    return topWeight > 0 ? `${setCount} · ${topWeight} kg` : setCount;
  });

  lastTimeLabel(performance: LastPerformance): string {
    const weights = performance.sets.map((set) => set.weight).filter((w): w is number => w !== null);
    const reps = performance.sets.map((set) => set.reps ?? 0).join(', ');
    const topWeight = weights.length ? `${Math.max(...weights)} kg × ` : '';
    return `${topWeight}${reps}`;
  }
}
