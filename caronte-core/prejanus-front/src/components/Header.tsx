import AuthenticationButton from "@/components/AuthenticationButton";
import { Divider, Link, Stack, Typography } from "@mui/material";
import { Suspense } from "react";

const Header = () => {
	return (
		<nav style={{ width: "100%", zIndex: 10 }}>
			<Stack
				direction="row"
				alignItems="center"
				justifyContent="space-between"
				sx={{ width: "100%", height: "5rem", p: 3 }}
			>
				<Link href={process.env.NEXT_PUBLIC_BASE_PATH} underline="none">
					<Typography variant="h6" color="primary">
						Universidade de São Paulo
					</Typography>
				</Link>

				<Suspense fallback={<></>}>
					<AuthenticationButton />
				</Suspense>
			</Stack>

			<Divider />
		</nav>
	);
};

export default Header;
