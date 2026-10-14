import getSession from "@/app/shared/session/getSession";

interface SubmissionIdParameter {
	submissionId: string;
}

export async function POST(
	request: Request,
	{ params }: { params: Promise<SubmissionIdParameter> },
) {
	const { submissionId } = await params;
	const { semester } = await request.json();

	const session = await getSession();
	return await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/entry-semester`,
		{
			method: "POST",
			body: JSON.stringify({
				semester: semester,
			}),
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
		},
	);
}
