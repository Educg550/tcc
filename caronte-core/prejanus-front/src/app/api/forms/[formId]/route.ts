import { NextRequest, NextResponse } from "next/server";
import getSession from "@/app/shared/session/getSession";

export async function GET(
	request: NextRequest,
	{ params }: { params: Promise<{ formId: string }> },
) {
	const { formId } = await params;
	const search = request.nextUrl.search;

	try {
		const response = await fetch(
			`${process.env.NEXT_PUBLIC_API_URL}/forms/${formId}${search || ""}`,
			{
				method: "GET",
				headers: await getSession(),
				credentials: "include",
			},
		);

		const form = await response.json();

		return NextResponse.json(form);
	} catch (error) {
		return NextResponse.json(
			{ error: "Erro ao carregar os formulários" },
			{ status: 500 },
		);
	}
}
