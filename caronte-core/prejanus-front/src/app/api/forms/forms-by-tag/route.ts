import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";

export async function GET(request: NextRequest) {
	const year = request.nextUrl.searchParams.get("year");
	const edict_type = request.nextUrl.searchParams.get("edict_type");

	try {
		const response = await fetch(
			`${process.env.NEXT_PUBLIC_API_URL}/forms?year=${year}&notice=${edict_type}`,
			{
				method: "GET",
				headers: await getSession(),
				credentials: "include",
			},
		);
		const forms = await response.json();
		return NextResponse.json(forms);
	} catch (error) {
		return NextResponse.json(
			{ error: "Erro ao carregar os formulários" },
			{ status: 500 },
		);
	}
}
