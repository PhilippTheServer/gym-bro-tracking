import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { BottomNavComponent } from './bottom-nav.component';

/** The app shell's layout: sheets render inside the scrolling content, the tab bar after it. */
@Component({
  standalone: true,
  imports: [BottomNavComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="app-shell">
      <main class="app-content">
        @if (sheetOpen()) {
          <div class="sheet-backdrop"></div>
        }
      </main>
      <gb-bottom-nav />
    </div>
  `,
})
class ShellHost {
  readonly sheetOpen = signal(false);
}

describe('BottomNavComponent', () => {
  let fixture: ComponentFixture<ShellHost>;
  let nav: HTMLElement;

  function setSheetOpen(open: boolean): void {
    fixture.componentInstance.sheetOpen.set(open);
    fixture.detectChanges();
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ShellHost],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(ShellHost);
    fixture.detectChanges();
    nav = fixture.nativeElement.querySelector('.bottom-nav');
    // The state is under test, not the animation: without the transition the computed
    // style settles immediately instead of 200 ms later.
    nav.style.transition = 'none';
  });

  it('is shown while no sheet is open', () => {
    expect(getComputedStyle(nav).visibility).toBe('visible');
    expect(getComputedStyle(nav).opacity).toBe('1');
  });

  it('steps out of view while a sheet is open, so it cannot cover the sheet', () => {
    setSheetOpen(true);

    expect(getComputedStyle(nav).visibility).toBe('hidden');
    expect(getComputedStyle(nav).opacity).toBe('0');
  });

  it('comes back once the sheet closes', () => {
    setSheetOpen(true);
    setSheetOpen(false);

    expect(getComputedStyle(nav).visibility).toBe('visible');
    expect(getComputedStyle(nav).opacity).toBe('1');
  });
});
