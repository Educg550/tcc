"use server";

import { cookies } from "next/headers";

export default async function setSession(session: string) {
	const cookieStore = await cookies();
	cookieStore.set("session", session);
}
