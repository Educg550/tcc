import { getCurrentUser } from "@/lib/getCurrentUser";
import { NextResponse } from "next/server";

export async function GET() {
	try {
		const user = await getCurrentUser();

		return NextResponse.json(user);
	} catch (error) {
		return NextResponse.json(
			{ message: "Erro ao carregar o usuário" },
			{ status: 500 },
		);
	}
}
