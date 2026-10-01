import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { toQueryParams } from './exercise-taxonomy';
import type {
  Exercise,
  ExerciseDetail,
  ExerciseFilters,
  ExerciseProgress,
  LastPerformance,
  SessionExerciseUpdate,
  ProgressOverview,
  SessionExerciseCreate,
  SessionSetCreate,
  SessionSetUpdate,
  WorkoutSession,
  WorkoutSessionCreate,
  WorkoutTemplate,
  WorkoutTemplateCreate,
} from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  // Read lazily: runtime-config.json can rewrite environment.apiUrl during app init.
  private get base(): string {
    return environment.apiUrl;
  }

  // ── Exercises ───────────────────────────────────────────────────────────────

  getExercises(filters: ExerciseFilters = {}): Observable<Exercise[]> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(toQueryParams(filters))) {
      params = params.set(key, value);
    }
    return this.http.get<Exercise[]>(`${this.base}/exercises`, { params });
  }

  /** The exercises this user last trained — what the picker offers before you search. */
  getRecentExercises(limit = 12): Observable<Exercise[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<Exercise[]>(`${this.base}/exercises/recent`, { params });
  }

  getExercise(id: string): Observable<ExerciseDetail> {
    return this.http.get<ExerciseDetail>(`${this.base}/exercises/${id}`);
  }

  /** The last completed sets for this exercise — null when it has never been trained. */
  getLastPerformance(id: string): Observable<LastPerformance | null> {
    return this.http.get<LastPerformance | null>(`${this.base}/exercises/${id}/last-performance`);
  }

  createExercise(data: Partial<Exercise>): Observable<Exercise> {
    return this.http.post<Exercise>(`${this.base}/exercises`, data);
  }

  updateExercise(id: string, data: Partial<Exercise>): Observable<Exercise> {
    return this.http.patch<Exercise>(`${this.base}/exercises/${id}`, data);
  }

  deleteExercise(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/exercises/${id}`);
  }

  // ── Templates ───────────────────────────────────────────────────────────────

  getTemplates(): Observable<WorkoutTemplate[]> {
    return this.http.get<WorkoutTemplate[]>(`${this.base}/templates`);
  }

  getTemplate(id: string): Observable<WorkoutTemplate> {
    return this.http.get<WorkoutTemplate>(`${this.base}/templates/${id}`);
  }

  createTemplate(data: WorkoutTemplateCreate): Observable<WorkoutTemplate> {
    return this.http.post<WorkoutTemplate>(`${this.base}/templates`, data);
  }

  updateTemplate(id: string, data: Partial<WorkoutTemplateCreate>): Observable<WorkoutTemplate> {
    return this.http.put<WorkoutTemplate>(`${this.base}/templates/${id}`, data);
  }

  deleteTemplate(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/templates/${id}`);
  }

  // ── Workouts ─────────────────────────────────────────────────────────────────

  getSessions(limit = 50, offset = 0): Observable<WorkoutSession[]> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<WorkoutSession[]>(`${this.base}/workouts`, { params });
  }

  getActiveSession(): Observable<WorkoutSession | null> {
    return this.http.get<WorkoutSession | null>(`${this.base}/workouts/active`);
  }

  getSession(id: string): Observable<WorkoutSession> {
    return this.http.get<WorkoutSession>(`${this.base}/workouts/${id}`);
  }

  startSession(data: WorkoutSessionCreate): Observable<WorkoutSession> {
    return this.http.post<WorkoutSession>(`${this.base}/workouts`, data);
  }

  updateSession(id: string, data: { name?: string; notes?: string }): Observable<WorkoutSession> {
    return this.http.patch<WorkoutSession>(`${this.base}/workouts/${id}`, data);
  }

  finishSession(id: string): Observable<WorkoutSession> {
    return this.http.post<WorkoutSession>(`${this.base}/workouts/${id}/finish`, {});
  }

  deleteSession(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/workouts/${id}`);
  }

  addExerciseToSession(
    sessionId: string,
    data: SessionExerciseCreate
  ): Observable<WorkoutSession> {
    return this.http.post<WorkoutSession>(
      `${this.base}/workouts/${sessionId}/exercises`,
      data
    );
  }

  addSet(
    sessionId: string,
    exerciseId: string,
    data: SessionSetCreate
  ): Observable<WorkoutSession> {
    return this.http.post<WorkoutSession>(
      `${this.base}/workouts/${sessionId}/exercises/${exerciseId}/sets`,
      data
    );
  }

  updateSet(
    sessionId: string,
    setId: string,
    data: SessionSetUpdate
  ): Observable<WorkoutSession> {
    return this.http.patch<WorkoutSession>(
      `${this.base}/workouts/${sessionId}/sets/${setId}`,
      data
    );
  }

  deleteSet(sessionId: string, setId: string): Observable<WorkoutSession> {
    return this.http.delete<WorkoutSession>(
      `${this.base}/workouts/${sessionId}/sets/${setId}`
    );
  }

  removeExerciseFromSession(
    sessionId: string,
    sessionExerciseId: string
  ): Observable<WorkoutSession> {
    return this.http.delete<WorkoutSession>(
      `${this.base}/workouts/${sessionId}/exercises/${sessionExerciseId}`
    );
  }

  /** The full list, in its new order — the API rejects a partial one. */
  reorderSessionExercises(sessionId: string, exerciseIds: string[]): Observable<WorkoutSession> {
    return this.http.patch<WorkoutSession>(
      `${this.base}/workouts/${sessionId}/exercises/reorder`,
      { exercise_ids: exerciseIds }
    );
  }

  updateSessionExercise(
    sessionId: string,
    sessionExerciseId: string,
    data: SessionExerciseUpdate
  ): Observable<WorkoutSession> {
    return this.http.patch<WorkoutSession>(
      `${this.base}/workouts/${sessionId}/exercises/${sessionExerciseId}`,
      data
    );
  }

  // ── Progress ─────────────────────────────────────────────────────────────────

  getProgressOverview(): Observable<ProgressOverview> {
    return this.http.get<ProgressOverview>(`${this.base}/progress/overview`);
  }

  getExerciseProgress(exerciseId: string): Observable<ExerciseProgress> {
    return this.http.get<ExerciseProgress>(
      `${this.base}/progress/exercises/${exerciseId}`
    );
  }
}
