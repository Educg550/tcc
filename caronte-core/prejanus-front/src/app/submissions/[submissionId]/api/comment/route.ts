import getSession from "@/app/shared/session/getSession";
import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";
import { getDaysFromDate } from "@/app/submissions/[submissionId]/api/utils";
import { NextResponse, NextRequest } from "next/server";
import { commentsFromDto } from "../../../../shared/data/mapper";
import ApplicantDto from "../dto/applicant-dto";

export async function POST(
	request: Request,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { text } = await request.json();
	const { submissionId } = await params;

	const session = await getSession();
	const response = await fetch(
		process.env.NEXT_PUBLIC_API_URL +
			"/submissions/" +
			submissionId +
			"/comments",
		{
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			body: JSON.stringify({
				comment: text,
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString(),
			}),
			credentials: "include",
		},
	);

	if (!response.ok) {
		const errorData = await response.json();
		return NextResponse.json(
			{ message: errorData, error: errorData },
			{ status: response.status },
		);
	}

	const data = await response.json();

	return Response.json({
		id: data.id,
		user: data.user,
		text: data.comment,
		postedWhen: getDaysFromDate(data.created_at),
	});
}

// Get all comments
export async function GET(
	request: Request,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { submissionId } = await params;
	const session = await getSession();

	const response = await fetch(
		process.env.NEXT_PUBLIC_API_URL +
			"/submissions/" +
			submissionId +
			"/comments",
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
		const errorData = await response.json();
		return NextResponse.json(
			{ message: errorData, error: errorData },
			{ status: response.status },
		);
	}

	const data = (await response.json()) as ApplicantDto["comments"];

	return Response.json(commentsFromDto(data));
}
