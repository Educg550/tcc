import CandidatesTable from "@/app/components/candidates-table";
import { ApplicantItem } from "@/app/model/application-candidate";
import { CandidateFieldProps } from "@/app/model/candidate-field";
import PagedCandidates from "@/app/model/paged-candidates";
import User from "@/app/model/user";
import { Box, Stack, Typography } from "@mui/material";
import { useCallback, useState } from "react";

interface Props {
	data: PagedCandidates;
	mutate: (candidates: PagedCandidates) => void;
	processId: string | string[];
	shownFields: CandidateFieldProps[];
	onCandidateClick: (candidateId: string) => any;
	phase: string | undefined;
	currentUser?: User;
	sidebarIsOpen?: boolean;
}

export default function CandidateList({
	data,
	mutate,
	processId,
	shownFields,
	onCandidateClick,
	currentUser,
	phase,
	sidebarIsOpen,
}: Props) {
	const onToggleFavorite = useCallback(
		(candidate: ApplicantItem) => {
			fetch(`submissions/${candidate.id}/api/favorite`, {
				method: candidate.isFavorite ? "DELETE" : "POST",
			})
				.then(() => {
					const index = data.candidates.findIndex(
						(applicant) => applicant.id === candidate.id,
					);
					const updatedCandidates = [...data.candidates];

					if (candidate.isFavorite)
						updatedCandidates.splice(index, 1);
					else
						updatedCandidates[index] = {
							...updatedCandidates[index],
							isFavorite: !candidate.isFavorite,
						};

					mutate({
						...data,
						candidates: updatedCandidates,
					});
				})
				.catch((e) => console.error(e));
		},
		[data, mutate],
	);

	const [resetKey, setResetKey] = useState(0);

	return (
		<Box
			sx={{
				display: "flex",
				width: "100%",
				height: "100%",
			}}
		>
			{data.candidates.length ? (
				<Box
					sx={{
						width: "100%",
						height: "100%",
						overflowY: "scroll",
					}}
				>
					<CandidatesTable
						key={resetKey}
						setResetKey={setResetKey}
						data={data}
						columns={shownFields}
						phase={phase}
						currentUser={currentUser}
						onCandidateClick={onCandidateClick}
						onToggleFavorite={onToggleFavorite}
						sidebarIsOpen={sidebarIsOpen}
					/>
				</Box>
			) : (
				<Stack
					direction="column"
					alignItems="center"
					justifyContent="center"
					sx={{ width: "100%", height: "100%" }}
				>
					<Typography>Nenhum candidato</Typography>
				</Stack>
			)}
		</Box>
	);
}
