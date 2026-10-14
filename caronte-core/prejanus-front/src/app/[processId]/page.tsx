"use client";

import DownloadIcon from "@mui/icons-material/Download";
import SubmissionListScaffolding from "@/app/[processId]/components/submission-list-scaffolding";
import {
	Box,
	Stack,
	Drawer,
	Divider,
	IconButton,
	Typography,
	Skeleton,
	Button,
	Select,
	MenuItem,
	Grid,
	Dialog,
	DialogContent,
	DialogActions,
	FormControlLabel,
	Checkbox,
	TextField,
	useMediaQuery,
} from "@mui/material";
import { useParams, useRouter } from "next/navigation";
import ProcessInfo from "./components/process-info";
import useSubmissionList from "./hooks/useSubmissionList";
import CloseIcon from "@mui/icons-material/Close";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ApprovalState } from "../model/application-candidate";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import CandidateDetailsPage from "./submissions/[submissionId]/candidate-details-page";
import { isAdminRole, RolesUser } from "../model/user";
import useProcess from "./hooks/useProcess";
import { useSnackbar } from "@/provider/messageContext";
import { UpdateViewOptionFn, ViewOptions } from "./models/viewOptions";
import EditableField from "./components/editable-field";
import TutorialDriver from "@/lib/tutorialDriver";
import "driver.js/dist/driver.css";
import { useUser } from "@/provider/UserProvider";
import theme from "../theme";

