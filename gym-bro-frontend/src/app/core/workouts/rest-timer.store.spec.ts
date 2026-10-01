import { TestBed } from '@angular/core/testing';
import { DEFAULT_REST_SECONDS, RestTimerStore } from './rest-timer.store';

describe('RestTimerStore', () => {
  let timer: RestTimerStore;

  beforeEach(() => {
    localStorage.clear();
    jasmine.clock().install();
    jasmine.clock().mockDate(new Date('2026-09-17T18:00:00Z'));
    TestBed.configureTestingModule({});
    timer = TestBed.inject(RestTimerStore);
  });

  afterEach(() => {
    timer.stop();
    jasmine.clock().uninstall();
    localStorage.clear();
  });

  it('is idle until a set is completed', () => {
    expect(timer.isRunning()).toBeFalse();
    expect(timer.secondsRemaining()).toBe(0);
  });

  it('counts down from the default rest', () => {
    timer.start('ex-1');
    expect(timer.secondsRemaining()).toBe(DEFAULT_REST_SECONDS);

    jasmine.clock().tick(30_000);
    expect(timer.secondsRemaining()).toBe(60);
    expect(timer.label()).toBe('1:00');
  });

  it('pads the seconds in the label', () => {
    timer.start('ex-1');
    jasmine.clock().tick(85_000);
    expect(timer.label()).toBe('0:05');
  });

  it('stops itself when the rest is up', () => {
    timer.start('ex-1');
    jasmine.clock().tick(DEFAULT_REST_SECONDS * 1000 + 500);
    expect(timer.isRunning()).toBeFalse();
  });

  it('extends the rest and remembers the longer one for that exercise', () => {
    timer.start('ex-1');
    timer.addSeconds(30);
    expect(timer.secondsRemaining()).toBe(DEFAULT_REST_SECONDS + 30);

    timer.stop();
    expect(timer.restSecondsFor('ex-1')).toBe(DEFAULT_REST_SECONDS + 30);
    // Another exercise keeps its own rest.
    expect(timer.restSecondsFor('ex-2')).toBe(DEFAULT_REST_SECONDS);
  });

  it('ignores an extension when nothing is resting', () => {
    timer.addSeconds(30);
    expect(timer.isRunning()).toBeFalse();
  });

  it('falls back to the default when storage holds nonsense', () => {
    localStorage.setItem('gym-bro.rest-seconds.ex-9', 'not-a-number');
    expect(timer.restSecondsFor('ex-9')).toBe(DEFAULT_REST_SECONDS);
  });
});
