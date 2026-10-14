import { Stack } from "@mui/material";

export default function Layout({ children }: { children: React.ReactNode }) {
	return (
		<Stack
			direction="column"
			justifyContent="center"
			alignItems="center"
			sx={{
				flex: 1,
				width: "100%",
				height: "100%",
			}}
			spacing={2}
		>
			{children}
		</Stack>
	);
}
