import { ApplicantItem } from "@/app/model/application-candidate";
import { CandidateFieldProps } from "@/app/model/candidate-field";
import PagedCandidates from "@/app/model/paged-candidates";
import { CircularProgress, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";
import CandidateList from "./candidates-list";
import User from "@/app/model/user";

interface Props {
	processId: string | string[];
	onCandidateClick: (candidateId: string) => void;
	phase: string | undefined;
	useSubmissionListValues: {
		data?: PagedCandidates;
		error?: any;
		isLoading: boolean;
		mutate: (candidates: PagedCandidates) => void;
		selectedFields: CandidateFieldProps[];
	};
	currentUser?: User;
	sidebarIsOpen?: boolean;
}

export default function SubmissionListScaffolding({
	processId,
	phase,
	onCandidateClick,
	useSubmissionListValues,
	currentUser,
	sidebarIsOpen,
}: Props) {
	const { data, error, isLoading, mutate, selectedFields } =
		useSubmissionListValues;

	return (
		<PageContent
			data={data}
			isLoading={isLoading}
			phase={phase}
			error={error}
			onCandidateClick={onCandidateClick}
			mutate={mutate}
			processId={processId}
			selectedFields={selectedFields}
			currentUser={currentUser}
			sidebarIsOpen={sidebarIsOpen}
		/>
	);
}

function PageContent({
	data,
	isLoading,
	error,
	mutate,
	processId,
	selectedFields,
	onCandidateClick,
	currentUser,
	phase,
	sidebarIsOpen,
}: {
	data?: PagedCandidates;
	isLoading: boolean;
	phase: string | undefined;
	error?: any;
	mutate: (candidates: PagedCandidates) => void;
	processId: string | string[];
	selectedFields: CandidateFieldProps[];
	onCandidateClick: (candidateId: string) => void;
	currentUser?: User;
	sidebarIsOpen?: boolean;
}): ReactNode {
	if (isLoading)
		return (
			<>
				<Stack
					direction="column"
					alignItems="center"
					justifyContent="center"
					sx={{ height: "100%" }}
				>
					<CircularProgress sx={{ m: 4 }} />
				</Stack>
			</>
		);

	if (!data && error)
		// Falhou sem nenhum cache
		return (
			<>
				<Stack
					direction="column"
					alignItems="center"
					justifyContent="center"
					sx={{ height: "100%" }}
					spacing={2}
				>
					<Typography>Ops!</Typography>
					<Typography color="textSecondary">
						Aconteceu um erro ao recuperar os candidatos
					</Typography>
					<Typography color="error">{error?.info?.detail}</Typography>
				</Stack>
			</>
		);

	return (
		<>
			<CandidateList
				data={data!}
				phase={phase}
				shownFields={selectedFields}
				mutate={mutate}
				currentUser={currentUser}
				processId={processId}
				onCandidateClick={onCandidateClick}
				sidebarIsOpen={sidebarIsOpen}
			/>
		</>
	);
}
