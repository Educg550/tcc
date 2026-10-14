
import { applicantDtoToApplicantItem } from "@/app/[processId]/mappers/applicant";
import getSession from "@/app/shared/session/getSession";
import { NextRequest } from "next/server";

export interface EdictSubmissionsRouteParam {
	processId: string;
}

export async function GET(
	request: NextRequest,
	{ params }: { params: Promise<EdictSubmissionsRouteParam &  {formTypes:"recommenders"|"candidates"}> },
) {
	const { processId,formTypes } = await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/${formTypes}/forms/versions/unmapped`,
		{
			credentials: "include",
			headers: await getSession(),
		},
	);

	if (response.status === 401) {
		return new Response(JSON.stringify({ error: "unauthorized" }), {
			status: 401,
			headers: { "Content-Type": "application/json" },
		});
	}

	const data = await response.json();

	if (!response.ok)
		return new Response(JSON.stringify(data), { status: 500 });


	const versions = data;
	return Response.json(versions);
}
