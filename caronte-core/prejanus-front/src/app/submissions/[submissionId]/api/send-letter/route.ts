import getSession from "@/app/shared/session/getSession";

interface SubmissionSelectionIdParameter {
	submissionId: string;
}

export async function POST(
	request: Request,
	{ params }: { params: Promise<SubmissionSelectionIdParameter> },
) {
	const { submissionId } = await params;

	const session = await getSession();
	return await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/send-letter`,
		{
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
		},
	);
}
