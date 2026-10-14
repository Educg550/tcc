import { applicantDtoToApplicantItem } from "@/app/[processId]/mappers/applicant";
import getSession from "@/app/shared/session/getSession";

export interface FavoritesRouteParam {
	processId: string;
}

export async function GET(
	_: Request,
	{ params }: { params: Promise<FavoritesRouteParam> },
) {
	const { processId } = await params;
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}/submissions?only_favorites=true`,
		{
			credentials: "include",
			headers: await getSession(),
		},
	);

	if (!response.ok) {
		return Response.json(
			{ error: "Erro ao consultar favoritos" },
			{ status: response.status },
		);
	}
	const { submissions } = await response.json();

	const candidates = submissions?.map(applicantDtoToApplicantItem) ?? [];
	return Response.json({
		candidates,
		itemCount: candidates.length,
		page: 1,
		totalItems: candidates.length,
	});
}
