import { useState } from "react";
import { TProcess } from "../models/process";
import {
	Button,
	Typography,
	Box,
	Stack,
	Chip,
	Menu,
	MenuItem,
	Tabs,
	Tab,
	Dialog,
	DialogTitle,
	DialogContent,
	DialogActions,
	Skeleton,
	IconButton,
	ListItemIcon,
	ListItemText,
	Divider,
} from "@mui/material";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { useRouter } from "next/navigation";
import CloseIcon from "@mui/icons-material/Close";
import SettingsIcon from "@mui/icons-material/Settings";
import ViewSidebarIcon from "@mui/icons-material/ViewSidebar";
import { useSnackbar } from "@/provider/messageContext";
import { UpdateViewOptionFn, ViewOptions } from "../models/viewOptions";
import Phases from "../models/phases";
import { ApprovalState } from "@/app/model/application-candidate";
import { approvalLabels } from "../mappers/applicant";
import { LabelPhase } from "../mappers/phases";

interface ProcessInfoProps {
	process?: TProcess;
	mutate: () => void;
	onToggleFavoritesOnly: (_: boolean) => void;
	setStatsTab: (tab?: ApprovalState) => void;
	isLoading?: boolean;
	viewOption: ViewOptions;
	updateViewOption: UpdateViewOptionFn;
}

