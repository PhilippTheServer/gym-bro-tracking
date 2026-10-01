import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  activeIcon: string;
}

@Component({
  selector: 'gb-bottom-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav class="bottom-nav">
      @for (item of navItems; track item.path) {
        <a
          [routerLink]="item.path"
          routerLinkActive="active"
          class="nav-item"
          [attr.aria-label]="item.label"
        >
          <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </a>
      }
    </nav>
  `,
  styles: [`
    .bottom-nav {
      display: flex;
      align-items: center;
      justify-content: space-around;
      background: var(--surface-1);
      border-top: 1px solid var(--separator);
      padding: 8px 0 env(safe-area-inset-bottom, 16px);
      position: relative;
      z-index: 100;
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
    }

    .nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      padding: 4px 16px;
      color: var(--text-tertiary);
      text-decoration: none;
      transition: color 0.15s ease;
      min-width: 60px;
      -webkit-tap-highlight-color: transparent;
    }

    .nav-item:active {
      opacity: 0.7;
      transform: scale(0.94);
    }

    .nav-item.active {
      color: var(--accent-orange);
    }

    .nav-icon {
      font-size: 22px;
      line-height: 1;
    }

    .nav-label {
      font-size: 10px;
      font-weight: 500;
      letter-spacing: 0.3px;
    }
  `],
})
export class BottomNavComponent {
  readonly navItems: NavItem[] = [
    { path: '/dashboard', label: 'Today', icon: '🏠', activeIcon: '🏠' },
    { path: '/workouts', label: 'History', icon: '📋', activeIcon: '📋' },
    { path: '/templates', label: 'Templates', icon: '📐', activeIcon: '📐' },
    { path: '/exercises', label: 'Exercises', icon: '💪', activeIcon: '💪' },
    { path: '/progress', label: 'Progress', icon: '📈', activeIcon: '📈' },
  ];
}
