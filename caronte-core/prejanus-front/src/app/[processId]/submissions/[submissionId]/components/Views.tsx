import useSWR from "swr";
import { SubmissionView } from "../../../models/submissionView";
import { Typography, List, ListItem, ListItemText } from "@mui/material";
import { getDaysFromDate } from "../../../../submissions/[submissionId]/api/utils";
import { useUser } from "../../../../../provider/UserProvider";

export default function Views({ submissionId }: { submissionId: string }) {
	const { data: views = [], isLoading } = useSWR<SubmissionView[]>(
		`/submissions/${submissionId}/api/view`
	);

	const { user } = useUser();

	if (isLoading) {
		return <Typography variant="body2">Carregando...</Typography>;
	}

	if (views.length === 0) {
		return <Typography variant="body2">Nenhuma visualização ainda</Typography>;
	}

	return (
		<List sx={{ width: "100%", maxWidth: 480 }}>
			{views.map((view) => {
				const isYou = view.user_id === user?.id;

				return (
					<ListItem
						key={view.id}
						divider
						sx={{
							borderRadius: 2,
							mb: 1,
							backgroundColor: "background.paper",
						}}
					>
						<ListItemText
							primary={
								<Typography variant="subtitle2" fontWeight={500}>
									{isYou ? "Você" : view.user?.name}
									{" "}
									visualizou
								</Typography>
							}
							secondary={
								<Typography variant="caption" color="text.secondary">
									{getDaysFromDate(view.created_at)}
								</Typography>
							}
						/>
					</ListItem>
				);
			})}
		</List>
	);
}
