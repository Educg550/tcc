"use client";

import clearSession from "@/app/shared/session/clearSession";
import { useUser } from "@/provider/UserProvider";
import { Button } from "@mui/material";
import { useCallback } from "react";

export default function LogOutButton() {
	const { setUser } = useUser();

	const handleClick = useCallback(() => {
		clearSession();
		setUser(undefined);
	}, [setUser]);

	return (
		<Button onClick={handleClick} variant="outlined" color="error">
			Sair
		</Button>
	);
}
