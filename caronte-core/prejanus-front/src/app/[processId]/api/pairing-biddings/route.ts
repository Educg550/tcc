import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";

type TApiParams = {
	params: Promise<{
		processId: string;
	}>;
};

export async function POST(request: NextRequest, { params }: TApiParams) {
	const { processId } = await params;

	const processUrl = new URL(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/pairing-biddings`,
	);

	const session = await getSession();
	try {
		const response = await fetch(processUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			credentials: "include",
		});
		if (!response.ok) {
			return NextResponse.json(
				{ error: "Erro ao solicitar CSV" },
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
