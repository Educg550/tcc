import { applicantDtoToApplicantItem } from "@/app/[processId]/mappers/applicant";
import getSession from "@/app/shared/session/getSession";
import { NextRequest } from "next/server";

export interface EdictSubmissionsRouteParam {
	processId: string;
}

export async function GET(
	request: NextRequest,
	{ params }: { params: Promise<EdictSubmissionsRouteParam> },
) {
	const searchParams = request.nextUrl.searchParams;

	const { processId } = await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/submissions?${searchParams}`,
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
		return new Response(JSON.stringify(data), { status: response.status });

	const candidates = data.submissions?.map(applicantDtoToApplicantItem) ?? [];

	return Response.json({
		candidates,
		itemCount: candidates.length,
		page: 1,
		totalItems: candidates.length,
	});
}
