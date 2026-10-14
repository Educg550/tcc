import getSession from "@/app/shared/session/getSession";
import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";

export async function POST(
	_: Request,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { submissionId } = await params;

	return await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/favorites`,
		{
			method: "POST",
			credentials: "include",
			headers: await getSession(),
		},
	);
}

export async function DELETE(
	_: Request,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { submissionId } = await params;

	return await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}/favorites`,
		{
			method: "DELETE",
			credentials: "include",
			headers: await getSession(),
		},
	);
}
