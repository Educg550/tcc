import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";

type TApiParams = {
	params: Promise<{
		processId: string;
	}>;
};

export async function POST(request: NextRequest, { params }: TApiParams) {
	const { processId } = await params;
	const mode = request.nextUrl.searchParams.get("mode");
	const body = await request.json();

	const processUrl = new URL(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/interactors_list`,
	);
	if (mode) processUrl.searchParams.set("mode", mode);

	const session = await getSession();
	try {
		const response = await fetch(processUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			body: JSON.stringify(body),
			credentials: "include",
		});
		if (!response.ok) {
			return NextResponse.json(
				{ error: "Erro ao solicitar PDF" },
				{ status: response.status },
			);
		}
		const data = await response.json();
		return NextResponse.json(data);
	} catch (e) {
		console.error("Error fetching data:", e);
		return NextResponse.json({ error: "Erro interno" }, { status: 500 });
	}
}
