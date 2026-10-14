import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";
import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";

export async function PUT(
	request: NextRequest,
	{
		params,
	}: {
		params: Promise<
			SubmissionRouteParam & {
				version: number;
				formTypes: "candidates" | "recommenders";
			}
		>;
	},
) {
	const { submissionId, processId, mappingId, version, formTypes } =
		await params;
	const body = await request.json();
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/${formTypes}/mappings/versions/${version}/${mappingId}`,
		{
			method: "PUT",
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

export async function DELETE(
	request: NextRequest,
	{
		params,
	}: {
		params: Promise<
			SubmissionRouteParam & {
				version: number;
				formTypes: "candidates" | "recommenders";
			}
		>;
	},
) {
	const { submissionId, processId, mappingId, version, formTypes } =
		await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/${formTypes}/mappings/versions/${version}/${mappingId}`,
		{
			method: "DELETE",
			cache: "no-store",
			credentials: "include",
			headers: {
				...(await getSession()),
				"Content-Type": "application/json",
			},
		},
	);

	if (!response.ok) return response;
	const mapping = await response.json();
	return Response.json(mapping);
}
