import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ApiService } from '../../../core/api/api.service';
import type { Exercise } from '../../../core/api/models';
import { ExercisePickerComponent } from './exercise-picker.component';

function exercise(id: string, name: string, overrides: Partial<Exercise> = {}): Exercise {
  return {
    id,
    name,
    muscle_group: 'back',
    primary_muscle: 'lats',
    equipment: 'cable',
    category: 'strength',
    is_custom: false,
    ...overrides,
  };
}

describe('ExercisePickerComponent', () => {
  let fixture: ComponentFixture<ExercisePickerComponent>;
  let picker: ExercisePickerComponent;
  let api: jasmine.SpyObj<ApiService>;

  const pulldown = exercise('1', 'Lat Pulldown');
  const row = exercise('2', 'Seated Cable Row');

  beforeEach(async () => {
    api = jasmine.createSpyObj<ApiService>('ApiService', ['getExercises', 'getRecentExercises']);
    api.getExercises.and.returnValue(of([pulldown, row]));
    api.getRecentExercises.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [ExercisePickerComponent],
      providers: [{ provide: ApiService, useValue: api }],
    }).compileComponents();

    fixture = TestBed.createComponent(ExercisePickerComponent);
    picker = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads the library on open', () => {
    expect(picker.results().length).toBe(2);
    expect(picker.loading()).toBeFalse();
  });

  it('emits immediately on a single pick', () => {
    const picked: Exercise[][] = [];
    picker.picked.subscribe((value) => picked.push(value));

    picker.choose(pulldown);

    expect(picked).toEqual([[pulldown]]);
  });

  it('collects several before emitting in multi mode', () => {
    fixture.componentRef.setInput('multi', true);
    const picked: Exercise[][] = [];
    picker.picked.subscribe((value) => picked.push(value));

    picker.choose(pulldown);
    picker.choose(row);

    expect(picked).toEqual([]);
    expect(picker.selected().length).toBe(2);

    picker.confirm();
    expect(picked).toEqual([[pulldown, row]]);
  });

  it('deselects on a second tap in multi mode', () => {
    fixture.componentRef.setInput('multi', true);

    picker.choose(pulldown);
    picker.choose(pulldown);

    expect(picker.selected()).toEqual([]);
    expect(picker.isSelected(pulldown)).toBeFalse();
  });

  it('refuses to confirm an empty selection', () => {
    fixture.componentRef.setInput('multi', true);
    const picked: Exercise[][] = [];
    picker.picked.subscribe((value) => picked.push(value));

    picker.confirm();

    expect(picked).toEqual([]);
  });

  it('asks the API for the chosen group and clears the primary muscle with it', () => {
    picker.selectGroup('back');
    picker.selectPrimaryMuscle('traps');
    expect(api.getExercises).toHaveBeenCalledWith(
      jasmine.objectContaining({ muscle_group: 'back', primary_muscle: 'traps' })
    );

    picker.selectGroup('legs');
    // A stale "traps" filter under Legs would return nothing at all.
    expect(picker.primaryMuscle()).toBeNull();
    expect(api.getExercises).toHaveBeenCalledWith(
      jasmine.objectContaining({ muscle_group: 'legs', primary_muscle: null })
    );
  });

  it('opens as a modal dialog in the top layer, where no scrolling ancestor can clip it', () => {
    const sheet = fixture.nativeElement.querySelector('.sheet-backdrop') as HTMLElement;

    expect(sheet.tagName).toBe('DIALOG');
    expect(sheet.matches(':modal')).toBeTrue();
  });

  it('reports a close when the browser closes the sheet, as Escape does', async () => {
    let closed = 0;
    picker.closed.subscribe(() => closed++);
    const sheet = fixture.nativeElement.querySelector('dialog.sheet-backdrop') as HTMLDialogElement;

    // The close event is queued as a task; the directive's listener runs before this one.
    const closeEvent = new Promise((resolve) => sheet.addEventListener('close', resolve));
    sheet.close();
    await closeEvent;

    expect(closed).toBe(1);
  });

  it('describes an exercise by its primary muscle and kit', () => {
    expect(picker.metaFor(pulldown)).toBe('Lats · Cable');
    expect(picker.metaFor(exercise('3', 'Plank', { primary_muscle: null, muscle_group: 'core' })))
      .toBe('Core · Cable');
  });
});
