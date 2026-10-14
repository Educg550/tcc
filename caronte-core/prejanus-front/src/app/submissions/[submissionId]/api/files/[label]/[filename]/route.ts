import getSession from "@/app/shared/session/getSession";
import { NextRequest, NextResponse } from "next/server";

export interface GetFileByName {
	submissionId: string;
	label: string;
	filename: string;
}

export async function GET(
	request: NextRequest,
	{ params }: { params: Promise<GetFileByName> },
) {
	const { submissionId, label, filename } = await params;

	const session = await getSession();
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/files/${label}/${filename}`,
		{
			method: "GET",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			credentials: "include",
		},
	);

	if (!response.ok) {
		if (response.status == 401) {
			return NextResponse.redirect(
				`${process.env.NEXT_PUBLIC_BASE_URL}${process.env.NEXT_PUBLIC_BASE_PATH}/login`,
			);
		}
		return response;
	}

	const headers = new Headers();
	headers.append("Content-Disposition", `inline; filename="${filename}"`);
	headers.append("Content-Type", "application/pdf");

	return new NextResponse(await response.blob(), {
		headers,
	});
}
