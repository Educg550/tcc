import { NextRequest, NextResponse } from "next/server";
import { TProcessDTO } from "../dtos/process.dto";
import { ToProcessDomain } from "../mappers/process";
import getSession from "@/app/shared/session/getSession";

type TApiParams = {
	params: Promise<{
		processId: string;
	}>;
};

export async function GET(_: NextRequest, { params }: TApiParams) {
	const { processId } = await params;

	const processUrl = `${process.env.NEXT_PUBLIC_API_URL}/edicts/${processId}`;

	try {
		const processResponse = await fetch(processUrl, {
			cache: "no-store",
			headers: await getSession(),
		});
		const processDTO: TProcessDTO = await processResponse.json();
		const edict = ToProcessDomain(processDTO);

		return NextResponse.json(edict);
	} catch (e) {
		console.error("Error fetching data:", e);
		return NextResponse.error();
	}
}
