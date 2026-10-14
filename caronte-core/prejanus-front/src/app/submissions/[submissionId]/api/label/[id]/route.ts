import getSession from "@/app/shared/session/getSession";

export interface DeleteCommentParam {
	id: string;
}

export async function DELETE(
	_: Request,
	{ params }: { params: Promise<DeleteCommentParam> },
) {
	const { id } = await params;
	return await fetch(
		process.env.NEXT_PUBLIC_API_URL + "/submissions/label/" + id,
		{
			method: "DELETE",
			credentials: "include",
			headers: await getSession(),
		},
	);
}
