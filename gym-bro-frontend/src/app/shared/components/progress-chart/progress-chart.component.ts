import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import {
  Chart,
  ChartData,
  ChartOptions,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  LineController,
  Tooltip,
  Filler,
} from 'chart.js';
import type { ExerciseProgressPoint } from '../../../core/api/models';

Chart.register(
  CategoryScale, LinearScale, LineElement, PointElement, LineController, Tooltip, Filler
);

@Component({
  selector: 'gb-progress-chart',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<canvas #canvas></canvas>`,
  styles: [`
    :host { display: block; }
    canvas { width: 100% !important; }
  `],
})
export class ProgressChartComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('canvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  @Input({ required: true }) points: ExerciseProgressPoint[] = [];
  @Input() metric: 'max_weight' | 'total_volume' | 'estimated_1rm' = 'max_weight';
  @Input() label = 'Weight (kg)';

  private chart?: Chart;

  ngAfterViewInit(): void {
    this._buildChart();
  }

  ngOnChanges(): void {
    if (this.chart) this._updateChart();
  }

  ngOnDestroy(): void {
    this.chart?.destroy();
  }

  private _buildChart(): void {
    const ctx = this.canvasRef.nativeElement.getContext('2d')!;
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, 'rgba(255, 159, 10, 0.35)');
    gradient.addColorStop(1, 'rgba(255, 159, 10, 0)');

    this.chart = new Chart(ctx, {
      type: 'line',
      data: this._getData(gradient),
      options: this._getOptions(),
    });
  }

  private _updateChart(): void {
    if (!this.chart) return;
    const ctx = this.canvasRef.nativeElement.getContext('2d')!;
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, 'rgba(255, 159, 10, 0.35)');
    gradient.addColorStop(1, 'rgba(255, 159, 10, 0)');
    this.chart.data = this._getData(gradient);
    this.chart.update('active');
  }

  private _getData(gradient: CanvasGradient): ChartData<'line'> {
    return {
      labels: this.points.map((p) =>
        new Date(p.date).toLocaleDateString('de-DE', { day: '2-digit', month: 'short' })
      ),
      datasets: [
        {
          label: this.label,
          data: this.points.map((p) => p[this.metric]),
          borderColor: '#ff9f0a',
          backgroundColor: gradient,
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: '#ff9f0a',
          pointBorderColor: '#000',
          pointBorderWidth: 1.5,
          tension: 0.3,
          fill: true,
        },
      ],
    };
  }

  private _getOptions(): ChartOptions<'line'> {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#2c2c2e',
          titleColor: '#ffffff',
          bodyColor: '#ebebf599',
          borderColor: '#38383a',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 10,
          callbacks: {
            label: (ctx) => ` ${ctx.formattedValue} ${this.label.includes('kg') ? 'kg' : ''}`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(56,56,58,0.4)' },
          ticks: { color: '#ebebf599', font: { size: 11 } },
        },
        y: {
          grid: { color: 'rgba(56,56,58,0.4)' },
          ticks: { color: '#ebebf599', font: { size: 11 } },
        },
      },
      interaction: { mode: 'index', intersect: false },
    };
  }
}
