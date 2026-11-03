/**
 * Server-only database helper for the web layer.
 * Uses parameterized SQL with the `pg` driver — no ORM.
 * AGENTS.md: web/ reads the database; never writes schema.
 */
import "server-only";
import { Pool } from "pg";

// Singleton pool — reuse across requests in the same process.
let _pool: Pool | undefined;

export function getPool(): Pool {
  if (!_pool) {
    const url = process.env.DATABASE_URL;
    if (!url) {
      throw new Error(
        "DATABASE_URL is not set. Add it to web/.env.local"
      );
    }
    _pool = new Pool({
      connectionString: url,
      ssl: { rejectUnauthorized: false }, // required for Neon
      max: 5,
    });
  }
  return _pool;
}

