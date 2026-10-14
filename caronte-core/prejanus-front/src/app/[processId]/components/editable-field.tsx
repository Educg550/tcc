import { Box, Button, Stack, Tooltip, Typography } from "@mui/material";
import LockOpenIcon from "@mui/icons-material/LockOpen";
import LockIcon from "@mui/icons-material/Lock";
import React, { Dispatch, SetStateAction } from "react";
import { ReactNode } from "react";

interface Props {
	isLoading: boolean;
	isUpdatingField?: boolean;
	label: string;
	children: ReactNode;
	onApply?: () => void;
	isEditing?: boolean;
	setIsEditing?: Dispatch<SetStateAction<boolean>>;
	accessLevel?: { lock: boolean; title: string };
}

export default function EditableField({
	isLoading,
	label,
	isUpdatingField,
	children,
	onApply,
	isEditing,
	setIsEditing,
	accessLevel,
}: Props) {
	const handleClick = () => {
		if (isEditing) {
			if (onApply) onApply();
		}
		if (setIsEditing) setIsEditing(!isEditing);
	};

	return (
		<>
			<Stack
				direction="row"
				alignItems="center"
				justifyContent="space-between"
				sx={{ mb: 2 }}
			>
				<Typography
					variant="body1"
					sx={{ fontWeight: "bold" }}
					display={"flex"}
					alignItems={"center"}
					gap={1}
				>
					{label}
					{accessLevel ? (
						<Tooltip
							title={
								<Typography color="inherit">
									{accessLevel.title}
								</Typography>
							}
						>
							{accessLevel.lock ? (
								<LockIcon color="action" fontSize="small" />
							) : (
								<LockOpenIcon color="action" fontSize="small" />
							)}
						</Tooltip>
					) : (
						<></>
					)}
				</Typography>
				{!!setIsEditing ? (
					<Button
						disabled={isLoading}
						variant="text"
						loading={isUpdatingField}
						onClick={handleClick}
					>
						{isEditing ? "Aplicar" : "Editar"}
					</Button>
				) : (
					<></>
				)}
			</Stack>
			<Box>{children}</Box>
		</>
	);
}
