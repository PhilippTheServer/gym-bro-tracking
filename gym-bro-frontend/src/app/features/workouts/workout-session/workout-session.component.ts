import {
  ChangeDetectionStrategy, Component, Input, OnDestroy, OnInit, computed, inject, signal,
} from '@angular/core';
import { CdkDragDrop, CdkDropList } from '@angular/cdk/drag-drop';
import { Router } from '@angular/router';
import { Subject, debounceTime, forkJoin } from 'rxjs';
import { ApiService } from '../../../core/api/api.service';
import { ActiveWorkoutStore } from '../../../core/store/active-workout.store';
import { RestTimerStore } from '../../../core/workouts/rest-timer.store';
import {
  activeExerciseId, applySetUpdate, completedSetCount, ghostFor, isExerciseComplete,
  moveExercise, nextSetDefaults, removeSet, totalSetCount,
} from '../../../core/workouts/session-logic';
import { templateFromSession } from '../../../core/workouts/template-logic';
import { applyImprovements, proposeTemplateUpdate } from '../../../core/workouts/progression';
import { ExercisePickerComponent } from '../../../shared/components/exercise-picker/exercise-picker.component';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { RestTimerBarComponent } from '../../../shared/components/rest-timer-bar/rest-timer-bar.component';
import { ModalSheetDirective } from '../../../shared/directives/modal-sheet.directive';
import { SessionExerciseCardComponent } from '../session-exercise-card/session-exercise-card.component';
import type { ExerciseImprovement } from '../../../core/workouts/progression';
import type {
  Exercise, LastPerformance, SessionExercise, SessionSet, WorkoutSession, WorkoutTemplate,
} from '../../../core/api/models';

/** Set edits are collected for this long before being sent, so a stepper held down is one request. */
const EDIT_FLUSH_MS = 400;

