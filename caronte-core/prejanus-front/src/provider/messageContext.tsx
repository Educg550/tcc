"use client";

import React, {
	createContext,
	useContext,
	useState,
	useCallback,
	ReactNode,
} from "react";
import { Snackbar, Alert, AlertColor } from "@mui/material";

type SnackbarContextType = {
	showSnackbar: (message: string, severity?: AlertColor) => void;
};

const SnackbarContext = createContext<SnackbarContextType | undefined>(
	undefined,
);

export const SnackbarProvider = ({ children }: { children: ReactNode }) => {
	const [snackbar, setSnackbar] = useState({
		open: false,
		message: "",
		severity: "info",
	});

	const showSnackbar = useCallback(
		(message: string, severity: AlertColor = "info") => {
			setSnackbar({ open: true, message, severity });
		},
		[],
	);

	const handleClose = () => {
		setSnackbar((prev) => ({ ...prev, open: false }));
	};

	return (
		<SnackbarContext.Provider value={{ showSnackbar }}>
			{children}
			<Snackbar
				open={snackbar.open}
				autoHideDuration={3000}
				onClose={handleClose}
				anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
			>
				<Alert
					onClose={handleClose}
					severity={snackbar.severity as AlertColor}
				>
					{snackbar.message}
				</Alert>
			</Snackbar>
		</SnackbarContext.Provider>
	);
};

export const useSnackbar = () => {
	const context = useContext(SnackbarContext);
	if (!context) {
		throw new Error("useSnackbar must be used within a SnackbarProvider");
	}
	return context;
};
