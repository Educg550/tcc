import getSession from "@/app/shared/session/getSession";

export type UserDTO = {
	id: number;
	name: string;
	email: string;
	role: string;
};

export async function getCurrentUser(): Promise<UserDTO | null> {
	try {
		const res = await fetch(
			`${process.env.NEXT_PUBLIC_API_URL}/auth/login`,
			{
				credentials: "include",
				headers: await getSession(),
			},
		);

		if (!res.ok) return null;

		return await res.json();
	} catch {
		return null;
	}
}
