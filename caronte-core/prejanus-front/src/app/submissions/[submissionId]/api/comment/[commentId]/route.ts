import getSession from "@/app/shared/session/getSession";

export interface DeleteCommentParam {
	commentId: string;
}

export async function DELETE(
	_: Request,
	{ params }: { params: Promise<DeleteCommentParam> },
) {
	const { commentId } = await params;
	return await fetch(
		process.env.NEXT_PUBLIC_API_URL + "/submissions/comments/" + commentId,
		{
			method: "DELETE",
			credentials: "include",
			headers: await getSession(),
		},
	);
}
