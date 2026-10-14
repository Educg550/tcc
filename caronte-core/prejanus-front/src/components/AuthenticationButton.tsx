"use client";

import SenhaunicaSignInButton from "@/components/SenhaunicaSignInButton";
import LogOutButton from "@/components/LogOutButton";
import { Stack, Typography } from "@mui/material";
import { useUser } from "@/provider/UserProvider";

export default function AuthenticationButton() {
	const { user } = useUser();

	return user === undefined ? (
		<SenhaunicaSignInButton />
	) : (
		<Stack
			direction="row"
			sx={{
				justifyContent: "center",
				alignItems: "center",
				gap: 2,
			}}
		>
			<Typography>{user.name}</Typography>
			<LogOutButton />
		</Stack>
	);
}
