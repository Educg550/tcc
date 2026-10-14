import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";
import { TProcessDatesDTO } from "../../dtos/processDates.dto";

type TApiParams = {
	params: Promise<{
		processId: string;
	}>;
};

export async function POST(request: NextRequest, { params }: TApiParams) {
	const { processId } = await params;
	const body = await request.json();

	const processUrl = `${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/edit-date`;
	const session = await getSession();
	try {
		const processEditResponse = await fetch(processUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			body: JSON.stringify(body),
			credentials: "include",
		});
		if (!processEditResponse.ok) {
			const errorData = await processEditResponse.json();
			return NextResponse.json(
				{ message: "Erro ao editar o edital", error: errorData },
				{ status: processEditResponse.status },
			);
		}

		const processDatesDTO: TProcessDatesDTO =
			await processEditResponse.json();

		return NextResponse.json(processDatesDTO, { status: 200 });
	} catch (e) {
		console.error("Error fetching data:", e);
		return NextResponse.error();
	}
}
