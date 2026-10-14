import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";

type TApiParams = {
	params: Promise<{
		processId: string;
	}>;
};

export async function POST(_: NextRequest, { params }: TApiParams) {
	const { processId } = await params;

	const today = new Date();
	today.setDate(today.getDate() + 7);

	const body = {
		confirmation_deadline: today.toISOString().split("T")[0],
		send_approval_letter: true,
	};

	const processUrl = `${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/close`;

	try {
		const session = await getSession();
		const response = await fetch(processUrl, {
			method: "PATCH",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			body: JSON.stringify(body),
			credentials: "include",
		});
		if (!response.ok) {
			const errorData = await response.json();
			return;
		}

		return NextResponse.json(response);
	} catch (e) {
		console.error("Error fetching data:", e);
		return NextResponse.error();
	}
}
