import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { ApiService } from '../../../core/api/api.service';
import { ExerciseLibraryComponent } from './exercise-library.component';

describe('ExerciseLibraryComponent', () => {
  let fixture: ComponentFixture<ExerciseLibraryComponent>;
  let library: ExerciseLibraryComponent;

  function createSheet(): HTMLDialogElement | null {
    return fixture.nativeElement.querySelector('dialog.sheet-backdrop');
  }

  beforeEach(async () => {
    const api = jasmine.createSpyObj<ApiService>('ApiService', ['getExercises']);
    api.getExercises.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [ExerciseLibraryComponent],
      providers: [provideRouter([]), { provide: ApiService, useValue: api }],
    }).compileComponents();

    fixture = TestBed.createComponent(ExerciseLibraryComponent);
    library = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('opens the custom-exercise sheet as a modal dialog in the top layer', () => {
    library.showCreateSheet.set(true);
    fixture.detectChanges();

    expect(createSheet()?.matches(':modal')).toBeTrue();
  });

  it('forgets the sheet when the browser closes it, as Escape does', async () => {
    library.showCreateSheet.set(true);
    fixture.detectChanges();

    const sheet = createSheet()!;
    const closeEvent = new Promise((resolve) => sheet.addEventListener('close', resolve));
    sheet.close();
    await closeEvent;
    fixture.detectChanges();

    expect(library.showCreateSheet()).toBeFalse();
    expect(createSheet()).toBeNull();
  });
});
