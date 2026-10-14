"use client";

import { Button } from "@mui/material";
import Link from "next/link";

export default function SenhaunicaSignInButton() {
	return (
		<Button component={Link} href="/login">
			Entrar com Senhaunica
		</Button>
	);
}
