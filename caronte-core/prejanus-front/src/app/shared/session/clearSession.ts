"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function clearSession() {
	const cookieStore = await cookies();
	cookieStore.delete("session");
	redirect("/");
}
