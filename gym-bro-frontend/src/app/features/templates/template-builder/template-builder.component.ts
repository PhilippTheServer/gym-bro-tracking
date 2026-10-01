import {
  ChangeDetectionStrategy, Component, Input, OnInit, inject, signal,
} from '@angular/core';
import { CdkDrag, CdkDragDrop, CdkDragHandle, CdkDropList } from '@angular/cdk/drag-drop';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/api/api.service';
import { MUSCLE_GROUP_LABELS } from '../../../core/api/exercise-taxonomy';
import { startingSets } from '../../../core/workouts/template-logic';
import { ExercisePickerComponent } from '../../../shared/components/exercise-picker/exercise-picker.component';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import type {
  Exercise, SetType, TemplateExerciseCreate, TemplateSetCreate, WorkoutTemplate,
  WorkoutTemplateCreate,
} from '../../../core/api/models';

interface BuilderSet extends TemplateSetCreate { _id: number; }

interface BuilderExercise {
  exercise: Exercise;
  sets: BuilderSet[];
  notes: string;
  _id: number;
}

const SET_LABELS: Record<SetType, string> = {
  warmup: 'W', working_set: 'S', drop_set: 'D', until_failure: 'F',
};
const SET_COLORS: Record<SetType, string> = {
  warmup: 'var(--set-warmup)',
  working_set: 'var(--set-working)',
  drop_set: 'var(--set-drop)',
  until_failure: 'var(--set-failure)',
};
const SET_TYPES: SetType[] = ['warmup', 'working_set', 'drop_set', 'until_failure'];

let _uid = 0;
const uid = () => ++_uid;

