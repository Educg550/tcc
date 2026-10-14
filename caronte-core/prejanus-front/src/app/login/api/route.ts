"use server";

import clearSession from "@/app/shared/session/clearSession";
import getSession from "@/app/shared/session/getSession";
import setSession from "@/app/shared/session/setSession";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
	const oauth_token = request.nextUrl.searchParams.get("oauth_token");
	const oauth_verifier = request.nextUrl.searchParams.get("oauth_verifier");
	try {
		let nextResponse = new NextResponse();
		let response = null;
		const session = await getSession();
		if (oauth_token && oauth_verifier) {
			const params = new URLSearchParams({
				oauth_token: oauth_token,
				oauth_verifier: oauth_verifier,
			});
			response = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL}/auth/login/senhaunica?${params.toString()}`,
				{
					method: "POST",
					headers: session,
					credentials: "include",
				},
			);
			nextResponse = new NextResponse(
				`<script type="text/javascript">self.close();</script>`,
				{ headers: { "content-type": "text/html" } },
			);
		} else {
			response = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL}/auth/login/senhaunica`,
				{
					method: "POST",
					headers: session,
					credentials: "include",
				},
			);
			const json = await response.json();
			nextResponse = NextResponse.json({
				url: json.redirect_to,
			});
		}
		const setCookie = response.headers.get("set-cookie");
		if (setCookie) {
			const cookie = parseSetCookieHeader(setCookie)["session"];
			if (cookie == "null") {
				throw new Error("Ocorreu uma falha");
			}
			setSession(cookie.toString());
		}
		return nextResponse;
	} catch (error) {
		console.error("Erro na rota /auth/login/senhaunica:", error);
		await clearSession();
		return NextResponse.json(
			{ error: "Erro ao realizar o login" },
			{ status: 500 },
		);
	}
}

function parseSetCookieHeader(cookieString: string) {
	const cookieObject: { [key: string]: string | boolean } = {};
	const parts = cookieString.split(";");

	const nameValue = parts[0].split("=");
	const name = decodeURIComponent(nameValue[0].trim());
	const value = decodeURIComponent(nameValue.slice(1).join("=").trim());
	cookieObject[name] = value;

	for (let i = 1; i < parts.length; i++) {
		const attribute = parts[i].trim();
		if (attribute.includes("=")) {
			const [key, val] = attribute
				.split("=")
				.map((s) => decodeURIComponent(s.trim()));
			cookieObject[key.toLowerCase()] = val;
		} else {
			// Handle flag attributes like 'Secure', 'HttpOnly'
			cookieObject[attribute.toLowerCase()] = true;
		}
	}
	return cookieObject;
}