@Component({
  selector: 'gb-workout-session',
  standalone: true,
  imports: [
    PageHeaderComponent, SessionExerciseCardComponent, ExercisePickerComponent,
    RestTimerBarComponent, CdkDropList, ModalSheetDirective,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page">
      @if (session(); as current) {
        <gb-page-header
          [title]="current.name"
          [subtitle]="headerSubtitle()"
          [showBack]="!isActive()"
          [actionLabel]="isActive() ? 'Finish' : ''"
          (action)="showFinishConfirm.set(true)"
        />

        <div class="content" cdkDropList (cdkDropListDropped)="onDrop($event)">
          @for (ex of current.exercises; track ex.id) {
            <gb-session-exercise-card
              [exercise]="ex"
              [active]="ex.id === activeId()"
              [collapsed]="isCollapsed(ex)"
              [editing]="editingId() === ex.id"
              [interactive]="isActive()"
              [lastPerformance]="lastPerformance()[ex.exercise_id] ?? null"
              (expanded)="expand(ex.id)"
              (setChanged)="onSetChanged($event.setId, $event.changes)"
              (setCompleted)="onSetCompleted(ex, $event.setId, $event.completed)"
              (setDeleted)="onSetDeleted($event)"
              (addSet)="onAddSet(ex)"
              (menuOpened)="openMenu(ex)"
              (fillFromLastTime)="fillFromLastTime(ex)"
            />
          }

          @if (isActive()) {
            <button class="add-exercise" (click)="showPicker.set(true)">+ Add Exercise</button>
          } @else {
            <button class="add-exercise" (click)="saveAsTemplate()" [disabled]="savedTemplate()">
              {{ savedTemplate() ? 'Saved as template ✓' : 'Save as template' }}
            </button>
          }
        </div>

        <gb-rest-timer-bar />

        @if (showPicker()) {
          <gb-exercise-picker
            [multi]="true"
            (picked)="addExercises($event)"
            (closed)="showPicker.set(false)"
          />
        }

        @if (swapping()) {
          <gb-exercise-picker (picked)="swapExercise($event[0])" (closed)="swapping.set(null)" />
        }

        @if (menuFor(); as entry) {
          <dialog
            gbModalSheet class="sheet-backdrop"
            (click)="menuFor.set(null)" (dismissed)="menuFor.set(null)"
          >
            <div class="sheet menu-sheet" (click)="$event.stopPropagation()">
              <h3>{{ entry.exercise.name }}</h3>
              <button class="menu-item" (click)="startSwap(entry)">Swap exercise</button>
              <button class="menu-item" (click)="toggleEditing(entry)">
                {{ editingId() === entry.id ? 'Done editing sets' : 'Delete sets' }}
              </button>
              <button class="menu-item danger" (click)="removeExercise(entry)">
                Remove from workout
              </button>
              <button class="menu-item cancel" (click)="menuFor.set(null)">Cancel</button>
            </div>
          </dialog>
        }

        @if (showWriteBack()) {
          <dialog gbModalSheet class="sheet-backdrop" (dismissed)="leave()">
            <div class="sheet writeback-sheet">
              <h3>You beat your targets</h3>
              <p class="confirm-meta">Update {{ templateName() }} with the new numbers?</p>

              @for (improvement of improvements(); track improvement.templateExerciseId) {
                <button
                  class="improvement"
                  [class.declined]="!isAccepted(improvement)"
                  (click)="toggleImprovement(improvement)"
                >
                  <span class="tick" [class.on]="isAccepted(improvement)">
                    {{ isAccepted(improvement) ? '✓' : '' }}
                  </span>
                  <span class="improvement-text">
                    <span class="improvement-name">{{ improvement.name }}</span>
                    <span class="improvement-change">{{ improvement.label }}</span>
                  </span>
                </button>
              }

              <div class="confirm-actions">
                <button
                  class="confirm-btn danger"
                  [disabled]="!accepted().length"
                  (click)="writeBack()"
                >Update template</button>
                <button class="confirm-btn cancel" (click)="leave()">Not this time</button>
              </div>
            </div>
          </dialog>
        }

        @if (showFinishConfirm()) {
          <dialog gbModalSheet class="sheet-backdrop" (dismissed)="showFinishConfirm.set(false)">
            <div class="sheet confirm-sheet">
              <h3>Finish Workout?</h3>
              <p class="confirm-meta">{{ completedSets() }} / {{ totalSets() }} sets completed</p>
              <div class="confirm-actions">
                <button class="confirm-btn danger" (click)="doFinish()">Finish</button>
                <button class="confirm-btn cancel" (click)="showFinishConfirm.set(false)">
                  Cancel
                </button>
              </div>
            </div>
          </dialog>
        }
      } @else if (loading()) {
        <div class="empty-state"><span>⏳</span><p>Loading…</p></div>
      }
    </div>
  `,
  styles: [`
    .page { min-height: 100%; background: var(--bg-primary); }
    .content { padding: 0 16px 140px; }

    .add-exercise {
      width: 100%; padding: 16px;
      background: var(--surface-1); border-radius: var(--radius-lg); border: none;
      color: var(--accent-orange); font-size: 17px; font-weight: 600; cursor: pointer;
      -webkit-tap-highlight-color: transparent;
    }
    .add-exercise:disabled { color: var(--accent-green); cursor: default; }

    .sheet-backdrop {
      position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      z-index: 200; display: flex; align-items: flex-end;
    }
    .sheet {
      width: 100%; background: var(--surface-1);
      border-radius: var(--radius-xl) var(--radius-xl) 0 0;
      padding-bottom: env(safe-area-inset-bottom, 20px);
    }

    .menu-sheet { padding: 22px 16px 26px; }
    .menu-sheet h3 {
      font-size: 17px; font-weight: 700; color: var(--text-primary);
      margin: 0 0 14px; text-align: center;
    }
    .menu-item {
      width: 100%; padding: 15px; margin-bottom: 8px; border: none;
      border-radius: var(--radius-md); background: var(--surface-2);
      color: var(--text-primary); font-size: 16px; font-weight: 600; cursor: pointer;
    }
    .menu-item.danger { color: var(--accent-red); }
    .menu-item.cancel { background: none; color: var(--text-secondary); }

    .confirm-sheet {
      padding: 28px 20px; align-items: center; display: flex; flex-direction: column; gap: 16px;
    }

    .writeback-sheet { padding: 26px 18px 22px; max-height: 80dvh; overflow-y: auto; }
    .writeback-sheet h3 {
      font-size: 21px; font-weight: 700; color: var(--text-primary); margin: 0 0 6px;
      text-align: center;
    }
    .writeback-sheet .confirm-meta { text-align: center; margin: 0 0 16px; }
    .improvement {
      display: flex; align-items: center; gap: 12px; width: 100%; text-align: left;
      background: var(--surface-2); border: none; border-radius: var(--radius-md);
      padding: 12px 14px; margin-bottom: 8px; cursor: pointer;
    }
    .improvement.declined { opacity: 0.45; }
    .tick {
      flex: none; width: 26px; height: 26px; border-radius: 7px;
      background: var(--surface-3); color: #000; font-weight: 800;
      display: grid; place-items: center; font-size: 13px;
    }
    .tick.on { background: var(--accent-green); }
    .improvement-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    .improvement-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
    .improvement-change { font-size: 13px; color: var(--accent-green); font-weight: 600; }
    .confirm-btn:disabled { background: var(--surface-2); color: var(--text-tertiary); }
    .confirm-sheet h3 { font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0; }
    .confirm-meta { font-size: 15px; color: var(--text-secondary); margin: 0; }
    .confirm-actions { display: flex; flex-direction: column; gap: 10px; width: 100%; }
    .confirm-btn {
      width: 100%; padding: 16px; border-radius: var(--radius-lg); border: none;
      font-size: 17px; font-weight: 700; cursor: pointer;
    }
    .confirm-btn.danger { background: var(--accent-green); color: #000; }
    .confirm-btn.cancel { background: var(--surface-2); color: var(--text-primary); }

    .empty-state {
      display: flex; flex-direction: column; align-items: center;
      padding: 80px 20px; gap: 12px; color: var(--text-secondary); font-size: 48px;
    }
  `],
})
export class WorkoutSessionComponent implements OnInit, OnDestroy {
  @Input() id!: string;

  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly activeStore = inject(ActiveWorkoutStore);
  private readonly restTimer = inject(RestTimerStore);

  readonly session = signal<WorkoutSession | null>(null);
  readonly loading = signal(true);
  readonly showPicker = signal(false);
  readonly showFinishConfirm = signal(false);
  readonly menuFor = signal<SessionExercise | null>(null);
  readonly swapping = signal<SessionExercise | null>(null);
  readonly editingId = signal<string | null>(null);
  readonly lastPerformance = signal<Record<string, LastPerformance | null>>({});
  readonly savedTemplate = signal(false);
  readonly showWriteBack = signal(false);
  readonly improvements = signal<ExerciseImprovement[]>([]);
  readonly declined = signal<string[]>([]);
  private readonly template = signal<WorkoutTemplate | null>(null);

  /** Exercises the lifter re-opened after finishing them. */
  private readonly reopened = signal<string[]>([]);

  private readonly flush = new Subject<void>();
  private pending = new Map<string, Partial<SessionSet>>();

  readonly activeId = computed(() => activeExerciseId(this.session()));
  readonly completedSets = computed(() => completedSetCount(this.session()));
  readonly totalSets = computed(() => totalSetCount(this.session()));

  readonly headerSubtitle = computed(() => {
    if (!this.isActive()) return this.durationLabel();
    return `${this.activeStore.formatElapsed()} · ${this.completedSets()}/${this.totalSets()} sets`;
  });

  ngOnInit(): void {
    this.flush.pipe(debounceTime(EDIT_FLUSH_MS)).subscribe(() => this.sendPending());
    this.api.getSession(this.id).subscribe((session) => {
      this.session.set(session);
      this.loading.set(false);
      if (this.isActive()) this.activeStore.setSession(session);
      this.loadLastPerformance(session);
    });
  }

  ngOnDestroy(): void {
    this.sendPending();
  }

  isActive(): boolean {
    return !this.session()?.completed_at;
  }

  isCollapsed(exercise: SessionExercise): boolean {
    if (!this.isActive()) return false;
    if (this.reopened().includes(exercise.id)) return false;
    return isExerciseComplete(exercise) && exercise.id !== this.activeId();
  }

  expand(exerciseId: string): void {
    this.reopened.update((ids) => (ids.includes(exerciseId) ? ids : [...ids, exerciseId]));
  }

  durationLabel(): string {
    const session = this.session();
    if (!session?.completed_at) return '';
    const ms = new Date(session.completed_at).getTime() - new Date(session.started_at).getTime();
    const minutes = Math.floor(ms / 60000);
    return minutes < 60 ? `${minutes} min` : `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
  }

  // ── Set editing ───────────────────────────────────────────────────────────────

  onSetChanged(setId: string, changes: Partial<SessionSet>): void {
    this.applyLocally(setId, changes);
    this.pending.set(setId, { ...this.pending.get(setId), ...changes });
    this.flush.next();
  }

  onSetCompleted(exercise: SessionExercise, setId: string, completed: boolean): void {
    this.applyLocally(setId, { completed });
    this.pending.set(setId, { ...this.pending.get(setId), completed });
    this.sendPending();
    if (completed) this.restTimer.start(exercise.exercise_id);
  }

  onSetDeleted(setId: string): void {
    const current = this.session();
    if (!current) return;
    this.pending.delete(setId);
    this.setSession(removeSet(current, setId));
    this.api.deleteSet(this.id, setId).subscribe((session) => this.setSession(session));
  }

  onAddSet(exercise: SessionExercise): void {
    const defaults = nextSetDefaults(exercise, this.lastPerformance()[exercise.exercise_id]);
    this.api
      .addSet(this.id, exercise.id, { ...defaults, order: exercise.sets.length })
      .subscribe((session) => this.setSession(session));
  }

  /** Fills every set that is still empty with what was done last time. */
  fillFromLastTime(exercise: SessionExercise): void {
    const performance = this.lastPerformance()[exercise.exercise_id];
    if (!performance) return;
    exercise.sets.forEach((set, index) => {
      if (set.completed || (set.weight !== null && set.reps !== null)) return;
      const ghost = ghostFor(performance, index);
      if (!ghost) return;
      const changes: Partial<SessionSet> = {};
      if (set.weight === null && ghost.weight !== null) changes.weight = ghost.weight;
      if (set.reps === null && ghost.reps !== null) changes.reps = ghost.reps;
      if (Object.keys(changes).length) this.onSetChanged(set.id, changes);
    });
  }

  private applyLocally(setId: string, changes: Partial<SessionSet>): void {
    const current = this.session();
    if (current) this.setSession(applySetUpdate(current, setId, changes));
  }

  /** Sends every collected edit. The responses are ignored: local state is already ahead. */
  private sendPending(): void {
    if (!this.pending.size) return;
    const batch = this.pending;
    this.pending = new Map();
    for (const [setId, changes] of batch) {
      this.api.updateSet(this.id, setId, changes).subscribe({
        error: () => this.api.getSession(this.id).subscribe((s) => this.setSession(s)),
      });
    }
  }

  // ── Restructuring ─────────────────────────────────────────────────────────────

  onDrop(event: CdkDragDrop<unknown>): void {
    const current = this.session();
    if (!current || event.previousIndex === event.currentIndex) return;
    const reordered = moveExercise(current, event.previousIndex, event.currentIndex);
    this.setSession(reordered);
    this.api
      .reorderSessionExercises(this.id, reordered.exercises.map((ex) => ex.id))
      .subscribe({ error: () => this.api.getSession(this.id).subscribe((s) => this.setSession(s)) });
  }

  openMenu(exercise: SessionExercise): void {
    this.menuFor.set(exercise);
  }

  toggleEditing(exercise: SessionExercise): void {
    this.editingId.update((id) => (id === exercise.id ? null : exercise.id));
    this.menuFor.set(null);
  }

  startSwap(exercise: SessionExercise): void {
    this.menuFor.set(null);
    this.swapping.set(exercise);
  }

  swapExercise(replacement: Exercise): void {
    const entry = this.swapping();
    this.swapping.set(null);
    if (!entry) return;
    this.api
      .updateSessionExercise(this.id, entry.id, { exercise_id: replacement.id })
      .subscribe((session) => {
        this.setSession(session);
        this.loadLastPerformance(session);
      });
  }

  removeExercise(exercise: SessionExercise): void {
    this.menuFor.set(null);
    this.api
      .removeExerciseFromSession(this.id, exercise.id)
      .subscribe((session) => this.setSession(session));
  }

  addExercises(picked: Exercise[]): void {
    this.showPicker.set(false);
    const current = this.session();
    if (!current) return;
    // Sequential: each call returns the whole session, so parallel requests would race and
    // the last response to land would win with a stale ordering.
    const add = (index: number): void => {
      if (index >= picked.length) return;
      this.api
        .addExerciseToSession(this.id, {
          exercise_id: picked[index].id,
          sets: [{ set_type: 'working_set', order: 0 }],
        })
        .subscribe((session) => {
          this.setSession(session);
          this.loadLastPerformance(session);
          add(index + 1);
        });
    };
    add(0);
  }

  // ── Finishing ─────────────────────────────────────────────────────────────────

  doFinish(): void {
    this.showFinishConfirm.set(false);
    this.sendPending();
    this.restTimer.stop();
    this.api.finishSession(this.id).subscribe((session) => {
      this.session.set(session);
      this.activeStore.clearSession();
      this.offerWriteBack(session);
    });
  }

  /**
   * A session that came from a template and beat it is the moment to update the template —
   * asked once, here, rather than left for a trip through the builder later.
   */
  private offerWriteBack(session: WorkoutSession): void {
    if (!session.template_id) {
      this.leave();
      return;
    }
    this.api.getTemplate(session.template_id).subscribe({
      next: (template) => {
        const improvements = proposeTemplateUpdate(template, session);
        if (!improvements.length) {
          this.leave();
          return;
        }
        this.template.set(template);
        this.improvements.set(improvements);
        this.showWriteBack.set(true);
      },
      error: () => this.leave(),
    });
  }

  templateName(): string {
    return this.template()?.name ?? 'the template';
  }

  isAccepted(improvement: ExerciseImprovement): boolean {
    return !this.declined().includes(improvement.templateExerciseId);
  }

  accepted(): ExerciseImprovement[] {
    return this.improvements().filter((improvement) => this.isAccepted(improvement));
  }

  toggleImprovement(improvement: ExerciseImprovement): void {
    const id = improvement.templateExerciseId;
    this.declined.update((ids) => (ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id]));
  }

  writeBack(): void {
    const template = this.template();
    if (!template) return;
    this.showWriteBack.set(false);
    this.api
      .updateTemplate(template.id, applyImprovements(template, this.accepted()))
      .subscribe({ next: () => this.leave(), error: () => this.leave() });
  }

  leave(): void {
    this.showWriteBack.set(false);
    this.router.navigate(['/workouts']);
  }

  /** Keeps a session worth repeating, with what was actually lifted as the targets. */
  saveAsTemplate(): void {
    const session = this.session();
    if (!session || this.savedTemplate()) return;
    this.api
      .createTemplate(templateFromSession(session, session.name))
      .subscribe(() => this.savedTemplate.set(true));
  }

  // ── Loading ───────────────────────────────────────────────────────────────────

  private setSession(session: WorkoutSession): void {
    this.session.set(session);
    if (this.isActive()) this.activeStore.setSession(session);
  }

  private loadLastPerformance(session: WorkoutSession): void {
    const missing = session.exercises
      .map((entry) => entry.exercise_id)
      .filter((id, index, ids) => ids.indexOf(id) === index && !(id in this.lastPerformance()));
    if (!missing.length) return;
    forkJoin(missing.map((id) => this.api.getLastPerformance(id))).subscribe((results) => {
      const merged = { ...this.lastPerformance() };
      missing.forEach((id, index) => (merged[id] = results[index]));
      this.lastPerformance.set(merged);
    });
  }
}
