import EditableField from "@/app/[processId]/components/editable-field";
import Phases from "@/app/[processId]/models/phases";
import { TProcess } from "@/app/[processId]/models/process";
import ApplicationCandidate, {
	ApprovalState,
} from "@/app/model/application-candidate";
import Label from "@/app/model/label";
import User, { isAdminRole, RolesUser } from "@/app/model/user";
import DoneIcon from "@mui/icons-material/Done";
import UserInfo from "@/app/model/user-info";
import {
	Autocomplete,
	Box,
	Button,
	Chip,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	Divider,
	Link,
	Skeleton,
	Stack,
	TextField,
	Tooltip,
	Typography,
} from "@mui/material";
import { useState } from "react";
import { getTextColor } from "../utils/utils";
import SelectStats from "@/app/components/select-stats";
import LockOpenIcon from "@mui/icons-material/LockOpen";
import SelectBidding from "@/app/components/select-bidding";
import { SentStatus } from "@/app/submissions/[submissionId]/api/dto/applicant-dto";
import { sentLabels } from "@/app/[processId]/mappers/applicant";
import SelectSemester from "@/app/components/select-semester";

interface Props {
	processData?: TProcess;
	candidateData: ApplicationCandidate | null;
	isLoading: boolean;
	currentUser?: User;
	userData?: UserInfo;
	isPrivateNotesSending: boolean;
	handleLabelAdd: (label: string, color: string) => void;
	isLabelAdding: boolean;
	isSendingForms: boolean;
	isSendingLetter: boolean;
	handlePrivateNotesSend: (text: string) => void;
	handleSendAcceptForms: () => void;
	handleSendAcceptLetters: () => void;
	handleLabelDelete: (id: number) => void;
	reloadData: () => void;
}

