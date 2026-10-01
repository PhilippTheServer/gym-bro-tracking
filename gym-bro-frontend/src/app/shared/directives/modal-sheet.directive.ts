import { AfterViewInit, Directive, ElementRef, inject, output } from '@angular/core';

/**
 * Opens a bottom sheet's `<dialog>` as a modal, which puts it in the browser's top layer.
 *
 * Rendered in place, a sheet is a fixed overlay inside the scrolling content, and iOS
 * WebKit clips it to that scroller: the strip below the content, where the sheet's bottom
 * button sits, was cut off. Nothing clips the top layer.
 *
 * The owner shows the sheet with `@if` and removes it to close it; removal also takes the
 * dialog out of the top layer. When the browser closes the dialog itself (Escape, a back
 * gesture), `dismissed` asks the owner to do the same, so the app never believes a sheet
 * is open that isn't.
 */
@Directive({
  selector: 'dialog[gbModalSheet]',
  standalone: true,
  host: { '(close)': 'dismissed.emit()' },
})
export class ModalSheetDirective implements AfterViewInit {
  readonly dismissed = output<void>();

  private readonly dialog = inject<ElementRef<HTMLDialogElement>>(ElementRef).nativeElement;

  ngAfterViewInit(): void {
    this.dialog.showModal();
  }
}
