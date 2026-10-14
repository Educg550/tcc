import { ShieldOutlined } from "@mui/icons-material";
import { Stack, Typography } from "@mui/material";

export default async function LandingPage() {
	return (
		<>
			<Stack
				direction="column"
				justifyContent="center"
				alignItems="center"
				spacing={4}
				sx={{
					height: "1",
					width: "1",
				}}
			>
				<ShieldOutlined style={{ width: "5em", height: "5em" }} />

				<Typography>
					Conteúdo restrito. Autentique-se utilizando sua conta da
					USP.
				</Typography>
			</Stack>
		</>
	);
}
