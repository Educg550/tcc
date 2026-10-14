import useSWR from "swr";
import Comment from "@/app/model/comment";
import { useSnackbar } from "../../provider/messageContext";
import { useState } from "react";

export default function useComments(submissionId: string) {
	const url = `/submissions/${submissionId}/api/comment`;
	const { data, error, isLoading, mutate } = useSWR<Comment[]>(url, {
		fallbackData: [],
	});
	const [isAddingComment, setIsAddingComment] = useState(false);
	const { showSnackbar } = useSnackbar();

	const deleteComment = (id: number) => {
		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/comment/${id}`,
			{
				method: "DELETE",
			},
		)
			.then((res) => {
				if (!res.ok) return;
				if (!data) return;

				const updatedComments = data.filter(
					(comment) => comment.id !== id,
				);

				mutate(updatedComments, false);
				showSnackbar("Comentário removido", "success");
			})
			.catch((_) => {
				showSnackbar("Erro ao remover comentário", "error");
			});
	};

	const addComment = async (text: string) => {
		const trimmed = text.trim();
		if (!trimmed) return;

		try {
			setIsAddingComment(true);

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/comment`,
				{
					method: "POST",
					body: JSON.stringify({ text: trimmed }),
				},
			);

			if (!response.ok) throw response;

			await response.json();
			await mutate(); // revalida SWR
		} catch (error: any) {
			const errorData = await error.json();
			if (errorData) {
				showSnackbar(errorData.message || errorData.detail, "error");
			}
			throw error;
		} finally {
			setIsAddingComment(false);
		}
	};

	return {
		comments: data ?? [],
		isLoading,
		error,
		mutate,
		deleteComment,
		addComment,
		isAddingComment,
	};
}
