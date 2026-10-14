import { EdictDTO } from "@/app/dtos/edict.dto";
import getSession from "@/app/shared/session/getSession";
import { NextResponse } from "next/server";

export async function GET() {
	try {
		const response = await fetch(
			`${process.env.NEXT_PUBLIC_API_URL}/edicts`,
			{
				cache: "no-store",
				headers: await getSession(),
			},
		);
		const data: EdictDTO[] = await response.json();

		const mappedData = data.map((proc) => ({
			id: proc.id,
			title: proc.title,
			year: proc.year,
			semester: proc.semester,
			edictType: proc.edict_type,
			isOpen: proc.is_open,
		}));

		return NextResponse.json(mappedData);
	} catch (error) {
		return NextResponse.json(
			{ error: "Erro ao carregar os editais" },
			{ status: 500 },
		);
	}
}

export async function POST(req: Request) {
	try {
		const body = await req.json();

		if (
			!body.title ||
			!body.description ||
			!body.year ||
			!body.semester ||
			!body.edict_type ||
			!body.candidate_forms ||
			!body.recommenders_forms ||
			body.is_open === undefined
		) {
			return NextResponse.json(
				{ message: "Todos os campos são obrigatórios" },
				{ status: 400 },
			);
		}

		const dates = [
			new Date(body.date_application),
			new Date(body.date_verification),
			new Date(body.date_evaluation),
			new Date(body.date_closed),
		];
		const checkSorted = (arr: any) =>
			arr.every(
				(value: any, index: number, array: any) =>
					index === 0 || value >= array[index - 1],
			);
		if (!checkSorted(dates)) {
			return NextResponse.json(
				{
					message:
						"As datas de término não podem ser anteriores às datas de início",
				},
				{ status: 400 },
			);
		}

		const session = await getSession();
		const response = await fetch(
			`${process.env.NEXT_PUBLIC_API_URL}/edicts`,
			{
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					cookie: session.Cookie,
				},
				body: JSON.stringify(body),
				credentials: "include",
			},
		);

		if (!response.ok) {
			const errorData = await response.json();
			return NextResponse.json(
				{ message: "Erro ao criar o edital", error: errorData },
				{ status: response.status },
			);
		}

		const createdEdict: EdictDTO = await response.json();

		return NextResponse.json(createdEdict, { status: 201 });
	} catch (error) {
		return NextResponse.json({ message: error }, { status: 500 });
	}
}
