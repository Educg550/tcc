import getSession from "@/app/shared/session/getSession";
import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";

export async function GET(
	_: Request,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { submissionId } = await params;

	const session = await getSession();
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/labels`,
		{
			method: "GET",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			credentials: "include",
		},
	);

	if (!response.ok) return response;

	const data = await response.json();

	return Response.json({
		labels: data.labels,
	});
}
