import { useEffect, useState } from "react";
import useSWR, { KeyedMutator } from "swr";
import User from "@/app/model/user";
import ApplicationCandidate from "@/app/model/application-candidate";
import { ApplicantItem } from "@/app/model/application-candidate";
import { CandidateFormResponse } from "@/app/model/application-candidate-form";
import PagedCandidates from "@/app/model/paged-candidates";
import { useSnackbar } from "@/provider/messageContext";
import { TProcess } from "@/app/[processId]/models/process";

export default function useCandidateDetails(
	parentData?: {
		data: PagedCandidates | undefined;
		mutate: KeyedMutator<PagedCandidates>;
		process: {
			data: TProcess | undefined;
			isLoading: boolean;
		};
	},
	submissionId?: string | string[],
	currentUser?: User,
): {
	data: {
		candidateData: ApplicationCandidate | null;
		submissionForm: CandidateFormResponse;
	};
	error: boolean;
	isLoading: boolean;
	isFavoriteLoading: boolean;
	isPrivateNotesSending: boolean;
	isLabelAdding: boolean;
	isSendingForms: boolean;
	isSendingLetter: boolean;
	handlePrivateNotesSend: (note: string) => void;
	handleLabelDelete: (id: number) => void;
	handleFavoriteToggle: () => void;
	handleReesendInformationsSend: (comment: string) => void;
	handleLabelAdd: (label: string, color: string) => void;
	handleSendAcceptForms: () => void;
	handleSendAcceptLetters: () => void;
	reloadData: () => void;
} {
	const { showSnackbar } = useSnackbar();

	const { data, error, isLoading, mutate } = useSWR<{
		summary: ApplicationCandidate | null;
		submissionForm: CandidateFormResponse;
	}>(
		`/prejanus/submissions/${submissionId}/api`,
		(url: string) => fetch(url).then((res) => res.json()),
		{ fallbackData: { summary: null, submissionForm: [] } },
	);

	useEffect(() => {
		if (!parentData) return;
		if (!data?.summary) return;

		const candidate = parentData.data?.candidates.find(
			(c) => c.id.toString() === submissionId,
		);

		if (candidate && candidate.biddingUsers !== data.summary.biddingUsers) {
			mutate(
				{
					...data,
					summary: {
						...data.summary,
						biddingUsers: candidate.biddingUsers,
					},
				},
				{ revalidate: false },
			);
		}
	}, [parentData, data, submissionId]);

	const [favoriteLoading, setFavoriteLoading] = useState(false);
	const [isLabelAdding, setLabelAdd] = useState(false);
	const [isSendingForms, setSendingForms] = useState(false);
	const [isSendingLetter, setSendingLetter] = useState(false);
	const [isPrivateNotesSending, setPrivateNotesSending] = useState(false);

	function reloadData() {
		if (parentData) {
			parentData.mutate();
		}
		mutate();
	}

	function handleLabelAdd(label: string, color: string) {
		const trimmed = label.trim();
		if (!trimmed || trimmed == "") return;

		const exist = data?.summary?.labels.filter(
			(labelFilter) => labelFilter.label == label,
		);
		if (exist && exist.length > 0) {
			showSnackbar(
				"Já existe uma label com esse nome nesse candidato",
				"warning",
			);
			return;
		}

		setLabelAdd(true);
		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/label`,
			{
				method: "POST",
				body: JSON.stringify({
					label: label,
					color: color,
				}),
			},
		)
			.then((data) => data.json())
			.then(() => {
				reloadData();
				setLabelAdd(false);
			})
			.catch(() => setLabelAdd(false));
	}

	function handleFavoriteToggle() {
		setFavoriteLoading(true);
		const noLongerFavorite = !!data?.summary?.isFavorite;

		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/favorite`,
			{
				method: noLongerFavorite ? "DELETE" : "POST",
			},
		)
			.then((res) => {
				if (!res.ok) return setFavoriteLoading(false);

				reloadData();

				setFavoriteLoading(false);
			})
			.catch((_) => setFavoriteLoading(false));
	}

	function handleSendAcceptForms() {
		setSendingForms(true);
		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/send-accept`,
			{
				method: "POST",
			},
		)
			.then((data) => {
				if (!data.ok) throw data;
				return data.json();
			})
			.then(() => {
				reloadData();
				setSendingForms(false);
				showSnackbar("Enviado com sucesso", "info");
			})
			.catch(async (error) => {
				setSendingForms(false);
				const errorData = await error.json();
				if (errorData) {
					showSnackbar(
						errorData.message || errorData.detail,
						"error",
					);
				}
			});
	}

	function handleSendAcceptLetters() {
		setSendingLetter(true);
		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/send-letter`,
			{
				method: "POST",
			},
		)
			.then((data) => {
				if (!data.ok) throw data;
				return data.json();
			})
			.then(() => {
				reloadData();
				setSendingLetter(false);
				showSnackbar("Enviado com sucesso", "info");
			})
			.catch(async (error) => {
				setSendingLetter(false);
				const errorData = await error.json();
				if (errorData) {
					showSnackbar(
						errorData.message || errorData.detail,
						"error",
					);
				}
			});
	}

	function handleReesendInformationsSend(text: string) {
		const trimmed = text.trim();
		if (!trimmed) return;

		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/reesend`,
			{
				method: "POST",
				body: JSON.stringify({ text: trimmed }),
			},
		)
			.then((response) => {
				if (!response.ok) throw response;
				return response.json();
			})
			.then((data) => {
				mutate();
				showSnackbar(data.message, "info");
			})
			.catch(async (error) => {
				const errorData = await error.json();
				if (errorData) {
					showSnackbar(
						errorData.message || errorData.detail,
						"error",
					);
				}
			});
	}

	function handlePrivateNotesSend(text: string) {
		const trimmed = text.trim();
		if (!trimmed) return;

		setPrivateNotesSending(true);
		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/private-notes`,
			{
				method: "POST",
				body: JSON.stringify({ text: trimmed }),
			},
		)
			.then((data) => data.json())
			.then(() => {
				mutate();
				setPrivateNotesSending(false);
			})
			.catch((_) => setPrivateNotesSending(false));
	}

	function handleLabelDelete(id: number) {
		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/label/${id}`,
			{
				method: "DELETE",
			},
		)
			.then((res) => {
				if (!res.ok) return;

				reloadData();
			})
			.catch((_) => {});
	}

	return {
		data: {
			candidateData: data?.summary == undefined ? null : data?.summary,
			submissionForm: data?.submissionForm || [],
		},
		error: !!error,
		isLoading: isLoading,
		isLabelAdding: isLabelAdding,
		isFavoriteLoading: favoriteLoading,
		isPrivateNotesSending: isPrivateNotesSending,
		isSendingForms: isSendingForms,
		isSendingLetter,
		handleLabelAdd: handleLabelAdd,
		handleFavoriteToggle: handleFavoriteToggle,
		handlePrivateNotesSend: handlePrivateNotesSend,
		handleReesendInformationsSend: handleReesendInformationsSend,
		handleLabelDelete: handleLabelDelete,
		reloadData: reloadData,
		handleSendAcceptForms: handleSendAcceptForms,
		handleSendAcceptLetters: handleSendAcceptLetters,
	};
}
