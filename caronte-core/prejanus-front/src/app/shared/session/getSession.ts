"use server";

import { cookies } from "next/headers";

export default async function getSession() {
	const cookieStore = await cookies();
	return { Cookie: `session=${cookieStore.get("session")?.value || ""}` };
}
