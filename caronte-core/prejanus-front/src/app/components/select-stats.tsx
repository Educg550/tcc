import React, { useEffect, useMemo, useState } from "react";
import {
	Avatar,
	Button,
	Chip,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	hslToRgb,
	List,
	ListItem,
	ListItemAvatar,
	ListItemButton,
	ListItemText,
	MenuItem,
	Select,
	SelectChangeEvent,
	Typography,
} from "@mui/material";
import { useSnackbar } from "@/provider/messageContext";

import {
	ApprovalState,
	BiddingState,
	BiddingUser,
} from "../model/application-candidate";
import getCandidateSelectStats from "../[processId]/utils/getCandidateSelectStats";
import {
	approvalLabels,
	biddingLabels,
} from "../[processId]/mappers/applicant";
import { GridStateColDef } from "@mui/x-data-grid/internals";
import User, { isAdminRole, RolesUser } from "../model/user";
import { useUser } from "@/provider/UserProvider";
import {
	getTextColor,
	stringToColor,
} from "../[processId]/submissions/[submissionId]/utils/utils";

export default function SelectStats(
	params: { cell?: any; table?: any; row?: any; colDef?: GridStateColDef } & {
		callback?: () => void;
	},
) {
	const callback = params.callback;
	const applicant = params.row.original ? params.row.original : params.row;

	const { showSnackbar } = useSnackbar();
	const [approvalState, setApprovalState] = useState<ApprovalState>(
		applicant.stats.toLowerCase(),
	);
	useEffect(() => {
		setApprovalState(applicant.stats.toLowerCase());
	}, [applicant]);
	const [open, setOpen] = useState(false);
	const [isLoading, setLoading] = useState(false);

	const { user } = useUser();

	function submissionStatsDefault(
		supervisorIds: number[],
		value: ApprovalState,
	) {
		const select = getCandidateSelectStats(
			applicant.id,
			value ?? ApprovalState.UnderReview,
			supervisorIds,
		);
		select()
			.then(async (res) => {
				if (res.ok && res.status === 200) {
					setApprovalState(value ?? ApprovalState.UnderReview);
				} else if (res.status === 400) {
					showSnackbar(
						"A submissão precisar ter pelo menos um orientador interessado!",
						"warning",
					);
				} else if (res.status === 409) {
					showSnackbar(
						"O edital está encerrado, não é mais possivel fazer alterações nas aprovações.",
						"warning",
					);
				} else {
					const errorData = await res.json();
					showSnackbar(
						`Houve um erro na aprovação da submissão: ${errorData.message || errorData.detail}`,
						"error",
					);
				}

				handleClose();
			})
			.catch(() => {
				handleClose();
			});
	}

	function submissionsStatsHandler(event: SelectChangeEvent) {
		setLoading(true);
		if (event.target.value === ApprovalState.Approved) {
			setOpen(true);
			return;
		}

		submissionStatsDefault([], event.target.value as ApprovalState);
	}

	const handleClose = () => {
		setOpen(false);
		setLoading(false);
		if (callback) callback();
	};

	const biddings = useMemo(() => {
		const biddingsObject: Record<string, BiddingUser[]> = {};

		if (!applicant.biddingUsers) return biddingsObject;

		Object.keys(applicant.biddingUsers).forEach((key: string) => {
			if (key != BiddingState.DECLINE) {
				if (
					!biddingsObject.hasOwnProperty(key) &&
					key != "" &&
					applicant.biddingUsers[key].length > 0
				)
					biddingsObject[key] = [];
				applicant.biddingUsers[key].forEach((user: BiddingUser) => {
					if (biddingsObject[key]) biddingsObject[key].push(user);
				});
			}
		});
		return biddingsObject;
	}, [applicant.biddingUsers]);

	return (
		<>
			<Select
				value={approvalState}
				size="small"
				onClick={(e) => e.stopPropagation()}
				onChange={submissionsStatsHandler}
				defaultValue={ApprovalState.UnderReview}
				fullWidth
				disabled={isLoading || !isAdminRole(user?.role as RolesUser)}
			>
				{params.cell
					? params.cell.getValue()?.map((option: ApprovalState) => (
							<MenuItem
								key={`menuitem--${option}`}
								value={option as ApprovalState}
							>
								{approvalLabels[option as ApprovalState]}
							</MenuItem>
						))
					: [
							<MenuItem
								key={`menuitem--${ApprovalState.Approved}`}
								value={ApprovalState.Approved}
							>
								{approvalLabels[ApprovalState.Approved]}
							</MenuItem>,
							<MenuItem
								key={`menuitem--${ApprovalState.Waitlist}`}
								value={ApprovalState.Waitlist}
							>
								{approvalLabels[ApprovalState.Waitlist]}
							</MenuItem>,
							<MenuItem
								key={`menuitem--${ApprovalState.Refused}`}
								value={ApprovalState.Refused}
							>
								{approvalLabels[ApprovalState.Refused]}
							</MenuItem>,
							<MenuItem
								key={`menuitem--${ApprovalState.UnderReview}`}
								value={ApprovalState.UnderReview}
							>
								{approvalLabels[ApprovalState.UnderReview]}
							</MenuItem>,
						]}
			</Select>
			<Dialog open={open} onClose={handleClose}>
				<DialogTitle>Confirmação</DialogTitle>
				<DialogContent>
					<List sx={{ pt: 0 }}>
						{biddings ? (
							Object.keys(biddings).map((key: string) => {
								return (
									<React.Fragment key={key}>
										<ListItemText>
											<Typography variant="subtitle2">
												{
													biddingLabels[
														key as BiddingState
													]
												}
											</Typography>
										</ListItemText>
										<List component="div" disablePadding>
											{biddings[key].map(
												(user: BiddingUser) => {
													const { color: bgColor } =
														stringToColor(
															user.name,
														);
													const fontColor =
														getTextColor(
															hslToRgb(bgColor),
														);
													return (
														<ListItem
															disablePadding
															key={user.id}
														>
															<ListItemButton
																onClick={() =>
																	submissionStatsDefault(
																		[
																			user.id,
																		],
																		ApprovalState.Approved,
																	)
																}
															>
																<ListItemAvatar>
																	<Avatar
																		alt={
																			user.name
																		}
																		sx={{
																			width: 24,
																			height: 24,
																			bgcolor:
																				bgColor,
																			color: fontColor,
																		}}
																		title={
																			user.name
																		}
																	>
																		{user.name[0].toUpperCase()}
																	</Avatar>
																</ListItemAvatar>
																<ListItemText>
																	<Typography variant="body2">
																		{
																			user.name
																		}{" "}
																	</Typography>
																	<Typography
																		variant="body2"
																		color="textSecondary"
																	>
																		{(() => {
																			if (
																				!user.slots
																			)
																				return "Quantidade de vagas restantes: 0";
																			return `Quantidade de vagas restantes: ${user.slots}`;
																		})()}
																	</Typography>
																</ListItemText>
															</ListItemButton>
														</ListItem>
													);
												},
											)}
										</List>
									</React.Fragment>
								);
							})
						) : (
							<></>
						)}
					</List>
				</DialogContent>
				<DialogActions>
					<Button onClick={handleClose}>Fechar</Button>
				</DialogActions>
			</Dialog>
		</>
	);
}
