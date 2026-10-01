import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { ApiService } from '../../../core/api/api.service';
import {
  EQUIPMENT_LABELS, EQUIPMENT_TYPES, MUSCLE_GROUPS, MUSCLE_GROUP_LABELS,
  PRIMARY_MUSCLE_LABELS, primaryMusclesFor,
} from '../../../core/api/exercise-taxonomy';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { ModalSheetDirective } from '../../../shared/directives/modal-sheet.directive';
import type { Equipment, Exercise, MuscleGroup, PrimaryMuscle } from '../../../core/api/models';

@Component({
  selector: 'gb-exercise-library',
  standalone: true,
  imports: [PageHeaderComponent, FormsModule, ModalSheetDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      <gb-page-header title="Exercises" actionLabel="+" (action)="showCreateSheet.set(true)" />
      <div class="content">
        <div class="search-bar">
          <input
            class="search-input"
            type="search"
            placeholder="Search exercises…"
            [ngModel]="search()"
            (ngModelChange)="onSearch($event)"
          >
        </div>

        <div class="chip-row">
          <button class="chip" [class.active]="group() === null" (click)="selectGroup(null)">All</button>
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

        <div class="result-count">
          {{ loading() ? 'Loading…' : exercises().length + ' exercises' }}
        </div>

        @for (ex of exercises(); track ex.id) {
          <div class="exercise-row" (click)="go(ex.id)">
            <div class="ex-info">
              <div class="ex-name">{{ ex.name }}</div>
              <div class="ex-meta">
                {{ metaFor(ex) }}
                @if (ex.is_custom) { <span class="custom-badge">Custom</span> }
              </div>
            </div>
            <span class="chevron">›</span>
          </div>
        } @empty {
          @if (!loading()) {
            <div class="empty">Nothing matches those filters.</div>
          }
        }
      </div>

      @if (showCreateSheet()) {
        <dialog
          gbModalSheet class="sheet-backdrop"
          (click)="showCreateSheet.set(false)" (dismissed)="showCreateSheet.set(false)"
        >
          <div class="sheet" (click)="$event.stopPropagation()">
            <div class="sheet-header">
              <h3>Custom Exercise</h3>
              <button class="sheet-close" (click)="showCreateSheet.set(false)">✕</button>
            </div>
            <div class="sheet-form">
              <input
                class="sheet-input" type="text" placeholder="Exercise name"
                [(ngModel)]="newName" maxlength="120"
              >
              <select class="sheet-input sheet-select" [(ngModel)]="newGroup">
                @for (g of muscleGroups; track g) {
                  <option [value]="g">{{ groupLabel(g) }}</option>
                }
              </select>
              <select class="sheet-input sheet-select" [(ngModel)]="newEquipment">
                @for (e of equipmentTypes; track e) {
                  <option [value]="e">{{ equipmentLabel(e) }}</option>
                }
              </select>
              <textarea
                class="sheet-input sheet-textarea" placeholder="Instructions (optional)"
                [(ngModel)]="newInstructions" rows="3"
              ></textarea>
              <button class="create-btn" (click)="createExercise()">Create</button>
            </div>
          </div>
        </dialog>
      }
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 100px; }

    .search-bar { padding: 4px 0 12px; }
    .search-input {
      width: 100%; background: var(--surface-2); border: none; border-radius: var(--radius-md);
      color: var(--text-primary); font-size: 16px; padding: 12px 14px; outline: none;
    }

    .chip-row {
      display: flex; gap: 8px; overflow-x: auto; padding-bottom: 10px;
      scrollbar-width: none; -webkit-overflow-scrolling: touch;
    }
    .chip-row::-webkit-scrollbar { display: none; }
    .chip {
      flex: none; background: var(--surface-2); border: none; border-radius: 999px;
      color: var(--text-secondary); font-size: 14px; font-weight: 600;
      padding: 8px 14px; cursor: pointer; white-space: nowrap;
      -webkit-tap-highlight-color: transparent;
    }
    .chip.small { font-size: 13px; padding: 6px 12px; }
    .chip.active { background: var(--accent-orange); color: #000; }

    .result-count {
      font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
      color: var(--text-tertiary); padding: 6px 2px 8px;
    }

    .exercise-row {
      display: flex; align-items: center; gap: 12px;
      padding: 13px 4px; border-bottom: 1px solid var(--separator); cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }
    .exercise-row:active { background: var(--surface-1); }
    .ex-info { flex: 1; min-width: 0; }
    .ex-name {
      font-size: 16px; font-weight: 500; color: var(--text-primary);
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .ex-meta { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
    .custom-badge {
      background: var(--surface-3); color: var(--accent-orange);
      border-radius: 5px; padding: 1px 6px; font-size: 10px; margin-left: 6px;
    }
    .chevron { color: var(--text-tertiary); font-size: 20px; }
    .empty { padding: 40px 0; text-align: center; color: var(--text-secondary); font-size: 15px; }

    .sheet-backdrop {
      position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      z-index: 200; display: flex; align-items: flex-end;
    }
    .sheet {
      width: 100%; background: var(--surface-1);
      border-radius: var(--radius-xl) var(--radius-xl) 0 0;
      max-height: 85dvh; overflow-y: auto;
      padding-bottom: env(safe-area-inset-bottom, 20px);
    }
    .sheet-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 20px 20px 12px;
    }
    .sheet-header h3 { font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0; }
    .sheet-close {
      background: var(--surface-3); border: none; color: var(--text-secondary);
      width: 28px; height: 28px; border-radius: 50%; font-size: 14px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }
    .sheet-form { padding: 0 20px 20px; display: flex; flex-direction: column; gap: 12px; }
    .sheet-input {
      width: 100%; background: var(--surface-3); border: none; border-radius: var(--radius-md);
      color: var(--text-primary); font-size: 16px; padding: 12px 14px; outline: none;
    }
    .sheet-select { appearance: none; }
    .sheet-textarea { resize: none; font-family: inherit; }
    .create-btn {
      width: 100%; padding: 16px; border: none; border-radius: var(--radius-lg);
      background: var(--accent-orange); color: #000; font-size: 17px; font-weight: 700;
      cursor: pointer;
    }
  `],
})
export class ExerciseLibraryComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly searchInput = new Subject<string>();

  protected readonly muscleGroups = MUSCLE_GROUPS;
  protected readonly equipmentTypes = EQUIPMENT_TYPES;

  readonly search = signal('');
  readonly group = signal<MuscleGroup | null>(null);
  readonly primaryMuscle = signal<PrimaryMuscle | null>(null);
  readonly equipment = signal<Equipment | null>(null);
  readonly exercises = signal<Exercise[]>([]);
  readonly loading = signal(true);
  readonly showCreateSheet = signal(false);

  readonly primaryMuscles = computed(() => primaryMusclesFor(this.group()));

  protected newName = '';
  protected newGroup: MuscleGroup = 'chest';
  protected newEquipment: Equipment = 'barbell';
  protected newInstructions = '';

  ngOnInit(): void {
    this.searchInput.pipe(debounceTime(250), distinctUntilChanged()).subscribe(() => this.load());
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

  go(id: string): void {
    this.router.navigate(['/exercises', id]);
  }

  createExercise(): void {
    if (!this.newName.trim()) return;
    this.api
      .createExercise({
        name: this.newName.trim(),
        muscle_group: this.newGroup,
        equipment: this.newEquipment,
        instructions: this.newInstructions.trim() || null,
      })
      .subscribe(() => {
        this.showCreateSheet.set(false);
        this.newName = '';
        this.newInstructions = '';
        this.load();
      });
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
          this.exercises.set(exercises);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
