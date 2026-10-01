import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { stepReps, stepWeight } from '../../../core/workouts/session-logic';
import type { SessionSet, SetType } from '../../../core/api/models';

const SET_TYPE_CONFIG: Record<SetType, { label: string; color: string; short: string }> = {
  warmup:        { label: 'Warm-up', color: 'var(--set-warmup)',  short: 'W' },
  working_set:   { label: 'Work',    color: 'var(--set-working)', short: 'S' },
  drop_set:      { label: 'Drop',    color: 'var(--set-drop)',    short: 'D' },
  until_failure: { label: 'Failure', color: 'var(--set-failure)', short: 'F' },
};

const SET_TYPES: SetType[] = ['warmup', 'working_set', 'drop_set', 'until_failure'];

/**
 * One logged set. Weight and reps step with the buttons either side — mid-set, hitting a
 * 44px button beats placing a caret in a number field — and an untouched set shows what
 * was done last time in grey rather than an empty box.
 */
@Component({
  selector: 'gb-set-row',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="set-row" [class.completed]="set().completed">
      <button
        class="type-badge"
        [style.color]="config().color"
        [style.border-color]="config().color"
        (click)="cycleType()"
        [attr.aria-label]="config().label"
      >{{ config().short }}</button>

      <div class="value-cell">
        <button class="step" (click)="bumpWeight(-1)" aria-label="Less weight">−</button>
        <input
          class="value"
          type="number"
          inputmode="decimal"
          [placeholder]="ghostWeight()"
          [ngModel]="set().weight"
          (ngModelChange)="onWeight($event)"
          [disabled]="set().completed"
          min="0"
          step="0.5"
        >
        <button class="step" (click)="bumpWeight(1)" aria-label="More weight">+</button>
      </div>

      <div class="value-cell">
        <button class="step" (click)="bumpReps(-1)" aria-label="Fewer reps">−</button>
        <input
          class="value"
          type="number"
          inputmode="numeric"
          [placeholder]="ghostReps()"
          [ngModel]="set().reps"
          (ngModelChange)="onReps($event)"
          [disabled]="set().completed"
          min="0"
        >
        <button class="step" (click)="bumpReps(1)" aria-label="More reps">+</button>
      </div>

      @if (showDelete()) {
        <button class="delete" (click)="deleted.emit()" aria-label="Delete set">✕</button>
      } @else {
        <button
          class="complete"
          [class.done]="set().completed"
          (click)="toggleComplete()"
          [attr.aria-label]="set().completed ? 'Mark incomplete' : 'Complete set'"
        >{{ set().completed ? '✓' : '' }}</button>
      }
    </div>
  `,
  styles: [`
    .set-row {
      display: grid;
      grid-template-columns: 28px 1fr 1fr 40px;
      align-items: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: var(--radius-md);
      background: var(--surface-2);
      margin-bottom: 6px;
    }
    .set-row.completed { background: color-mix(in srgb, var(--accent-green) 12%, var(--surface-2)); }

    .type-badge {
      width: 28px; height: 40px; border-radius: 8px;
      border: 2px solid currentColor; background: none;
      font-size: 12px; font-weight: 700; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      -webkit-tap-highlight-color: transparent;
    }

    .value-cell {
      display: grid; grid-template-columns: 30px 1fr 30px;
      align-items: center; background: var(--surface-3);
      border-radius: var(--radius-sm); overflow: hidden;
    }
    .step {
      height: 40px; border: none; background: none;
      color: var(--text-secondary); font-size: 20px; font-weight: 600;
      cursor: pointer; -webkit-tap-highlight-color: transparent;
    }
    .step:active { background: var(--surface-1); }
    .value {
      background: none; border: none; outline: none;
      color: var(--text-primary); font-size: 17px; font-weight: 700;
      text-align: center; width: 100%; padding: 9px 0;
      font-variant-numeric: tabular-nums;
    }
    .value::placeholder { color: var(--text-tertiary); font-weight: 500; }
    .value:disabled { color: var(--text-secondary); }

    .complete, .delete {
      width: 40px; height: 40px; border-radius: 10px; border: none;
      cursor: pointer; font-size: 16px; font-weight: 800;
      -webkit-tap-highlight-color: transparent;
    }
    .complete { background: var(--surface-3); color: #000; }
    .complete.done { background: var(--accent-green); }
    .delete { background: var(--surface-3); color: var(--accent-red); }

    input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; }
    input[type=number] { -moz-appearance: textfield; }
  `],
})
export class SetRowComponent {
  readonly set = input.required<SessionSet>();
  /** What this set held last time, shown as the placeholder while it is empty. */
  readonly ghost = input<{ weight: number | null; reps: number | null } | null>(null);
  readonly showDelete = input(false);

  readonly changed = output<Partial<SessionSet>>();
  readonly completedToggled = output<boolean>();
  readonly deleted = output<void>();

  private readonly pending = signal<Partial<SessionSet>>({});

  readonly config = computed(() => SET_TYPE_CONFIG[this.set().set_type]);

  readonly ghostWeight = computed(() => {
    const weight = this.ghost()?.weight;
    return weight === null || weight === undefined ? '—' : String(weight);
  });

  readonly ghostReps = computed(() => {
    const reps = this.ghost()?.reps;
    return reps === null || reps === undefined ? '—' : String(reps);
  });

  onWeight(weight: number | null): void {
    this.pending.update((changes) => ({ ...changes, weight }));
    this.changed.emit({ weight });
  }

  onReps(reps: number | null): void {
    this.pending.update((changes) => ({ ...changes, reps }));
    this.changed.emit({ reps });
  }

  bumpWeight(direction: 1 | -1): void {
    if (this.set().completed) return;
    this.onWeight(stepWeight(this.set().weight, direction));
  }

  bumpReps(direction: 1 | -1): void {
    if (this.set().completed) return;
    this.onReps(stepReps(this.set().reps, direction));
  }

  cycleType(): void {
    const index = SET_TYPES.indexOf(this.set().set_type);
    this.changed.emit({ set_type: SET_TYPES[(index + 1) % SET_TYPES.length] });
  }

  /**
   * Ticking an empty set off logs what the placeholder was offering: the lifter did the
   * set they were shown, and making them type it first would be busywork.
   */
  toggleComplete(): void {
    const set = this.set();
    if (set.completed) {
      this.completedToggled.emit(false);
      return;
    }
    const ghost = this.ghost();
    const changes: Partial<SessionSet> = {};
    if (set.weight === null && ghost?.weight != null) changes.weight = ghost.weight;
    if (set.reps === null && ghost?.reps != null) changes.reps = ghost.reps;
    if (Object.keys(changes).length) this.changed.emit(changes);
    this.completedToggled.emit(true);
  }
}