export default function Sidebar({
	processData,
	candidateData,
	isLoading,
	currentUser,
	userData,
	isPrivateNotesSending,
	handlePrivateNotesSend,
	handleLabelAdd,
	handleSendAcceptForms,
	handleSendAcceptLetters,
	isSendingForms,
	isSendingLetter,
	isLabelAdding,
	handleLabelDelete,
	reloadData,
}: Props) {
	const [enablePrivateNotes, setEnablePrivateNotes] = useState(false);
	const [enableLabel, setEnableLabel] = useState(false);
	const [label, setLabel] = useState<{ label: string; color: string }>({
		label: "",
		color: "#357535",
	});
	const [privateNotes, setPrivateNotes] = useState(
		candidateData?.privateNotes,
	);
	const [isModalFormsOpen, setModalFormsOpen] = useState(false);
	const [isModalLetterOpen, setModalLetterOpen] = useState(false);

	if (!processData || processData.phase !== Phases.avaliacao) return <></>;

	const acceptSentStatus = candidateData?.acceptInfo.find(
		(value) => value.name == "accept.sent",
	)?.value;

	const acceptInfo = candidateData?.acceptInfo.find(
		(value) => value.name == "accept.accept",
	)?.value;

	const semesterSubmission = candidateData?.applicationInfo.find(
		(value) => value.name == "research.semester",
	)?.value;

	return (
		<>
			<Box sx={{ position: "sticky", top: 25 + 57 + 16, maxWidth: 250 }}>
				<EditableField
					isLoading={isLoading}
					label="Manifestar Interesse"
					accessLevel={{
						lock: true,
						title: "Disponível apenas para você",
					}}
				>
					{!isLoading && candidateData ? (
						<SelectBidding
							row={candidateData}
							callback={reloadData}
						/>
					) : (
						<Skeleton width={210} sx={{ mb: 2 }} />
					)}
				</EditableField>

				<Divider sx={{ mb: 2 }} />

				<EditableField
					isLoading={isLoading}
					isUpdatingField={isLabelAdding}
					label="Rótulos"
					accessLevel={{
						lock: true,
						title: "Disponível apenas para você",
					}}
					setIsEditing={setEnableLabel}
					isEditing={enableLabel}
					onApply={() => {
						if (label) handleLabelAdd(label.label, label.color);
					}}
				>
					{!isLoading && process ? (
						enableLabel ? (
							<Stack
								direction="row"
								alignItems="center"
								sx={{ mb: 2 }}
								gap={1}
							>
								<Autocomplete
									fullWidth
									freeSolo
									disableClearable
									onInputChange={(event, newInputValue) => {
										if (newInputValue) {
											setLabel((prev) => ({
												...prev,
												label: newInputValue,
											}));
										}
									}}
									onChange={(event, newValue, reason) => {
										if (newValue) {
											setLabel((prev) => ({
												...prev,
												label: (newValue as Label)
													.label,
												color: (newValue as Label)
													.color,
											}));
										}
									}}
									renderOption={(props, option) => {
										const { key, ...optionProps } = props;
										return (
											<li key={key} {...optionProps}>
												<Box
													component={DoneIcon}
													sx={{
														width: 17,
														height: 17,
														mr: "5px",
														ml: "-2px",
													}}
													style={{
														visibility:
															candidateData &&
															userData?.labels &&
															candidateData.labels.filter(
																(label) =>
																	label.label ==
																	option.label,
															).length > 0
																? "visible"
																: "hidden",
													}}
												/>
												<Box
													component="span"
													sx={{
														width: 14,
														height: 14,
														flexShrink: 0,
														borderRadius: "3px",
														mr: 1,
														mt: "2px",
													}}
													style={{
														backgroundColor:
															option.color,
													}}
												/>
												<Box
													sx={(t) => ({
														flexGrow: 1,
														"& span": {
															color: "#8b949e",
															...t.applyStyles(
																"light",
																{
																	color: "#586069",
																},
															),
														},
													})}
												>
													{option.label}
												</Box>
											</li>
										);
									}}
									renderInput={(params) => (
										<TextField {...params} />
									)}
									getOptionLabel={(option) =>
										(option as Label).label
									}
									options={userData?.labels || []}
								/>
								<TextField
									type="color"
									sx={{ minWidth: "60px" }}
									value={label.color}
									onChange={(event) => {
										setLabel((prev) => ({
											...prev,
											color: event.target.value,
										}));
									}}
								/>
							</Stack>
						) : (
							<Stack
								direction="row"
								alignItems="center"
								flexWrap="wrap"
								spacing={1.5}
								gap={1}
								sx={{ mb: 2 }}
							>
								{candidateData?.labels.map((label) => (
									<Chip
										key={label.id.toString()}
										label={label.label}
										style={{
											color: getTextColor(label.color),
											backgroundColor: label.color,
											marginBottom: 0,
											marginLeft: 0,
										}}
										onDelete={() => {
											handleLabelDelete(label.id);
										}}
									/>
								))}
							</Stack>
						)
					) : (
						<Skeleton width={210} sx={{ mb: 2 }} />
					)}
				</EditableField>

				<Divider sx={{ mb: 2 }} />

				<EditableField
					isLoading={isLoading}
					isUpdatingField={isPrivateNotesSending}
					label="Notas pessoais"
					accessLevel={{
						lock: true,
						title: "Disponível apenas para você",
					}}
					setIsEditing={setEnablePrivateNotes}
					isEditing={enablePrivateNotes}
					onApply={() => {
						if (privateNotes) handlePrivateNotesSend(privateNotes);
					}}
				>
					{!isLoading && process ? (
						<TextField
							disabled={!enablePrivateNotes}
							multiline
							rows={4}
							onChange={(event) => {
								setPrivateNotes(event.target.value);
							}}
							fullWidth
							defaultValue={candidateData?.privateNotes}
						/>
					) : (
						<Skeleton width={210} sx={{ mb: 2 }} />
					)}
				</EditableField>

				<Divider sx={{ mb: 2 }} />

				<EditableField isLoading={isLoading} label="Status">
					{!isLoading && candidateData ? (
						<SelectStats
							row={candidateData}
							callback={reloadData}
						/>
					) : (
						<Skeleton width={210} sx={{ mb: 2 }} />
					)}
				</EditableField>

				<Divider sx={{ mb: 2 }} />

				<EditableField
					isLoading={isLoading}
					label="Semestre de Entrada"
				>
					{!isLoading && candidateData ? (
						<>
							<SelectSemester
								row={candidateData}
								callback={reloadData}
							/>
							{candidateData.entrySemester !=
							semesterSubmission ? (
								<Typography
									color="textSecondary"
									variant="caption"
								>
									Semestre de entrada diferente do apresentado
									pelo candidato*
								</Typography>
							) : (
								<></>
							)}
						</>
					) : (
						<Skeleton width={210} sx={{ mb: 2 }} />
					)}
				</EditableField>

				{isAdminRole(currentUser?.role as RolesUser) &&
				candidateData?.stats == ApprovalState.Approved ? (
					<>
						<Divider sx={{ mb: 2, mt: 2 }} />
						<EditableField
							isLoading={isLoading}
							label="Enviar formulário de aceite"
						>
							{!isLoading && candidateData ? (
								<Button
									color="primary"
									variant="outlined"
									disabled={
										acceptSentStatus !=
										sentLabels[SentStatus.NOT_SENT]
									}
									loading={isSendingForms}
									onClick={(event) => {
										setModalFormsOpen(true);
									}}
								>
									Enviar
								</Button>
							) : (
								<Skeleton width={210} sx={{ mb: 2 }} />
							)}
						</EditableField>
					</>
				) : (
					<></>
				)}

				{
					//TODO: melhorar forma de verificacao
					(isAdminRole(currentUser?.role as RolesUser) &&
						acceptInfo == "Aceito a vaga.") ||
					acceptInfo == "I accept the offer." ? (
						<>
							<Divider sx={{ mb: 2, mt: 2 }} />
							<EditableField
								isLoading={isLoading}
								label="Enviar carta de aceite"
							>
								{!isLoading && candidateData ? (
									<Button
										color="primary"
										variant="outlined"
										disabled={candidateData.letterSent}
										loading={isSendingLetter}
										onClick={(event) => {
											setModalLetterOpen(true);
										}}
									>
										Enviar
									</Button>
								) : (
									<Skeleton width={210} sx={{ mb: 2 }} />
								)}
							</EditableField>
						</>
					) : (
						<></>
					)
				}
			</Box>

			<Dialog
				open={isModalFormsOpen}
				onClose={() => setModalFormsOpen(false)}
			>
				<DialogTitle>Confirmar envio de formulário</DialogTitle>
				<DialogContent>
					<Typography>
						Após o envio do formulário, esta ação será finalizada e
						não poderá ser desfeita.
					</Typography>
				</DialogContent>
				<DialogActions>
					<Button
						onClick={() => setModalFormsOpen(false)}
						color="error"
					>
						Cancelar
					</Button>
					<Button
						onClick={() => {
							setModalFormsOpen(false);
							handleSendAcceptForms();
						}}
						color="secondary"
					>
						Confirmar
					</Button>
				</DialogActions>
			</Dialog>

			<Dialog
				open={isModalLetterOpen}
				onClose={() => setModalLetterOpen(false)}
			>
				<DialogTitle>Confirmar envio de carta</DialogTitle>
				<DialogContent>
					<Typography>
						Após o envio da carta, esta ação será finalizada e não
						poderá ser desfeita.
					</Typography>
				</DialogContent>
				<DialogActions>
					<Button
						onClick={() => setModalLetterOpen(false)}
						color="error"
					>
						Cancelar
					</Button>
					<Button
						onClick={() => {
							setModalLetterOpen(false);
							handleSendAcceptLetters();
						}}
						color="secondary"
					>
						Confirmar
					</Button>
				</DialogActions>
			</Dialog>
		</>
	);
}
