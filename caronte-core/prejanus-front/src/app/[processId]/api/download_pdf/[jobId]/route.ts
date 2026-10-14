import getSession from "@/app/shared/session/getSession";
import { NextRequest, NextResponse } from "next/server";

export async function GET(
	req: NextRequest,
	{ params }: { params: Promise<{ jobId: string }> },
) {
	const { jobId } = await params;

	const session = await getSession();
	const backendRes = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/edicts/download_pdf/${jobId}`,
		{
			headers: {
				"Content-Type": "application/json",
				cookie: session.Cookie,
			},
			credentials: "include",
		},
	);

	if (backendRes.status === 404) {
		return NextResponse.json(
			{ error: "PDF ainda não pronto" },
			{ status: 404 },
		);
	}

	if (!backendRes.ok) {
		return NextResponse.json(
			{ error: "Erro ao baixar PDF" },
			{ status: backendRes.status },
		);
	}

	const pdfBuffer = await backendRes.arrayBuffer();
	return new NextResponse(pdfBuffer, {
		headers: {
			"Content-Type": "application/pdf",
			"Content-Disposition": `inline; filename="${jobId}.pdf"`,
		},
	});
}
