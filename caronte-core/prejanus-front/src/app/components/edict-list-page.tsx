"use client";

import {
	Box,
	Button,
	CircularProgress,
	Stack,
	Tab,
	Tabs,
	Typography,
} from "@mui/material";
import EdictList from "@/app/components/edict-list";
import useEdict from "@/app/hooks/useEdict";
import { TEdict } from "@/app/model/edict";
import { useEffect, useState } from "react";
import { useSnackbar } from "@/provider/messageContext";

const ITEMS_PER_PAGE = 5;

type Props = {
	isLoading: boolean;
	isError: boolean;
	filteredEdicts?: TEdict[];
	currentItems?: TEdict[];
	isAllProgramsOpen: boolean;
	page: number;
	handlePageChange: (
		event: React.ChangeEvent<unknown>,
		value: number,
	) => void | undefined;
	handleClickEdict: (id: number) => void;
};

export default function EdictsListPage() {
	const [value, setValue] = useState(0);

	const handleChange = (event: React.SyntheticEvent, newValue: number) => {
		setValue(newValue);
	};

	const { showSnackbar } = useSnackbar();

	const {
		currentItems,
		filteredEdicts,
		isAllProgramsOpen,
		page,
		isError,
		isLoading,
		setIsAllProgramsOpen,
		handlePageChange,
		handleClickEdict,
		handleCreateEdictClick,
	} = useEdict({ itemsPerPage: ITEMS_PER_PAGE });

	useEffect(() => {
		if (isError) {
			showSnackbar("Ocorreu um erro ao carregar os editais", "error");
		}
	}, [isError, showSnackbar]);

	return (
		<>
			<Typography gutterBottom variant="h4">
				Editais
			</Typography>
			<Box sx={{ width: "100%" }}>
				<Stack
					direction="row"
					sx={{
						justifyContent: "space-between",
						alignItems: "center",
					}}
				>
					<Tabs
						sx={{ borderBottom: 1, borderColor: "divider" }}
						value={value}
						onChange={handleChange}
					>
						<Tab
							label="Todos"
							onClick={() => setIsAllProgramsOpen(true)}
						/>
						<Tab
							label="Abertos"
							onClick={() => setIsAllProgramsOpen(false)}
						/>
					</Tabs>
					<Button
						onClick={handleCreateEdictClick}
						variant="contained"
					>
						Criar edital
					</Button>
				</Stack>
			</Box>

			{renderContent({
				isLoading,
				isError,
				filteredEdicts,
				isAllProgramsOpen,
				currentItems,
				handlePageChange,
				handleClickEdict,
				page,
			})}
		</>
	);
}

const renderContent = ({
	isLoading,
	isError,
	filteredEdicts,
	isAllProgramsOpen,
	currentItems,
	page,
	handlePageChange,
	handleClickEdict,
}: Props) => {
	if (isLoading)
		return (
			<Box
				sx={{
					display: "flex",
					justifyContent: "center",
					alignItems: "center",
					width: "100%",
					height: "100%",
				}}
			>
				<CircularProgress />
			</Box>
		);

	if (filteredEdicts && filteredEdicts.length)
		return (
			<EdictList
				filteredEdicts={currentItems}
				handlePageChange={handlePageChange}
				itemsPerPage={ITEMS_PER_PAGE}
				page={page}
				edictsCount={filteredEdicts.length}
				handleClickEdict={handleClickEdict}
			/>
		);

	return (
		<Stack
			direction="row"
			justifyContent="center"
			alignItems="center"
			sx={{
				textAlign: "center",
				width: "100%",
				height: "100%",
			}}
			spacing={2}
		>
			<Typography color="textSecondary">
				Nenhum edital encontrado!
			</Typography>
		</Stack>
	);
};
