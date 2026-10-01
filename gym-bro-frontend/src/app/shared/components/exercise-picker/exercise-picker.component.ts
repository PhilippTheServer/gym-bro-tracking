import {
  ChangeDetectionStrategy, Component, OnInit, computed, inject, input, output, signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ModalSheetDirective } from '../../directives/modal-sheet.directive';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { ApiService } from '../../../core/api/api.service';
import {
  EQUIPMENT_LABELS, EQUIPMENT_TYPES, MUSCLE_GROUPS, MUSCLE_GROUP_LABELS,
  PRIMARY_MUSCLE_LABELS, primaryMusclesFor,
} from '../../../core/api/exercise-taxonomy';
import type { Equipment, Exercise, MuscleGroup, PrimaryMuscle } from '../../../core/api/models';

/**
 * The one exercise picker. A flat search box was tolerable over 67 exercises; over 876 it
 * is not, so the library is narrowed server-side by group, primary muscle and equipment,
 * and the exercises you actually train are offered before you type anything.
 */
@Component({
  selector: 'gb-exercise-picker',
  standalone: true,
  imports: [FormsModule, ModalSheetDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <dialog gbModalSheet class="sheet-backdrop" (click)="closed.emit()" (dismissed)="closed.emit()">
      <div class="sheet" (click)="$event.stopPropagation()">
        <div class="grab-bar"></div>

        <div class="sheet-header">
          <h3>{{ multi() ? 'Add Exercises' : 'Add Exercise' }}</h3>
          <button class="sheet-close" (click)="closed.emit()" aria-label="Close">✕</button>
        </div>

        <input
          class="sheet-search"
          type="search"
          placeholder="Search 876 exercises…"
          [ngModel]="search()"
          (ngModelChange)="onSearch($event)"
        >

        <div class="chip-row">
          <button class="chip" [class.active]="group() === null" (click)="selectGroup(null)">
            All
          </button>
          @for (g of muscleGroups; track g) {
            <button class="chip" [class.active]="group() === g" (click)="selectGroup(g)">
              {{ groupLabel(g) }}
            </button>
          }
        </div>

        @if (primaryMuscles().length) {
          <div class="chip-row sub">
            <button
              class="chip small"
              [class.active]="primaryMuscle() === null"
              (click)="selectPrimaryMuscle(null)"
            >All {{ groupLabel(group()!) }}</button>
            @for (m of primaryMuscles(); track m) {
              <button
                class="chip small"
                [class.active]="primaryMuscle() === m"
                (click)="selectPrimaryMuscle(m)"
              >{{ muscleLabel(m) }}</button>
            }
          </div>
        }

        <div class="chip-row sub">
          <button
            class="chip small"
            [class.active]="equipment() === null"
            (click)="selectEquipment(null)"
          >Any kit</button>
          @for (e of equipmentTypes; track e) {
            <button
              class="chip small"
              [class.active]="equipment() === e"
              (click)="selectEquipment(e)"
            >{{ equipmentLabel(e) }}</button>
          }
        </div>

        <div class="sheet-list">
          @if (loading()) {
            <div class="hint">Loading…</div>
          } @else {
            @if (showRecent()) {
              <div class="list-label">Recently trained</div>
              @for (ex of recent(); track ex.id) {
                <button class="option" [class.picked]="isSelected(ex)" (click)="choose(ex)">
                  <div class="option-text">
                    <div class="option-name">{{ ex.name }}</div>
                    <div class="option-meta">{{ metaFor(ex) }}</div>
                  </div>
                  @if (multi()) {
                    <span class="tick" [class.on]="isSelected(ex)">{{ isSelected(ex) ? '✓' : '' }}</span>
                  }
                </button>
              }
              <div class="list-label">All exercises</div>
            }

            @for (ex of results(); track ex.id) {
              <button class="option" [class.picked]="isSelected(ex)" (click)="choose(ex)">
                <div class="option-text">
                  <div class="option-name">{{ ex.name }}</div>
                  <div class="option-meta">{{ metaFor(ex) }}</div>
                </div>
                @if (multi()) {
                  <span class="tick" [class.on]="isSelected(ex)">{{ isSelected(ex) ? '✓' : '' }}</span>
                }
              </button>
            } @empty {
              <div class="hint">Nothing matches. Try a different filter.</div>
            }
          }
        </div>

        @if (multi()) {
          <div class="sheet-footer">
            <button class="add-btn" [disabled]="!selected().length" (click)="confirm()">
              {{ selected().length ? 'Add ' + selected().length + ' exercise' + (selected().length === 1 ? '' : 's') : 'Select exercises' }}
            </button>
          </div>
        }
      </div>
    </dialog>
  `,
  styles: [`
    .sheet-backdrop {
      position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      z-index: 200; display: flex; align-items: flex-end;
    }
    .sheet {
      width: 100%; background: var(--surface-1);
      border-radius: var(--radius-xl) var(--radius-xl) 0 0;
      height: 88dvh; display: flex; flex-direction: column;
      padding-bottom: env(safe-area-inset-bottom, 0);
    }
    .grab-bar {
      width: 36px; height: 5px; border-radius: 3px; background: var(--surface-3);
      margin: 8px auto 0; flex: none;
    }
    .sheet-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 20px 10px; flex: none;
    }
    .sheet-header h3 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
    .sheet-close {
      background: var(--surface-3); border: none; color: var(--text-secondary);
      width: 28px; height: 28px; border-radius: 50%; font-size: 14px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }
    .sheet-search {
      flex: none; margin: 0 20px 10px;
      background: var(--surface-3); border: none; border-radius: var(--radius-md);
      color: var(--text-primary); font-size: 16px; padding: 12px 14px; outline: none;
    }
    .chip-row {
      flex: none; display: flex; gap: 8px; overflow-x: auto; padding: 0 20px 10px;
      scrollbar-width: none; -webkit-overflow-scrolling: touch;
    }
    .chip-row::-webkit-scrollbar { display: none; }
    .chip-row.sub { padding-bottom: 8px; }
    .chip {
      flex: none; background: var(--surface-2); border: none; border-radius: 999px;
      color: var(--text-secondary); font-size: 14px; font-weight: 600;
      padding: 8px 14px; cursor: pointer; white-space: nowrap;
      -webkit-tap-highlight-color: transparent;
    }
    .chip.small { font-size: 13px; padding: 6px 12px; }
    .chip.active { background: var(--accent-orange); color: #000; }

    .sheet-list { flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; }
    .list-label {
      font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
      color: var(--text-tertiary); padding: 12px 20px 6px;
    }
    .option {
      display: flex; align-items: center; gap: 12px; width: 100%; text-align: left;
      padding: 13px 20px; background: none; border: none;
      border-bottom: 1px solid var(--separator); cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }
    .option:active { background: var(--surface-2); }
    .option.picked { background: color-mix(in srgb, var(--accent-orange) 12%, transparent); }
    .option-text { flex: 1; min-width: 0; }
    .option-name {
      font-size: 16px; font-weight: 500; color: var(--text-primary);
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .option-meta { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
    .tick {
      flex: none; width: 26px; height: 26px; border-radius: 7px;
      background: var(--surface-3); color: #000; font-weight: 800;
      display: grid; place-items: center; font-size: 13px;
    }
    .tick.on { background: var(--accent-green); }
    .hint { padding: 24px 20px; color: var(--text-secondary); font-size: 15px; text-align: center; }

    .sheet-footer { flex: none; padding: 12px 20px 20px; border-top: 1px solid var(--separator); }
    .add-btn {
      width: 100%; padding: 16px; border: none; border-radius: var(--radius-lg);
      background: var(--accent-orange); color: #000; font-size: 17px; font-weight: 700;
      cursor: pointer;
    }
    .add-btn:disabled { background: var(--surface-2); color: var(--text-tertiary); cursor: default; }
  `],
})
export class ExercisePickerComponent implements OnInit {
  /** Multi-select mode: tapping toggles, and a footer button confirms the batch. */
  readonly multi = input(false);

  readonly picked = output<Exercise[]>();
  readonly closed = output<void>();

  private readonly api = inject(ApiService);
  private readonly searchInput = new Subject<string>();

  protected readonly muscleGroups = MUSCLE_GROUPS;
  protected readonly equipmentTypes = EQUIPMENT_TYPES;

  readonly search = signal('');
  readonly group = signal<MuscleGroup | null>(null);
  readonly primaryMuscle = signal<PrimaryMuscle | null>(null);
  readonly equipment = signal<Equipment | null>(null);
  readonly results = signal<Exercise[]>([]);
  readonly recent = signal<Exercise[]>([]);
  readonly selected = signal<Exercise[]>([]);
  readonly loading = signal(true);

  readonly primaryMuscles = computed(() => primaryMusclesFor(this.group()));
  readonly showRecent = computed(
    () => this.recent().length > 0 && !this.search() && !this.group() && !this.equipment()
  );

  ngOnInit(): void {
    this.searchInput
      .pipe(debounceTime(250), distinctUntilChanged())
      .subscribe(() => this.load());
    this.api.getRecentExercises().subscribe((e) => this.recent.set(e));
    this.load();
  }

  onSearch(term: string): void {
    this.search.set(term);
    this.searchInput.next(term);
  }

  selectGroup(group: MuscleGroup | null): void {
    this.group.set(group);
    this.primaryMuscle.set(null);
    this.load();
  }

  selectPrimaryMuscle(muscle: PrimaryMuscle | null): void {
    this.primaryMuscle.set(muscle);
    this.load();
  }

  selectEquipment(equipment: Equipment | null): void {
    this.equipment.set(equipment === this.equipment() ? null : equipment);
    this.load();
  }

  groupLabel(group: MuscleGroup): string {
    return MUSCLE_GROUP_LABELS[group];
  }

  muscleLabel(muscle: PrimaryMuscle): string {
    return PRIMARY_MUSCLE_LABELS[muscle];
  }

  equipmentLabel(equipment: Equipment): string {
    return EQUIPMENT_LABELS[equipment];
  }

  metaFor(exercise: Exercise): string {
    const muscle = exercise.primary_muscle
      ? PRIMARY_MUSCLE_LABELS[exercise.primary_muscle]
      : MUSCLE_GROUP_LABELS[exercise.muscle_group];
    return `${muscle} · ${EQUIPMENT_LABELS[exercise.equipment]}`;
  }

  isSelected(exercise: Exercise): boolean {
    return this.selected().some((e) => e.id === exercise.id);
  }

  choose(exercise: Exercise): void {
    if (!this.multi()) {
      this.picked.emit([exercise]);
      return;
    }
    this.selected.update((list) =>
      list.some((e) => e.id === exercise.id)
        ? list.filter((e) => e.id !== exercise.id)
        : [...list, exercise]
    );
  }

  confirm(): void {
    if (this.selected().length) this.picked.emit(this.selected());
  }

  private load(): void {
    this.loading.set(true);
    this.api
      .getExercises({
        search: this.search(),
        muscle_group: this.group(),
        primary_muscle: this.primaryMuscle(),
        equipment: this.equipment(),
      })
      .subscribe({
        next: (exercises) => {
          this.results.set(exercises);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
