import { CommentType } from "@/app/submissions/[submissionId]/api/dto/applicant-dto";
import {
	Avatar,
	Box,
	hslToRgb,
	IconButton,
	Paper,
	Stack,
	Tooltip,
	Typography,
} from "@mui/material";
import Comment from "@/app/model/comment";
import User from "@/app/model/user";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { getTextColor, stringToColor } from "../utils/utils";
import useSWR from "swr";
import useComments from "@/app/hooks/useComments";

export enum ActivityViewerOptionsEnum {
	ALL_ACTIVITIES = "ALL_ACTIVITIES",
	INTERNAL_COMMENTS_ONLY = "INTERNAL_COMMENTS_ONLY",
	HISTORY_ONLY = "HISTORY_ONLY",
}

interface Props {
	submissionId: string;
	currentUser?: User;
	activityViewerOption: ActivityViewerOptionsEnum;
}

export default function ActivitiesViewer({
	submissionId,
	currentUser,
	activityViewerOption,
}: Props) {
	const historyOnly =
		activityViewerOption === ActivityViewerOptionsEnum.HISTORY_ONLY ||
		activityViewerOption === ActivityViewerOptionsEnum.ALL_ACTIVITIES;
	const commentsOnly =
		activityViewerOption ===
			ActivityViewerOptionsEnum.INTERNAL_COMMENTS_ONLY ||
		activityViewerOption === ActivityViewerOptionsEnum.ALL_ACTIVITIES;
	const { deleteComment, comments, error, isLoading, mutate } =
		useComments(submissionId);

	return (
		<Box sx={{ position: "relative", ml: 3 }}>
			<Box
				sx={{
					position: "absolute",
					top: 0,
					left: 8,
					width: "2px",
					height: "100%",
					bgcolor: "text.disabled",
				}}
			/>
			<Stack spacing={4}>
				{!isLoading &&
					comments.map((comment, index) => {
						if (
							comment.type === CommentType.Comment ||
							comment.type === CommentType.ExternalComment
						) {
							if (
								comment.type === CommentType.ExternalComment &&
								!historyOnly
							)
								return;
							if (
								comment.type === CommentType.Comment &&
								!commentsOnly
							)
								return;

							const { color: bgColor } = stringToColor(
								comment.user.name,
							);
							const fontColor = getTextColor(hslToRgb(bgColor));
							return (
								<Box
									key={comment.text + comment.user.id + index}
									sx={{
										position: "relative",
										pl: 6,
									}}
								>
									<Box
										sx={{
											position: "absolute",
											top: "6px",
											left: "5px",
											width: 8,
											height: 8,
											bgcolor: "secondary.main",
											borderRadius: "50%",
											border: "2px solid white",
										}}
									/>
									<Paper
										elevation={1}
										variant="outlined"
										sx={{
											px: 2,
											py: 1,
										}}
									>
										<Stack
											alignItems={"center"}
											justifyContent={"space-between"}
											direction="row"
										>
											<Stack
												sx={{
													mb: 1,
												}}
												alignItems={"center"}
												direction={"row"}
												flexWrap={"wrap"}
												columnGap={2}
												rowGap={1}
											>
												<Stack
													direction="row"
													alignItems={"center"}
												>
													<Avatar
														key={index}
														alt={comment.user.name}
														sx={{
															width: 21,
															height: 21,
															fontSize: 11,
															mr: 1,
															bgcolor: bgColor,
															color: fontColor,
														}}
														title={
															comment.user.name
														}
													>
														{comment.user.name[0].toUpperCase()}
													</Avatar>
													<Typography
														variant="body2"
														color="text.primary"
													>
														{comment.user.name}
													</Typography>
												</Stack>
												<Typography
													variant="body2"
													color="text.secondary"
												>
													{comment.postedWhen}
												</Typography>
												{comment.type ===
												CommentType.ExternalComment ? (
													<Tooltip title="Comentário externo">
														<OpenInNewIcon
															fontSize="small"
															sx={{
																color: "text.secondary",
															}}
														/>
													</Tooltip>
												) : (
													<></>
												)}
											</Stack>

											{comment.user.id ===
												currentUser?.id && (
												<IconButton
													onClick={(_) => {
														deleteComment(
															comment.id,
														);
													}}
													size="small"
												>
													<DeleteOutlineIcon />
												</IconButton>
											)}
										</Stack>

										<Typography
											variant="body2"
											sx={{
												whiteSpace: "normal",
												wordBreak: "break-word",
											}}
										>
											{comment.text}
										</Typography>
									</Paper>
								</Box>
							);
						} else if (
							(comment.type === CommentType.Favorite ||
								comment.type === CommentType.Interest) &&
							historyOnly
						) {
							return (
								<Box
									key={comment.text + comment.user.id + index}
									sx={{
										position: "relative",
										pl: 6,
									}}
								>
									<Box
										sx={{
											position: "absolute",
											top: "6px",
											left: "5px",
											width: 8,
											height: 8,
											bgcolor: "secondary.main",
											borderRadius: "50%",
											border: "2px solid white",
										}}
									/>

									<Typography
										variant="body2"
										color="textSecondary"
										sx={{
											whiteSpace: "normal",
											wordBreak: "break-word",
										}}
									>
										{comment.text}
									</Typography>
								</Box>
							);
						} else if (
							comment.type === CommentType.Advisor &&
							historyOnly
						) {
							return (
								<Box
									key={comment.text + comment.user.id + index}
									sx={{
										position: "relative",
										pl: 6,
									}}
								>
									<Box
										sx={{
											position: "absolute",
											top: "1px",
											left: "1px",
											width: 16,
											height: 16,
											bgcolor: "secondary.main",
											borderRadius: "50%",
											border: "2px solid white",
										}}
									/>

									<Typography
										variant="body2"
										color="textSecondary"
										sx={{
											whiteSpace: "normal",
											wordBreak: "break-word",
										}}
									>
										{comment.text}
									</Typography>
								</Box>
							);
						} else if (
							comment.type === CommentType.Custom &&
							historyOnly
						) {
							return (
								<Box
									key={comment.text + comment.user.id + index}
									sx={{
										position: "relative",
										pl: 6,
									}}
								>
									<Box
										sx={{
											position: "absolute",
											top: "6px",
											left: "5px",
											width: 8,
											height: 8,
											bgcolor: "secondary.main",
											borderRadius: "50%",
											border: "2px solid white",
										}}
									/>

									<Typography
										variant="body2"
										color="textSecondary"
										sx={{
											whiteSpace: "normal",
											wordBreak: "break-word",
										}}
									>
										{comment.text} {comment.postedWhen}
									</Typography>
								</Box>
							);
						}
					})}
			</Stack>
		</Box>
	);
}