export default function ProcessInfo({
	process: edict,
	mutate,
	onToggleFavoritesOnly,
	viewOption,
	updateViewOption,
	setStatsTab,
	isLoading,
}: ProcessInfoProps) {
	const { showSnackbar } = useSnackbar();
	const router = useRouter();
	const [isModalOpen, setModalOpen] = useState(false);

	const handleCloseEdict = async () => {
		if (!edict?.processId) return;

		try {
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_BASE_PATH}/${edict.processId}/api/close`,
				{
					method: "POST",
				},
			);

			if (!response.ok) {
				const errorData = await response.json();
				if ("message" in errorData) {
					showSnackbar(`${errorData.message}`, "error");
				}
				return;
			}

			showSnackbar(`Edital fechado!`, "success");
			setModalOpen(false);
			router.push(`/${edict.processId}`);
		} catch (error) {
			showSnackbar(
				`Erro: ${error instanceof Error ? error.message : "Erro desconhecido"}`,
				"error",
			);
			setModalOpen(false);
		}
	};

	const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
	const open = Boolean(anchorEl);
	const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
		setAnchorEl(event.currentTarget);
	};
	const handleClose = () => {
		setAnchorEl(null);
	};

	const [value, setValue] = useState(0);

	const handleChange = (event: React.SyntheticEvent, newValue: number) => {
		setValue(newValue);
	};

	return (
		<>
			<Typography gutterBottom variant="h4">
				{isLoading ? (
					<Skeleton width={210} />
				) : edict == undefined || edict.title == undefined ? (
					`Edital inválido`
				) : (
					`${edict?.title} - ${edict?.year}.${edict?.semester}`
				)}
				{isLoading ? (
					<Skeleton width={50} />
				) : (
					<Stack
						direction="row"
						sx={{ alignItems: "center", gap: 1 }}
					>
						<Chip
							color={edict?.is_open ? "success" : "primary"}
							label={edict?.is_open ? "Aberto" : "Concluído"}
						/>
						{edict?.phase != undefined ? (
							<Chip label={LabelPhase(edict?.phase as Phases)} />
						) : (
							<></>
						)}
					</Stack>
				)}
			</Typography>
			<Typography gutterBottom>
				{isLoading ? <Skeleton width={210} /> : edict?.description}
			</Typography>
			<Box sx={{ width: "100%" }}>
				<Stack
					direction="row"
					sx={{
						justifyContent: "space-between",
						alignItems: "center",
					}}
				>
					<Tabs
						sx={{ borderBottom: 1, borderColor: "divider" }}
						value={value}
						onChange={handleChange}
					>
						<Tab
							key="tab-todos"
							label="Todos"
							className="tutorialDriver--tab__all"
							onClick={() => {
								onToggleFavoritesOnly(false);
								setStatsTab();
							}}
						/>
						{edict
							? (() => {
									const tabs = [];
									if (edict.phase === Phases.encerrado) {
										tabs.push([
											<Tab
												key={`tab-${ApprovalState.Approved}`}
												label={
													approvalLabels[
														ApprovalState.Approved
													]
												}
												onClick={() =>
													setStatsTab(
														ApprovalState.Approved,
													)
												}
											/>,
											<Tab
												key={`tab-${ApprovalState.Refused}`}
												label={
													approvalLabels[
														ApprovalState.Refused
													]
												}
												onClick={() =>
													setStatsTab(
														ApprovalState.Refused,
													)
												}
											/>,
											<Tab
												key={`tab-${ApprovalState.UnderReview}`}
												label={
													approvalLabels[
														ApprovalState
															.UnderReview
													]
												}
												onClick={() =>
													setStatsTab(
														ApprovalState.UnderReview,
													)
												}
											/>,
											<Tab
												key={`tab-${ApprovalState.Waitlist}`}
												label={
													approvalLabels[
														ApprovalState.Waitlist
													]
												}
												onClick={() =>
													setStatsTab(
														ApprovalState.Waitlist,
													)
												}
											/>,
										]);
									} else if (
										edict.phase === Phases.avaliacao
									) {
										tabs.push([
											<Tab
												key="tab-favoritos"
												label="Favoritos"
												onClick={() =>
													onToggleFavoritesOnly(true)
												}
											/>,
										]);
									}
									return tabs;
								})()
							: []}
					</Tabs>
					<Stack
						direction="row"
						sx={{ alignItems: "center", gap: 1 }}
					>
						<IconButton
							className="tutorialDriver--verticon__button"
							onClick={handleClick}
						>
							<MoreVertIcon />
						</IconButton>
						<Menu
							className="tutorialDriver--verticon"
							anchorEl={anchorEl}
							open={open}
							onClose={handleClose}
							anchorOrigin={{
								vertical: "bottom",
								horizontal: "right",
							}}
							transformOrigin={{
								vertical: "top",
								horizontal: "right",
							}}
						>
							{/* <MenuItem
								onClick={() => {
									edict?.is_open && setModalOpen(true);
									handleClose();
								}}
							>
								{edict?.is_open ? (
									<>
										<ListItemIcon>
											<CloseIcon fontSize="small" />
										</ListItemIcon>
										<ListItemText>
											Fechar edital
										</ListItemText>
									</>
								) : (
									"Reabrir edital"
								)}
							</MenuItem> */}
							<MenuItem
								disabled={!edict?.processId}
								onClick={() => {
									router.push(`${edict?.processId}/edit`);
									handleClose();
								}}
							>
								<ListItemIcon>
									<SettingsIcon fontSize="small" />
								</ListItemIcon>
								<ListItemText>
									Configurações edital
								</ListItemText>
							</MenuItem>
							<Divider />
							<MenuItem
								onClick={() => {
									handleClose();
									updateViewOption(
										"collapsedSidebar",
										!viewOption.collapsedSidebar,
									);
								}}
							>
								<ListItemIcon>
									<ViewSidebarIcon fontSize="small" />
								</ListItemIcon>
								<ListItemText>
									{viewOption.collapsedSidebar
										? "Mostrar barra lateral"
										: "Esconder barra lateral"}
								</ListItemText>
							</MenuItem>
						</Menu>
					</Stack>
				</Stack>
			</Box>

			<Dialog open={isModalOpen} onClose={() => setModalOpen(false)}>
				<DialogTitle>Confirmar Fechamento</DialogTitle>
				<DialogContent>
					Tem certeza de que deseja fechar o edital {edict?.title}?
					Essa ação não pode ser desfeita.
				</DialogContent>
				<DialogActions>
					<Button
						onClick={() => setModalOpen(false)}
						color="secondary"
					>
						Cancelar
					</Button>
					<Button onClick={handleCloseEdict} color="primary">
						Confirmar
					</Button>
				</DialogActions>
			</Dialog>
		</>
	);
}
