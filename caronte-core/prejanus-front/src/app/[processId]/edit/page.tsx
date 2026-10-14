"use client";

import {
	Box,
	Button,
	FormControl,
	MenuItem,
	Select,
	SelectChangeEvent,
	Stack,
	TextField as MUITextField,
	Typography,
} from "@mui/material";
import { DatePicker, LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs, { Dayjs } from "dayjs";
import { useEffect, useState } from "react";
import useProcess from "../hooks/useProcess";
import { useParams, useRouter } from "next/navigation";
import { useSnackbar } from "@/provider/messageContext";
import MappingHistory from "../components/MappingHistory";
import Phases from "../models/phases";
import { useMappings } from "../../hooks/useMappings";

export default function EditProcess() {
	const router = useRouter();
	const { processId } = useParams<{ processId: string }>();
	const { showSnackbar } = useSnackbar();

	const {
		data: processDate,
		error: errorProcess,
		isLoading: isLoadingProcess,
		removeEdict,
	} = useProcess({
		processId,
	});

	const { mappings: candidateMapping } = useMappings(processId, "candidate");

	const { mappings: recommenderMapping } = useMappings(
		processId,
		"recommender",
	);

	useEffect(() => {
		if (errorProcess) {
			showSnackbar("Ocorreu um erro ao carregar o edital", "error");
		}
	}, [errorProcess, showSnackbar]);

	const [formData, setFormData] = useState({
		title: "",
		description: "",
		year: "",
		semester: "",
		edict_type: "",
		date_application: null as Dayjs | null,
		date_verification: null as Dayjs | null,
		date_evaluation: null as Dayjs | null,
		date_closed: null as Dayjs | null,
	});

	const [years, setYears] = useState<number[]>([]);
	useEffect(() => {
		const currentYear = new Date().getFullYear();
		setYears(Array.from({ length: 6 }, (_, i) => currentYear + i));
	}, []);

	useEffect(() => {
		if (isLoadingProcess || !processDate) return;

		setFormData((prevData) => ({
			...prevData,
			title: processDate.title,
			description: processDate.description,
			year: String(processDate.year),
			semester: String(processDate.semester),
			edict_type: processDate.type,
			date_application: dayjs(
				processDate.phases[Phases.inscricoes].closed_date,
			),
			date_evaluation: dayjs(
				processDate.phases[Phases.homologacao].closed_date,
			),
			date_verification: dayjs(
				processDate.phases[Phases.avaliacao].closed_date,
			),
			date_closed: dayjs(
				processDate.phases[Phases.encerrado].closed_date,
			),
		}));
	}, [processDate, isLoadingProcess]);

	type ChangeEvents =
		| React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
		| SelectChangeEvent<string>;

	const handleChange =
		(field: string) => (event: ChangeEvents | Dayjs | null) => {
			const value =
				field.startsWith("date") || field.endsWith("date")
					? event
					: (event as ChangeEvents).target.value;
			setFormData((prevData) => ({
				...prevData,
				[field]: value,
			}));
		};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		try {
			const response = await fetch("edit/api", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(formData),
			});

			if (!response.ok) {
				const errorData = await response.json();
				if ("message" in errorData) {
					showSnackbar(`${errorData.message}`, "error");
				} else {
					showSnackbar(
						`Erro: ${errorData.error?.detail[0].input + " " + errorData.error?.detail[0].msg || "Erro ao editar o edital"}`,
						"error",
					);
				}
				return;
			}

			showSnackbar(`Edital editado com sucesso!`, "success");
			router.push(`/${processId}`);
		} catch (error) {
			showSnackbar(
				`Erro: ${error instanceof Error ? error.message : "Erro desconhecido"}`,
				"error",
			);
		}
	};

	return (
		<Box style={{ maxWidth: "900px", margin: "0 auto" }}>
			<Typography sx={{ m: 4 }}>Edições básicas</Typography>
			<LocalizationProvider dateAdapter={AdapterDayjs}>
				<Box component="form" onSubmit={handleSubmit}>
					<Stack spacing={3}>
						<MUITextField
							label="Título"
							fullWidth
							value={formData.title}
							onChange={handleChange("title")}
							required
						/>

						<MUITextField
							label="Descrição"
							fullWidth
							value={formData.description}
							onChange={handleChange("description")}
							multiline
							rows={4}
							required
						/>
						<FormControl fullWidth>
							<Typography
								variant="body2"
								color="primary"
								sx={{ mb: "6px" }}
							>
								Ano *
							</Typography>
							<Select
								labelId="year-label"
								value={formData.year}
								onChange={handleChange("year")}
								required
							>
								{years.map((year) => (
									<MenuItem key={year} value={year}>
										{year}
									</MenuItem>
								))}
							</Select>
						</FormControl>
						<FormControl fullWidth>
							<Typography
								variant="body2"
								color="primary"
								sx={{ mb: "6px" }}
							>
								Semestre *
							</Typography>
							<Select
								labelId="semester-label"
								value={formData.semester}
								onChange={handleChange("semester")}
								required
							>
								<MenuItem value="1">1</MenuItem>
								<MenuItem value="2">2</MenuItem>
							</Select>
						</FormControl>
						<FormControl fullWidth>
							<Typography
								variant="body2"
								color="primary"
								sx={{ mb: "6px" }}
							>
								Tipo do edital *
							</Typography>
							<Select
								name="edict_type"
								value={formData.edict_type}
								onChange={handleChange("edict_type")}
								required
							>
								<MenuItem value="Doutorado">Doutorado</MenuItem>
								<MenuItem value="Mestrado">Mestrado</MenuItem>
							</Select>
						</FormControl>
						<Stack
							direction="row"
							sx={{ flexWrap: "wrap", gap: 3 }}
						>
							<DatePicker
								label="Data de inscrição"
								value={formData.date_application}
								onChange={handleChange("date_application")}
								slots={{ textField: MUITextField }}
								enableAccessibleFieldDOMStructure={false}
								sx={{ flexGrow: 1 }}
							/>
							<DatePicker
								label="Data de homologação"
								value={formData.date_verification}
								onChange={handleChange("date_verification")}
								slots={{ textField: MUITextField }}
								enableAccessibleFieldDOMStructure={false}
								sx={{ flexGrow: 1 }}
							/>
							<DatePicker
								label="Data de avaliação"
								value={formData.date_evaluation}
								onChange={handleChange("date_evaluation")}
								slots={{ textField: MUITextField }}
								enableAccessibleFieldDOMStructure={false}
								sx={{ flexGrow: 1 }}
							/>
							<DatePicker
								label="Data de encerramento"
								value={formData.date_closed}
								onChange={handleChange("date_closed")}
								slots={{ textField: MUITextField }}
								enableAccessibleFieldDOMStructure={false}
								sx={{ flexGrow: 1 }}
							/>
						</Stack>
						<Button
							type="submit"
							variant="contained"
							sx={{ backgroundColor: "black" }}
							fullWidth
						>
							Editar edital
						</Button>
					</Stack>
				</Box>
			</LocalizationProvider>

			<Typography sx={{ m: 4 }}>Avançado</Typography>

			<Stack direction="row" sx={{ flexWrap: "wrap", gap: 1, mt: 4 }}>
				<Button variant="outlined" color="error" disabled={true}>
					Fechar edital
				</Button>

				<Button
					variant="contained"
					color="error"
					onClick={removeEdict}
					disabled={true}
				>
					Remover edital
				</Button>
			</Stack>

			<Typography sx={{ m: 4 }}>Mapeamentos</Typography>

			<Typography sx={{ m: 4 }}>Mapeamento de candidatura</Typography>
			{processDate?.candidate_form_id && (
				<Stack direction="row" sx={{ flexWrap: "wrap", gap: 1, mt: 4 }}>
					<MappingHistory
						processId={processId}
						formId={processDate?.candidate_form_id}
						mappings={candidateMapping || []}
						formType={"candidate"}
					/>
				</Stack>
			)}
			<Typography sx={{ m: 4 }}>Mapeamento de recomendação</Typography>
			{processDate?.candidate_form_id && (
				<Stack direction="row" sx={{ flexWrap: "wrap", gap: 1, mt: 4 }}>
					<MappingHistory
						processId={processId}
						formId={processDate?.recommender_form_id}
						mappings={recommenderMapping || []}
						formType="recommender"
					/>
				</Stack>
			)}
		</Box>
	);
}
