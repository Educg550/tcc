import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";
import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";

export async function GET(
	_: NextRequest,
	{
		params,
	}: {
		params: Promise<
			SubmissionRouteParam & { formTypes: "recommenders" | "candidates" }
		>;
	},
) {
	const { submissionId, processId, formTypes } = await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/${formTypes}/mappings`,
		{
			cache: "no-store",
			credentials: "include",
			headers: await getSession(),
		},
	);

	if (!response.ok) return response;
	const mapping = await response.json();
	return Response.json(mapping);
}

export async function POST(
	request: NextRequest,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { processId } = await params;

	const searchParams = request.nextUrl.searchParams;
	const form_id = searchParams.get("form_id");
	const form_type = "candidate";
	const body = await request.json();

	if (!form_id) {
		return new Response("Missing form_id", { status: 400 });
	}

	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/mapping?form_id=${form_id}&form_type=${form_type}`,
		{
			method: "POST",
			cache: "no-store",
			credentials: "include",
			headers: {
				...(await getSession()),
				"Content-Type": "application/json",
			},
			body: JSON.stringify(body),
		},
	);

	if (!response.ok) return response;
	return new Response("OK", { status: 200 });
}
