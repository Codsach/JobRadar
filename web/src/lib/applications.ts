/**
 * Application tracker data access layer.
 * Stored in PostgreSQL `applications` table.
 * AGENTS.md: web/ may write to `preferences` and `applications`.
 */
import "server-only";
import { getPool } from "./db";
import { ApplicationItem, ApplicationStatus } from "./application-types";

export * from "./application-types";

export async function getApplications(): Promise<ApplicationItem[]> {
  const pool = getPool();
  const query = `
    SELECT
      a.id,
      a.job_id,
      a.status,
      a.notes,
      a.created_at AT TIME ZONE 'UTC' AS created_at,
      a.updated_at AT TIME ZONE 'UTC' AS updated_at,
      j.title,
      c.name AS company_name,
      j.location,
      j.url,
      j.category,
      j.level,
      j.posted_at AT TIME ZONE 'UTC' AS posted_at,
      j.first_seen_at AT TIME ZONE 'UTC' AS first_seen_at
    FROM applications a
    JOIN jobs j ON j.id = a.job_id
    JOIN companies c ON c.id = j.company_id
    ORDER BY a.updated_at DESC
  `;

  const { rows } = await pool.query(query);

  return rows.map((r) => ({
    ...r,
    created_at: new Date(r.created_at).toISOString(),
    updated_at: new Date(r.updated_at).toISOString(),
    posted_at: r.posted_at ? new Date(r.posted_at).toISOString() : null,
    first_seen_at: new Date(r.first_seen_at).toISOString(),
  }));
}

export async function saveApplication(
  jobId: number,
  status: ApplicationStatus,
  notes: string | null
): Promise<void> {
  const pool = getPool();
  const query = `
    INSERT INTO applications (job_id, status, notes, created_at, updated_at)
    VALUES ($1, $2, $3, NOW(), NOW())
    ON CONFLICT (job_id) DO UPDATE SET
      status = EXCLUDED.status,
      notes = EXCLUDED.notes,
      updated_at = NOW()
  `;

  await pool.query(query, [jobId, status, notes ?? null]);
}

export async function deleteApplication(jobId: number): Promise<void> {
  const pool = getPool();
  await pool.query(`DELETE FROM applications WHERE job_id = $1`, [jobId]);
}
