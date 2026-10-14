import getSession from "@/app/shared/session/getSession";
import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";
import { getDaysFromDate } from "@/app/submissions/[submissionId]/api/utils";

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
			"/reesend_submission",
		{
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			body: JSON.stringify({
				text: text,
			}),
			credentials: "include",
		},
	);

	if (!response.ok) return response;

	const data = await response.json();

	return Response.json({
		message: data.message,
	});
}
