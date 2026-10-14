"use client";

import { createTheme } from "@mui/material/styles";

const theme = createTheme({
	palette: {
		primary: {
			main: "#1E1E1E",
		},
		secondary: {
			main: "#4A789C",
		},
		error: {
			main: "#ff3333",
		},
	},
	typography: {
		fontFamily: "var(--font-roboto)",
		button: {
			textTransform: "none",
		},
	},
});

export default theme;
