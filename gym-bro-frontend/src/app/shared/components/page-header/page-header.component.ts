import { ChangeDetectionStrategy, Component, Input, output } from '@angular/core';
import { Location } from '@angular/common';

@Component({
  selector: 'gb-page-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="page-header">
      @if (showBack) {
        <button class="back-btn" (click)="onBack()" aria-label="Go back">
          <span>‹</span>
        </button>
      }
      <div class="header-content" [class.centered]="!showBack && !actionLabel">
        @if (subtitle) {
          <span class="subtitle">{{ subtitle }}</span>
        }
        <h1 class="title">{{ title }}</h1>
      </div>
      @if (actionLabel) {
        <button class="action-btn" (click)="action.emit()">{{ actionLabel }}</button>
      }
    </header>
  `,
  styles: [`
    .page-header {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      padding: 12px 20px 16px;
      min-height: 88px;
      gap: 8px;
    }

    .back-btn {
      background: none;
      border: none;
      color: var(--accent-blue);
      font-size: 32px;
      padding: 0 8px 0 0;
      cursor: pointer;
      line-height: 1;
      -webkit-tap-highlight-color: transparent;
      flex-shrink: 0;
    }

    .header-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .header-content.centered {
      align-items: center;
    }

    .subtitle {
      font-size: 13px;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 500;
    }

    .title {
      font-size: 34px;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0;
      line-height: 1.1;
      letter-spacing: -0.5px;
    }

    .action-btn {
      background: none;
      border: none;
      color: var(--accent-orange);
      font-size: 17px;
      font-weight: 600;
      cursor: pointer;
      padding: 8px 0 8px 8px;
      -webkit-tap-highlight-color: transparent;
      flex-shrink: 0;
    }
  `],
})
export class PageHeaderComponent {
  @Input() title = '';
  @Input() subtitle = '';
  @Input() showBack = false;
  @Input() actionLabel = '';

  readonly action = output<void>();

  constructor(private location: Location) {}

  onBack(): void {
    this.location.back();
  }
}
