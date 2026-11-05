"use server";

/**
 * Server actions for the "Add Company" UI.
 * Both actions require an active session (GitHub OAuth via next-auth).
 */
import { auth } from "@/auth";
import { detectAts, saveCompanySource, DetectResult } from "@/lib/companies";
import { revalidatePath } from "next/cache";

function requireAuth() {
  // We call auth() synchronously in the action; it returns a promise.
  return auth().then((session) => {
    if (!session?.user) {
      throw new Error("Unauthorized: you must be signed in to add a company.");
    }
  });
}

export interface DetectActionResult {
  ok: boolean;
  data?: DetectResult;
  error?: string;
}

/** Step 1: probe the ATS and return a preview (no DB writes). */
export async function detectAtsAction(
  companyName: string,
  careersUrl?: string
): Promise<DetectActionResult> {
  try {
    await requireAuth();

    if (!companyName.trim()) {
      return { ok: false, error: "Company name is required." };
    }

    const result = await detectAts({ companyName: companyName.trim(), careersUrl: careersUrl?.trim() || undefined });
    return { ok: true, data: result };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Step 2: save the confirmed source after the user clicks Confirm. */
export async function saveCompanyAction(result: DetectResult): Promise<{ ok: boolean; error?: string }> {
  try {
    await requireAuth();
    await saveCompanySource(result);
    revalidatePath("/");
    revalidatePath("/settings");
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