export default function Process() {
	const { processId } = useParams<{ processId: string | string[] }>();
	const router = useRouter();
	const [isModalOpen, setModalOpen] = useState(false);
	const [onlyFavorites, setOnlyFavorites] = useState(false);
	const [statsTab, setStatsTab] = useState<ApprovalState | undefined>(
		undefined,
	);
	const { user } = useUser();
	const [viewOptions, setViewOptions] = useState<ViewOptions>({
		collapsedSidebar: false,
	});
	const updateViewOption: UpdateViewOptionFn = useCallback((key, value) => {
		setViewOptions((prev) => ({ ...prev, [key]: value }));
	}, []);

	const { showSnackbar } = useSnackbar();

	const {
		data: process,
		error,
		isLoading,
		mutate,
		isAdvancingPhaseEdict,
		handleAdvancePhaseEdict,
		isHandleSlotsEdict,
		handleSlotsEdict,
		interactorEdictDownload,
		pairingBiddingsDownload,
		sections,
		inLoadingDownloadData,
		inLoadingDownloadPairing,
	} = useProcess({
		processId,
	});

	useEffect(() => {
		if (error) {
			showSnackbar("Ocorreu um erro ao carregar o edital", "error");
		}
	}, [error, showSnackbar]);

	const useSubmissionListValues = useSubmissionList({
		processId,
		onlyFavorites,
		stats: statsTab,
	});

	const [open, setOpen] = useState(false);

	const [candidateId, setCandidateId] = useState<string>();

	const toggleDrawer = useCallback(
		(newCandidateId?: string) => {
			if (newCandidateId) {
				setCandidateId(newCandidateId);
				setOpen(true);
				setViewOptions((prev) => ({ ...prev, collapsedSidebar: true }));
			} else {
				setOpen(false);
			}
		},
		[setCandidateId, setOpen],
	);

	useEffect(() => {
		if (isLoading && useSubmissionListValues.isLoading) return;

		const timeout = setTimeout(() => TutorialDriver(), 1000);
		return () => clearTimeout(timeout);
	}, [useSubmissionListValues.isLoading, isLoading]);

	const contentDrawer = useMemo(() => {
		if (!candidateId) return null;

		const parentData = {
			data: useSubmissionListValues.data,
			mutate: useSubmissionListValues.mutate,
			process: {
				data: process,
				isLoading,
			},
		};

		return (
			<CandidateDetailsPage
				submissionId={candidateId}
				currentUser={user}
				parentData={parentData}
			/>
		);
	}, [candidateId, user, useSubmissionListValues, process, isLoading]);

	const [enablePhase, setEnablePhase] = useState(false);
	const [phase, setPhase] = useState<string | undefined>(undefined);

	const [enableSlots, setEnableSlots] = useState(false);
	const [slots, setSlots] = useState<string>("");

	useEffect(() => {
		if (process && process.phases[process.phase]) {
			setPhase(process.phases[process.phase].id.toString());
		}
	}, [process]);

	useEffect(() => {
		if (process && process.slots) {
			setSlots(process.slots.toString());
		}
	}, [process]);

	const isXL = useMediaQuery(theme.breakpoints.up("xl"));

	const memoizedStyle = useMemo(() => {
		if (!open) return {};

		return {
			marginRight: {
				xl: "912px",
			},
		};
	}, [open]);

	return (
		<>
			<title>{isLoading ? "Edital" : process?.title}</title>

			<Box component={"main"} sx={memoizedStyle}>
				<Grid container spacing={2}>
					<Grid size={12}>
						<ProcessInfo
							isLoading={isLoading}
							process={process}
							mutate={useSubmissionListValues.mutate}
							onToggleFavoritesOnly={setOnlyFavorites}
							setStatsTab={setStatsTab}
							updateViewOption={updateViewOption}
							viewOption={viewOptions}
						/>
					</Grid>
					<Grid
						size={
							viewOptions.collapsedSidebar
								? { xs: 12 }
								: { xl: "grow", xs: 12 }
						}
					>
						<SubmissionListScaffolding
							processId={processId}
							useSubmissionListValues={useSubmissionListValues}
							phase={process?.phase}
							onCandidateClick={toggleDrawer}
							currentUser={user}
							sidebarIsOpen={open}
						/>
					</Grid>
					<Grid
						width="260px"
						sx={
							viewOptions.collapsedSidebar
								? { display: "none" }
								: {}
						}
					>
						<Box sx={{ position: "sticky", top: 25 }}>
							{(() => {
								if (
									isAdminRole(
										(user?.role as RolesUser) || undefined,
									)
								) {
									return (
										<>
											<EditableField
												isLoading={isLoading}
												isUpdatingField={
													isAdvancingPhaseEdict
												}
												label="Fase"
												setIsEditing={setEnablePhase}
												isEditing={enablePhase}
												onApply={() => {
													setModalOpen(true);
												}}
											>
												{!isLoading &&
												process &&
												phase ? (
													<Select
														disabled={!enablePhase}
														labelId="phase-label"
														value={phase}
														onChange={(event) => {
															setPhase(
																event.target
																	.value,
															);
														}}
														required
														fullWidth
													>
														{Object.keys(
															process.phases,
														).map((key) => {
															const value =
																process.phases[
																	key
																];

															return (
																<MenuItem
																	key={
																		value.id
																	}
																	value={
																		value.id
																	}
																>
																	{
																		value.label
																	}
																</MenuItem>
															);
														})}
													</Select>
												) : (
													<Skeleton width={210} />
												)}
											</EditableField>

											<Divider sx={{ mt: 2, mb: 2 }} />

											<EditableField
												label="Dados"
												isLoading={false}
											>
												<Stack
													flexDirection={"column"}
													sx={{ mb: 2 }}
												>
													{sections.sections.map(
														(section) => (
															<FormControlLabel
																key={section.id}
																control={
																	<Checkbox
																		value={
																			section.id
																		}
																		checked={sections.selectedSections.includes(
																			section.id,
																		)}
																		onChange={
																			sections.handleChange
																		}
																	/>
																}
																label={
																	section.label
																}
															/>
														),
													)}
												</Stack>
												<Stack
													alignItems={"center"}
													flexDirection={"row"}
													gap={1}
												>
													<Button
														color="primary"
														variant="outlined"
														loading={
															inLoadingDownloadData
														}
														onClick={() =>
															interactorEdictDownload()
														}
													>
														<DownloadIcon />
													</Button>
												</Stack>
											</EditableField>

											<Divider sx={{ mt: 2, mb: 2 }} />

											<EditableField
												label="Emparelhamento dos biddings"
												isLoading={false}
											>
												<Stack
													alignItems={"center"}
													flexDirection={"row"}
													gap={1}
												>
													<Button
														color="primary"
														variant="outlined"
														loading={
															inLoadingDownloadPairing
														}
														onClick={() =>
															pairingBiddingsDownload()
														}
													>
														<DownloadIcon />
													</Button>
												</Stack>
											</EditableField>

											<Divider sx={{ mt: 2, mb: 2 }} />
										</>
									);
								}
							})()}

							<EditableField
								isLoading={isLoading}
								isUpdatingField={isHandleSlotsEdict}
								label="Minha estimativa de vagas para orientação"
								setIsEditing={setEnableSlots}
								isEditing={enableSlots}
								onApply={() => {
									handleSlotsEdict(slots || "0");
								}}
							>
								{!isLoading && process ? (
									<TextField
										disabled={!enableSlots}
										type="number"
										variant="outlined"
										value={slots}
										autoComplete={"false"}
										onChange={(event) => {
											try {
												const value = parseInt(
													event.target.value,
												);
												setSlots(
													value > 0
														? value.toString()
														: "0",
												);
											} catch {
												setSlots("0");
											}
										}}
										slotProps={{
											input: {
												inputProps: {
													min: 0,
													pattern: "\\d*",
													inputMode: "numeric",
												},
											},
										}}
										fullWidth
									/>
								) : (
									<Skeleton width={210} />
								)}
							</EditableField>

							{/* <Divider sx={{ mb: 2 }} /> */}
						</Box>
					</Grid>
				</Grid>
			</Box>

			<Drawer
				anchor="right"
				open={open}
				onClose={() => toggleDrawer()}
				variant={isXL ? "persistent" : "temporary"}
				style={{
					zIndex: 1300,
				}}
			>
				<Box
					sx={{
						width: {
							xs: "100%",
							sm: 600,
							md: 768,
							lg: 912,
						},
					}}
				>
					<Box
						sx={{
							position: "sticky",
							top: 0,
							backgroundColor: "#fff",
							zIndex: 5000,
							padding: 1,
						}}
					>
						<Stack
							direction="row"
							sx={{
								alignItems: "center",
								justifyContent: "end",
								gap: 1,
								marginBottom: 1,
							}}
						>
							<IconButton
								onClick={() => {
									router.push(
										`/${processId}/submissions/${candidateId}`,
									);
								}}
							>
								<OpenInFullIcon />
							</IconButton>
							<IconButton onClick={() => toggleDrawer()}>
								<CloseIcon />
							</IconButton>
						</Stack>
						<Divider />
					</Box>
					<Box
						sx={{
							position: "relative",
							display: "block",
							padding: 1,
						}}
					>
						{contentDrawer}
					</Box>
				</Box>
			</Drawer>

			<Dialog
				open={isModalOpen}
				onClose={() => {
					setModalOpen(false);
				}}
			>
				<DialogContent>
					<Typography>
						Esta ação irá alterar o <i>status</i> do formulário
						correspondente aos candidatos do processo. Tem certeza
						de que deseja prosseguir com a alteração da fase?
					</Typography>
				</DialogContent>
				<DialogActions>
					<Button
						onClick={() => {
							setModalOpen(false);
							setEnablePhase(true);
						}}
						color="secondary"
					>
						Cancelar
					</Button>
					<Button
						onClick={() => {
							handleAdvancePhaseEdict(phase || "");
							setModalOpen(false);
						}}
						color="primary"
					>
						Confirmar
					</Button>
				</DialogActions>
			</Dialog>
		</>
	);
}
