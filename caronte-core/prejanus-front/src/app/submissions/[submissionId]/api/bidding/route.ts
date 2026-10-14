import getSession from "@/app/shared/session/getSession";

interface SubmissionIdParameter {
	submissionId: string;
}

export async function POST(
	request: Request,
	{ params }: { params: Promise<SubmissionIdParameter> },
) {
	const { submissionId } = await params;
	const { bidding } = await request.json();

	const session = await getSession();
	return await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/bidding`,
		{
			method: "POST",
			body: JSON.stringify({
				bidding: bidding,
			}),
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
		},
	);
}
