import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";

type TApiParams = {
	params: Promise<{
		processId: string;
	}>;
};

export async function POST(request: NextRequest, { params }: TApiParams) {
	const { processId } = await params;
	const body = await request.json();

	const processUrl = `${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/slots`;
	const session = await getSession();
	try {
		const processSlotsResponse = await fetch(processUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			body: JSON.stringify(body),
			credentials: "include",
		});
		if (!processSlotsResponse.ok) throw new Error("");

		const processSlotsDTO: { amount: string } =
			await processSlotsResponse.json();

		return NextResponse.json(processSlotsDTO, { status: 200 });
	} catch (e) {
		return NextResponse.json(
			{
				message: `Erro ao definir número de candidatos`,
			},
			{ status: 400 },
		);
	}
}