@Component({
  selector: 'gb-template-builder',
  standalone: true,
  imports: [PageHeaderComponent, ExercisePickerComponent, FormsModule, CdkDropList, CdkDrag, CdkDragHandle],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <gb-page-header
        [title]="id ? 'Edit Template' : 'New Template'"
        [showBack]="true"
        [actionLabel]="saving() ? 'Saving…' : 'Save'"
        (action)="save()"
      />

      <div class="content">
        <div class="form-card">
          <input
            class="name-input"
            type="text"
            placeholder="Template name"
            [(ngModel)]="name"
            maxlength="120"
          >
          @if (nameMissing()) {
            <div class="error">Give the template a name before saving.</div>
          }
          <textarea
            class="desc-input"
            placeholder="Description (optional)"
            [(ngModel)]="description"
            rows="2"
          ></textarea>
          <div class="duration-row">
            <label class="duration-label">Est. duration</label>
            <input
              class="duration-input"
              type="number"
              inputmode="numeric"
              placeholder="—"
              [(ngModel)]="durationMinutes"
              min="1"
              max="300"
            >
            <span class="duration-unit">min</span>
          </div>
        </div>

        <div cdkDropList (cdkDropListDropped)="onDrop($event)">
          @for (ex of exercises(); track ex._id; let i = $index) {
            <div class="exercise-block" cdkDrag>
              <div class="ex-header">
                <span class="handle" cdkDragHandle aria-label="Reorder">⠿</span>
                <div class="ex-info">
                  <div class="ex-name">{{ ex.exercise.name }}</div>
                  <div class="ex-muscle">{{ muscleLabel(ex) }}</div>
                </div>
                <button class="remove-ex" (click)="removeExercise(i)" aria-label="Remove">✕</button>
              </div>

              <input
                class="notes-input"
                type="text"
                placeholder="Note (optional) — cues, tempo, setup"
                [(ngModel)]="ex.notes"
              >

              <div class="set-labels-row">
                <span>Type</span><span>Weight</span><span>Reps</span><span></span><span></span>
              </div>

              @for (set of ex.sets; track set._id; let si = $index) {
                <div class="set-edit-row">
                  <button
                    class="type-badge"
                    [style.color]="setColor(set.set_type)"
                    [style.border-color]="setColor(set.set_type)"
                    (click)="cycleSetType(ex, si)"
                  >{{ setLabel(set.set_type) }}</button>

                  <input
                    class="set-val-input"
                    type="number" inputmode="decimal" placeholder="—"
                    [(ngModel)]="set.target_weight" min="0" step="0.5"
                  >
                  <input
                    class="set-val-input"
                    type="number" inputmode="numeric" placeholder="—"
                    [(ngModel)]="set.target_reps" min="1"
                  >
                  <span class="range-dash">–</span>
                  <input
                    class="set-val-input optional"
                    type="number" inputmode="numeric" placeholder="max"
                    [(ngModel)]="set.target_reps_max" min="1"
                  >
                  <button class="remove-set" (click)="removeSet(ex, si)" aria-label="Remove set">−</button>
                </div>
              }
              <button class="add-set-btn" (click)="addSet(ex)">+ Set</button>
            </div>
          }
        </div>

        <button class="add-exercise-btn" (click)="showPicker.set(true)">+ Add Exercises</button>
      </div>

      @if (showPicker()) {
        <gb-exercise-picker
          [multi]="true"
          (picked)="pickExercises($event)"
          (closed)="showPicker.set(false)"
        />
      }
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }

    .form-card {
      background: var(--surface-1); border-radius: var(--radius-lg);
      padding: 4px 16px 16px; margin-bottom: 20px;
    }
    .name-input {
      width: 100%; background: none; border: none;
      color: var(--text-primary); font-size: 22px; font-weight: 700;
      padding: 12px 0; outline: none; border-bottom: 1px solid var(--separator);
    }
    .error { color: var(--accent-red); font-size: 13px; padding: 8px 0 0; }
    .desc-input {
      width: 100%; background: none; border: none; resize: none;
      color: var(--text-secondary); font-size: 15px;
      padding: 12px 0; outline: none; border-bottom: 1px solid var(--separator);
    }
    .duration-row { display: flex; align-items: center; gap: 10px; padding-top: 12px; }
    .duration-label { font-size: 15px; color: var(--text-secondary); flex: 1; }
    .duration-input {
      width: 70px; background: var(--surface-3); border: none;
      color: var(--text-primary); font-size: 16px; font-weight: 600;
      padding: 8px 10px; border-radius: var(--radius-sm); text-align: center; outline: none;
    }
    .duration-unit { font-size: 13px; color: var(--text-tertiary); }

    .exercise-block {
      background: var(--surface-1); border-radius: var(--radius-lg);
      margin-bottom: 14px; overflow: hidden;
    }
    .ex-header {
      display: flex; align-items: center; gap: 10px; padding: 12px 14px;
      border-bottom: 1px solid var(--separator);
    }
    .handle {
      color: var(--text-tertiary); font-size: 16px; cursor: grab;
      letter-spacing: -2px; touch-action: none; padding: 4px 2px;
    }
    .ex-info { flex: 1; min-width: 0; }
    .ex-name {
      font-size: 17px; font-weight: 700; color: var(--text-primary);
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .ex-muscle { font-size: 12px; color: var(--accent-orange); margin-top: 2px; }
    .remove-ex {
      background: var(--surface-3); border: none; color: var(--text-secondary);
      width: 28px; height: 28px; border-radius: 50%; font-size: 13px;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
    }

    .notes-input {
      width: calc(100% - 28px); margin: 10px 14px 4px;
      background: var(--surface-2); border: none; border-radius: var(--radius-sm);
      color: var(--text-primary); font-size: 14px; padding: 9px 11px; outline: none;
    }
    .notes-input::placeholder { color: var(--text-tertiary); }

    .set-labels-row, .set-edit-row {
      display: grid;
      grid-template-columns: 32px 1fr 52px 10px 52px 26px;
      gap: 6px; align-items: center;
    }
    .set-labels-row {
      padding: 8px 14px 2px; font-size: 10px; color: var(--text-tertiary);
      text-transform: uppercase; letter-spacing: 0.4px;
    }
    .set-edit-row { padding: 5px 14px; }

    .type-badge {
      width: 32px; height: 36px; border-radius: 8px; border: 2px solid currentColor;
      background: none; font-size: 13px; font-weight: 700; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }
    .set-val-input {
      background: var(--surface-3); border: none;
      color: var(--text-primary); font-size: 16px; font-weight: 600;
      padding: 9px 4px; border-radius: var(--radius-sm);
      text-align: center; width: 100%; outline: none;
    }
    .set-val-input.optional { font-weight: 500; }
    .set-val-input::placeholder { color: var(--text-tertiary); font-size: 12px; font-weight: 500; }
    .range-dash { text-align: center; color: var(--text-tertiary); font-size: 13px; }
    .remove-set {
      background: none; border: none; color: var(--accent-red);
      font-size: 20px; font-weight: 700; cursor: pointer; padding: 0;
    }
    .add-set-btn {
      display: block; width: 100%; padding: 11px;
      background: none; border: none; border-top: 1px solid var(--separator);
      color: var(--accent-blue); font-size: 15px; font-weight: 600;
      cursor: pointer; text-align: center;
    }
    .add-exercise-btn {
      width: 100%; padding: 16px;
      background: var(--surface-1); border-radius: var(--radius-lg); border: none;
      color: var(--accent-orange); font-size: 17px; font-weight: 600; cursor: pointer;
    }

    .cdk-drag-preview { box-shadow: 0 8px 24px rgba(0,0,0,0.6); }
    .cdk-drag-placeholder { opacity: 0.35; }

    input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; }
    input[type=number] { -moz-appearance: textfield; }
  `],
})
export class TemplateBuilderComponent implements OnInit {
  @Input() id?: string;

  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  readonly exercises = signal<BuilderExercise[]>([]);
  readonly showPicker = signal(false);
  readonly saving = signal(false);
  readonly nameMissing = signal(false);

  protected name = '';
  protected description = '';
  protected durationMinutes?: number;

  ngOnInit(): void {
    if (this.id) {
      this.api.getTemplate(this.id).subscribe((template) => this.load(template));
    }
  }

  private load(template: WorkoutTemplate): void {
    this.name = template.name;
    this.description = template.description ?? '';
    this.durationMinutes = template.estimated_duration_minutes ?? undefined;
    this.exercises.set(
      template.exercises.map((entry) => ({
        exercise: entry.exercise,
        notes: entry.notes ?? '',
        _id: uid(),
        sets: entry.sets.map((set) => ({
          set_type: set.set_type,
          target_reps: set.target_reps,
          target_reps_max: set.target_reps_max,
          target_weight: set.target_weight,
          target_duration_seconds: set.target_duration_seconds,
          order: set.order,
          _id: uid(),
        })),
      }))
    );
  }

  muscleLabel(entry: BuilderExercise): string {
    return MUSCLE_GROUP_LABELS[entry.exercise.muscle_group];
  }

  setLabel(type?: SetType): string {
    return SET_LABELS[type ?? 'working_set'];
  }

  setColor(type?: SetType): string {
    return SET_COLORS[type ?? 'working_set'];
  }

  cycleSetType(entry: BuilderExercise, index: number): void {
    const set = entry.sets[index];
    const position = SET_TYPES.indexOf(set.set_type ?? 'working_set');
    entry.sets[index] = { ...set, set_type: SET_TYPES[(position + 1) % SET_TYPES.length] };
    this.exercises.update((list) => [...list]);
  }

  /** Every picked exercise lands ready to train: three sets, carrying the last numbers used. */
  pickExercises(picked: Exercise[]): void {
    this.showPicker.set(false);
    const previous = this.exercises().at(-1)?.sets.at(-1);
    const added = picked.map((exercise) => ({
      exercise,
      notes: '',
      _id: uid(),
      sets: startingSets(previous).map((set) => ({ ...set, _id: uid() })),
    }));
    this.exercises.update((list) => [...list, ...added]);
  }

  removeExercise(index: number): void {
    this.exercises.update((list) => list.filter((_, position) => position !== index));
  }

  onDrop(event: CdkDragDrop<unknown>): void {
    this.exercises.update((list) => {
      const reordered = [...list];
      const [moved] = reordered.splice(event.previousIndex, 1);
      reordered.splice(event.currentIndex, 0, moved);
      return reordered;
    });
  }

  addSet(entry: BuilderExercise): void {
    const last = entry.sets.at(-1);
    entry.sets.push({
      set_type: last?.set_type ?? 'working_set',
      target_reps: last?.target_reps ?? 8,
      target_reps_max: last?.target_reps_max ?? null,
      target_weight: last?.target_weight ?? null,
      order: entry.sets.length,
      _id: uid(),
    });
    this.exercises.update((list) => [...list]);
  }

  removeSet(entry: BuilderExercise, index: number): void {
    entry.sets.splice(index, 1);
    this.exercises.update((list) => [...list]);
  }

  save(): void {
    if (this.saving()) return;
    if (!this.name.trim()) {
      // Saving used to fail silently here, which looked like the button being broken.
      this.nameMissing.set(true);
      return;
    }
    this.nameMissing.set(false);
    this.saving.set(true);

    const payload: WorkoutTemplateCreate = {
      name: this.name.trim(),
      description: this.description.trim() || null,
      estimated_duration_minutes: this.durationMinutes ?? null,
      exercises: this.exercises().map(
        (entry, order): TemplateExerciseCreate => ({
          exercise_id: entry.exercise.id,
          order,
          notes: entry.notes.trim() || null,
          sets: entry.sets.map(
            (set, setOrder): TemplateSetCreate => ({
              set_type: set.set_type ?? 'working_set',
              target_reps: set.target_reps ?? null,
              target_reps_max: set.target_reps_max ?? null,
              target_weight: set.target_weight ?? null,
              order: setOrder,
            })
          ),
        })
      ),
    };

    const request = this.id
      ? this.api.updateTemplate(this.id, payload)
      : this.api.createTemplate(payload);

    request.subscribe({
      next: () => this.router.navigate(['/templates']),
      error: () => this.saving.set(false),
    });
  }
}
