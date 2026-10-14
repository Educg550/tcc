import { NextRequest } from "next/server";
import { SubmissionRouteParam } from "../types";
import getSession from "@/app/shared/session/getSession";

export async function POST(
	_: NextRequest,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { submissionId } = await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/view`,
		{
			method: "POST",
			cache: "no-store",
			credentials: "include",
			headers: await getSession(),
		},
	);

	if (!response.ok) return response;
	return new Response("OK", { status: 200 });
}

export async function GET(
	_: NextRequest,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { submissionId } = await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/view`,
		{
			cache: "no-store",
			credentials: "include",
			headers: await getSession(),
		},
	);

	if (!response.ok) return response;
	const views = await response.json();
	return Response.json(views);
}
