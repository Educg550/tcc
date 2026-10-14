import InfoField from "@/app/shared/model/info-field";
import { Box, Divider, Stack, Typography } from "@mui/material";
import ReactMarkdown from "react-markdown";

interface Props {
	info?: InfoField[];
	loading: boolean;
}

export default function CandidatePersonalInfo({ info, loading }: Props) {
	if (loading) return <></>;

	return (
		<Box px={4}>
			{info?.map((item, index) => (
				<Box key={item.label}>
					<Stack
						direction="column"
						spacing={2}
						alignItems="start"
						py={2}
					>
						<Typography color="text.secondary" variant="body2">
							{item.label}
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
												whiteSpace: "pre-wrap",
												wordWrap: "break-word",
											}}
											{...props}
										/>
									),
								}}
							>
								{item.value.replaceAll("\\n", "\n\n")}
							</ReactMarkdown>
						</Typography>
					</Stack>
					{index < (info?.length ?? 0) - 1 && <Divider />}
				</Box>
			))}
		</Box>
	);
}
