import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";
import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";

export async function POST(
	request: NextRequest,
	{
		params,
	}: {
		params: Promise<
			SubmissionRouteParam & {
				version: number;
				formTypes: "recommenders" | "candidates";
			}
		>;
	},
) {
	const { submissionId, processId, version, formTypes } = await params;
	const body = await request.json();
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/${formTypes}/mappings/versions/${version}/`,
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
	const mapping = await response.json();
	return Response.json(mapping);
}
