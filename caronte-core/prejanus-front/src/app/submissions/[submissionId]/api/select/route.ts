import getSession from "@/app/shared/session/getSession";

interface SubmissionSelectionIdParameter {
	submissionId: string;
}

export async function POST(
	request: Request,
	{ params }: { params: Promise<SubmissionSelectionIdParameter> },
) {
	const { submissionId } = await params;
	const { supervisorId, stats } = await request.json();

	const session = await getSession();
	return await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/select`,
		{
			method: "POST",
			body: JSON.stringify({
				user_ids: supervisorId ?? null,
				stats: stats,
			}),
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
		},
	);
}
