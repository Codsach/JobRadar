"use server";

import { revalidatePath } from "next/cache";
import { ApplicationStatus, saveApplication, deleteApplication } from "@/lib/applications";

export async function updateJobApplicationAction(
  jobId: number,
  status: ApplicationStatus,
  notes: string | null
) {
  await saveApplication(jobId, status, notes);
  revalidatePath("/");
  revalidatePath("/tracker");
}

export async function deleteJobApplicationAction(jobId: number) {
  await deleteApplication(jobId);
  revalidatePath("/");
  revalidatePath("/tracker");
}

