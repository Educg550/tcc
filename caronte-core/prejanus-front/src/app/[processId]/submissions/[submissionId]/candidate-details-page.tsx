"use client";

import { useParams } from "next/navigation";
import useSWR from "swr";
import { useEffect, useState, useMemo } from "react";
import useCandidateDetails from "@/app/[processId]/submissions/[submissionId]/hooks/use-candidate-details";
import {
	Accordion,
	AccordionDetails,
	AccordionSummary,
	Box,
	CircularProgress,
	Link,
	MenuItem,
	Select,
	Skeleton,
	Stack,
	Typography,
} from "@mui/material";
import FavoriteButton from "@/app/components/favorite-button";
import User from "@/app/model/user";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import withElevationBackground from "@/components/CustomPaper";
import { KeyedMutator } from "swr";
import PagedCandidates from "@/app/model/paged-candidates";
import React from "react";
import { TProcess } from "@/app/[processId]/models/process";
import { TMapping } from "@/app/[processId]/models/mapping";
import Phases from "../../models/phases";
import ActivitiesViewer, {
	ActivityViewerOptionsEnum,
} from "./components/ActivitiesViewer";
import CandidateRecommendersInfo from "./components/CandidateRecommendersInfo";
import Sidebar from "./components/Sidebar";
import CandidateComments from "./components/CandidateComments";
import useUserInformations from "./hooks/useUserInformations";
import { smartLink } from "./utils/smartLink";
import CandidateAcceptInfo from "./components/CandidateAcceptInfo";
import { ApprovalState } from "../../../model/application-candidate";
import {
	FormSection,
	FormField,
} from "../../../model/application-candidate-form";
import Views from "@/app/[processId]/submissions/[submissionId]/components/Views";
import CandidateSubmittedDocs from "@/app/[processId]/submissions/[submissionId]/components/CandidateSubmittedDocs";
import { useSWRConfig } from "swr";
import { ApplicantItem } from "../../../model/application-candidate";

const DynamicSectionFields = ({
	section,
	loading,
}: {
	section: FormSection;
	loading: boolean;
}) => {
	if (loading) return <Skeleton variant="rectangular" height={100} />;

	return (
		<Stack spacing={2}>
			{section.fields.map((field) => {
				let value;
				switch (field.type) {
					case "CheckBox":
						const parsed = JSON.parse(field.value);
						value = Array.isArray(parsed)
							? parsed.join(", ")
							: field.value;
						break;
					default:
						value = field.value;
				}

				return (
					<Box key={field.field_id}>
						<Typography variant="caption" color="text.secondary">
							{field.label.pt}{" "}
							{/* TODO colocar de acordo com o idioma */}
						</Typography>
						<Typography variant="body1">{value || "-"}</Typography>
					</Box>
				);
			})}
		</Stack>
	);
};

const ElevatedAccordion = withElevationBackground(Accordion);

