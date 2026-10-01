import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ModalSheetDirective } from './modal-sheet.directive';

@Component({
  standalone: true,
  imports: [ModalSheetDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (open()) {
      <dialog gbModalSheet class="sheet-backdrop" (dismissed)="dismissals = dismissals + 1"></dialog>
    }
  `,
})
class SheetHost {
  readonly open = signal(true);
  dismissals = 0;
}

describe('ModalSheetDirective', () => {
  let fixture: ComponentFixture<SheetHost>;

  function sheet(): HTMLDialogElement | null {
    return fixture.nativeElement.querySelector('dialog');
  }

  function nextClose(dialog: HTMLDialogElement): Promise<unknown> {
    return new Promise((resolve) => dialog.addEventListener('close', resolve));
  }

  beforeEach(() => {
    fixture = TestBed.createComponent(SheetHost);
    fixture.detectChanges();
  });

  it('opens the dialog as a modal in the top layer', () => {
    expect(sheet()!.open).toBeTrue();
    expect(sheet()!.matches(':modal')).toBeTrue();
  });

  it('asks the owner to close when the browser closes the dialog', async () => {
    const dialog = sheet()!;
    const closed = nextClose(dialog);

    dialog.close();
    await closed;

    expect(fixture.componentInstance.dismissals).toBe(1);
  });

  it('leaves no modal behind when the owner removes it, and reports no dismissal', () => {
    const dialog = sheet()!;

    fixture.componentInstance.open.set(false);
    fixture.detectChanges();

    expect(sheet()).toBeNull();
    expect(dialog.matches(':modal')).toBeFalse();
    expect(fixture.componentInstance.dismissals).toBe(0);
  });
});
