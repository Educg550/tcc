import { SubmissionRouteParam } from "@/app/submissions/[submissionId]/api/types";
import applicantDtoToModel from "@/app/shared/data/mapper";
import convertFormToApplicantDto from "@/app/shared/data/mapper";
import getSession from "@/app/shared/session/getSession";
import { NextRequest } from "next/server";

export async function GET(
	_: NextRequest,
	{ params }: { params: Promise<SubmissionRouteParam> },
) {
	const { submissionId } = await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/submissions/${submissionId}?include_comments=true`,
		{
			cache: "no-store",
			credentials: "include",
			headers: await getSession(),
		},
	);

	if (!response.ok) return response;
	const data = await response.json();

	//if (data["detail"]) throw Error(data["detail"]);

	//const applicantDto = convertFormToApplicantDto(data.);
	return Response.json({
		summary: applicantDtoToModel(data.summary),
		submissionForm: data.submission_form,
	});
	//return Response.json(data);
}
