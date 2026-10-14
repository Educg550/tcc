import InfoField from "@/app/shared/model/info-field";
import { Box, Chip, Divider, Stack, Typography } from "@mui/material";
import React from "react";
import ReactMarkdown from "react-markdown";

interface Props {
	info?: InfoField[][];
	loading: boolean;
}

export default function CandidateRecommendersInfo({ info, loading }: Props) {
	if (loading) return <></>;

	return (
		<Box px={4}>
			{info?.map((recommenderInfo, index) => {
				const infoArray = [...recommenderInfo];
				const name = infoArray.shift();
				const sent = infoArray.shift();
				return (
					<React.Fragment key={index}>
						{name ? (
							<Stack
								key={name.label}
								gap={2}
								direction="row"
								alignItems={"center"}
							>
								<Typography
									variant="h6"
									sx={{
										flex: 1,
									}}
								>
									{index + 1}. {name.value}
								</Typography>
								{sent?.value.toLowerCase() == "true" ? (
									<Chip label={"Enviado"} />
								) : (
									<Chip label={"Não Respondido"} />
								)}
							</Stack>
						) : (
							""
						)}
						{infoArray.map((info, index) => (
							<Box key={info.label}>
								<Stack
									direction="column"
									spacing={2}
									alignItems="start"
									py={2}
								>
									<Typography
										color="text.secondary"
										variant="body2"
									>
										{info.label}
									</Typography>
									<Typography
										variant="caption"
										sx={{
											flex: 1,
											wordWrap: "break-word",
											overflowWrap: "anywhere",
										}}
									>
										<ReactMarkdown
											components={{
												pre: ({ node, ...props }) => (
													<pre
														style={{
															whiteSpace:
																"pre-wrap",
															wordWrap:
																"break-word",
														}}
														{...props}
													/>
												),
											}}
										>
											{info.value.replaceAll(
												"\\n",
												"\n\n",
											)}
										</ReactMarkdown>
									</Typography>
								</Stack>
								{index < infoArray.length - 1 && <Divider />}
							</Box>
						))}
					</React.Fragment>
				);
			})}
		</Box>
	);
}