export default function CandidateDetailsPage({
	submissionId,
	currentUser,
	parentData,
}: {
	submissionId?: string | string[];
	currentUser?: User;
	parentData?: {
		data: PagedCandidates | undefined;
		mutate: KeyedMutator<PagedCandidates>;
		process: {
			data: TProcess | undefined;
			isLoading: boolean;
		};
	};
}) {
	const params = useParams<{
		submissionId: string | string[];
		processId: string;
	}>();
	submissionId = params.submissionId || submissionId;
	let processId = params.processId;

	const [activityViewerOption, setActivityViewerOption] =
		useState<ActivityViewerOptionsEnum>(() => {
			const saved =
				typeof window !== "undefined"
					? localStorage.getItem("activityViewerOption")
					: null;
			return (
				(saved as ActivityViewerOptionsEnum) ||
				ActivityViewerOptionsEnum.ALL_ACTIVITIES
			);
		});

	const {
		data,
		error: candidateLoadError,
		isLoading: loadingCandidate,
		isFavoriteLoading,
		handlePrivateNotesSend,
		handleSendAcceptForms,
		handleSendAcceptLetters,
		isSendingForms,
		isSendingLetter,
		handleFavoriteToggle,
		handleReesendInformationsSend,
		handleLabelAdd,
		isLabelAdding,
		handleLabelDelete,
		reloadData,
		isPrivateNotesSending,
	} = useCandidateDetails(parentData, submissionId, currentUser);

	const { candidateData, submissionForm } = data;

	const { mutate } = useSWRConfig();

	const { data: userData } = useUserInformations(submissionId);

	// estado para controlar quais seções estão expandidas
	const [expandedSections, setExpandedSections] = useState<
		Record<number, boolean>
	>({});

	useEffect(() => {
		if (submissionForm && Object.keys(expandedSections).length === 0) {
			const initial: Record<number, boolean> = {};
			submissionForm.forEach((s: FormSection) => {
				initial[s.id] = true;
			});
			setExpandedSections(initial);
		}
	}, [submissionForm]);

	useEffect(() => {
		let id = setTimeout(() => {
			fetch(`/prejanus/submissions/${submissionId}/api/view/`, {
				method: "POST",
			}).then(() => mutate(`/submissions/${submissionId}/api/view`));
		}, 4000);

		return () => {
			clearTimeout(id);
		};
	}, [mutate, submissionId]);

	if (!candidateData && candidateLoadError)
		return (
			<Stack
				alignItems="center"
				justifyContent="center"
				sx={{ height: "100%", py: 5 }}
			>
				<Typography variant="h6">Ops! Erro ao buscar dados.</Typography>
				<Typography color="error">
					{candidateLoadError?.info?.detail}
				</Typography>
			</Stack>
		);

	const toggleSection = (id: number) => {
		setExpandedSections((prev) => ({ ...prev, [id]: !prev[id] }));
	};

	return (
		<>
			<title>
				{loadingCandidate ? "Candidato" : candidateData?.name}
			</title>

			<Stack
				direction="column"
				sx={{
					height: "100%",
					width: "100%",
					flexGrow: 1,
					maxWidth: 1200,
					mx: "auto",
				}}
				spacing={2}
			>
				<Stack
					direction="row"
					sx={{ gap: 5, flexWrap: "wrap", px: 3, py: 2.5 }}
				>
					<Box
						sx={{
							flexGrow: 1,
							maxWidth: { sm: "100%", md: "calc(100% - 300px)" },
						}}
					>
						<Stack
							direction="column"
							sx={{ gap: 1, flexWrap: "wrap" }}
						>
							{isFavoriteLoading ? (
								<CircularProgress size={24} />
							) : (
								parentData?.process.data?.phase ===
									Phases.avaliacao && (
									<FavoriteButton
										isFavorite={candidateData?.isFavorite}
										toggleFavorite={handleFavoriteToggle}
									/>
								)
							)}
							{loadingCandidate ? (
								<Skeleton width={210} />
							) : (
								<Typography variant="h4">
									{candidateData?.name}
								</Typography>
							)}
							{loadingCandidate ? (
								<Skeleton width={160} />
							) : (
								<Typography
									variant="body2"
									color="text.secondary"
								>
									{candidateData?.email}
								</Typography>
							)}
							{candidateData?.lattesCurriculum && (
								<Link
									variant="body2"
									color="text.secondary"
									target="_blank"
									sx={{ wordBreak: "break-all" }}
									href={`${candidateData.lattesCurriculum}`}
								>
									{smartLink(
										`${candidateData.lattesCurriculum}`,
									)}
								</Link>
							)}
							{candidateData?.personalWebsite && (
								<Link
									variant="body2"
									color="text.secondary"
									target="_blank"
									sx={{
										wordBreak: "break-all",
									}}
									href={smartLink(
										candidateData?.personalWebsite,
									)}
								>
									{candidateData?.personalWebsite}
								</Link>
							)}
						</Stack>

						{submissionForm?.map((section: FormSection) => (
							<ElevatedAccordion
								key={section.id}
								elevation={1}
								expanded={!!expandedSections[section.id]}
								onChange={() => toggleSection(section.id)}
							>
								<AccordionSummary
									expandIcon={<ArrowDropDownIcon />}
								>
									<Typography variant="h6">
										{section.title.pt || "Sem nome"}
									</Typography>
								</AccordionSummary>
								<AccordionDetails>
									<DynamicSectionFields
										section={
											{
												...section,
												fields: section.fields.filter(
													(field) =>
														field.type != "File",
												),
											} // Retira todos que são arquivos
										}
										loading={loadingCandidate}
									/>
								</AccordionDetails>
							</ElevatedAccordion>
						))}

						<Typography variant="h5">
							Informações adicionais
						</Typography>

						{/*DOCUMENTOS */}
						<ElevatedAccordion
							key={"documents"}
							elevation={1}
							expanded={!!expandedSections[-1]}
							onChange={() => toggleSection(-1)}
						>
							<AccordionSummary
								expandIcon={<ArrowDropDownIcon />}
							>
								<Typography variant="h6">Documentos</Typography>
							</AccordionSummary>
							<AccordionDetails>
								{/*Simplificou-se a extração aqui mesmo na Prop*/}
								<CandidateSubmittedDocs
									submissionId={submissionId}
									loading={loadingCandidate}
									fields={submissionForm?.flatMap(
										(section: FormSection) =>
											section.fields.filter(
												(field) =>
													field.type === "File",
											),
									)}
								/>
							</AccordionDetails>
						</ElevatedAccordion>

						{/*INFORMAÇÕES DOS RECOMENDADORES*/}
						<ElevatedAccordion
							key="recommendersInfo"
							elevation={1}
							expanded={!!expandedSections[-2]}
							onChange={() => toggleSection(-2)}
						>
							<AccordionSummary
								expandIcon={<ArrowDropDownIcon />}
							>
								<Typography variant="h6">
									Informações dos Recomendadores
								</Typography>
							</AccordionSummary>
							<AccordionDetails>
								<CandidateRecommendersInfo
									info={candidateData?.recommendersInfo}
									loading={loadingCandidate}
								/>
							</AccordionDetails>
						</ElevatedAccordion>

						{candidateData?.stats === ApprovalState.Approved && (
							<ElevatedAccordion elevation={1}>
								<AccordionSummary
									expandIcon={<ArrowDropDownIcon />}
								>
									<Typography variant="h6">
										Informações de Aceite
									</Typography>
								</AccordionSummary>
								<AccordionDetails>
									<CandidateAcceptInfo
										info={candidateData?.acceptInfo}
										loading={loadingCandidate}
									/>
								</AccordionDetails>
							</ElevatedAccordion>
						)}

						{submissionId && (
							<ElevatedAccordion elevation={1}>
								<AccordionSummary
									expandIcon={<ArrowDropDownIcon />}
								>
									<Typography variant="h6">
										Visualizações
									</Typography>
								</AccordionSummary>
								<AccordionDetails>
									<Views
										submissionId={
											Array.isArray(submissionId)
												? submissionId[0]
												: submissionId
										}
									/>
								</AccordionDetails>
							</ElevatedAccordion>
						)}
						<Box sx={{ mt: 4 }}>
							<Stack
								direction="row"
								alignItems="center"
								justifyContent="space-between"
								mb={2}
							>
								<Typography variant="h6">Atividades</Typography>
								<Select
									value={activityViewerOption}
									onChange={(e) =>
										setActivityViewerOption(
											e.target
												.value as ActivityViewerOptionsEnum,
										)
									}
									size="small"
									sx={{ minWidth: 200 }}
								>
									<MenuItem
										value={
											ActivityViewerOptionsEnum.ALL_ACTIVITIES
										}
									>
										Todas Atividades
									</MenuItem>
									<MenuItem
										value={
											ActivityViewerOptionsEnum.INTERNAL_COMMENTS_ONLY
										}
									>
										Apenas Comentários
									</MenuItem>
									<MenuItem
										value={
											ActivityViewerOptionsEnum.HISTORY_ONLY
										}
									>
										Apenas Histórico
									</MenuItem>
								</Select>
							</Stack>

							<ActivitiesViewer
								submissionId={String(submissionId)}
								currentUser={currentUser}
								activityViewerOption={activityViewerOption}
							/>

							<CandidateComments
								submissionId={String(submissionId)}
								handleReesendInformationsSend={
									handleReesendInformationsSend
								}
								currentUser={currentUser}
								processData={parentData?.process.data}
							/>
						</Box>
					</Box>

					{/* Sidebar fixa */}
					<Box>
						<Sidebar
							processData={parentData?.process.data}
							candidateData={candidateData}
							isLoading={loadingCandidate}
							currentUser={currentUser}
							isPrivateNotesSending={isPrivateNotesSending}
							handlePrivateNotesSend={handlePrivateNotesSend}
							handleLabelAdd={handleLabelAdd}
							isLabelAdding={isLabelAdding}
							handleSendAcceptForms={handleSendAcceptForms}
							handleSendAcceptLetters={handleSendAcceptLetters}
							isSendingForms={isSendingForms}
							isSendingLetter={isSendingLetter}
							handleLabelDelete={handleLabelDelete}
							reloadData={reloadData}
							userData={userData}
						/>
					</Box>
				</Stack>
			</Stack>
		</>
	);
}
