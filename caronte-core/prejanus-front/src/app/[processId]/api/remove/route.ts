import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";

type TApiParams = {
	params: Promise<{
		processId: string;
	}>;
};

export async function DELETE(request: NextRequest, { params }: TApiParams) {
	const { processId } = await params;

	const processUrl = `${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/remove`;

	try {
		const session = await getSession();
		const response = await fetch(processUrl, {
			method: "DELETE",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			credentials: "include",
		});
		if (!response.ok) {
			return NextResponse.error();
		}

		return NextResponse.json({});
	} catch (e) {
		console.error("Error fetching data:", e);
		return NextResponse.error();
	}
}
