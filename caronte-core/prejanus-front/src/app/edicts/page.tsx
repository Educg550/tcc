"use client";

import { useSnackbar } from "@/provider/messageContext";
import {
	Box,
	Button,
	FormControl,
	MenuItem,
	Select,
	SelectChangeEvent,
	Stack,
	Switch,
	TextField as MUITextField,
	Typography,
} from "@mui/material";
import { DatePicker, LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs, { Dayjs } from "dayjs";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { TForms } from "../model/forms";
import useSWR from "swr";
import MappingCreator from "../components/MappingCreator";
import {
	RECOMMENDER_MAPPING_PARAMS,
	CANDIDATE_MAPPING_PARAMS,
} from "../shared/data/mapping_params";

const Edicts = () => {
	const router = useRouter();
	const { showSnackbar } = useSnackbar();

	const [formData, setFormData] = useState({
		title: "",
		description: "",
		year: "",
		semester: "",
		edict_type: "",
		candidate_forms: null as number | null,
		recommenders_forms: null as number | null,
		is_open: true,
		date_application: null as Dayjs | null,
		date_verification: null as Dayjs | null,
		date_evaluation: null as Dayjs | null,
		date_closed: null as Dayjs | null,
	});

	const {
		data: responseFormsData,
		error,
		isLoading,
	} = useSWR<TForms[]>(
		`/api/forms/forms-by-tag?year=${formData.year}&edict_type=${formData.edict_type}`,
	);

	const [processId, setProcessId] = useState<null | number>(null);

	useEffect(() => {
		setFormData((prev) => ({
			...prev,
			date_application: dayjs().add(0, "day"),
			date_verification: dayjs().add(1, "day"),
			date_evaluation: dayjs().add(2, "day"),
			date_closed: dayjs().add(3, "day"),
		}));
	}, []);

	type ChangeEvents =
		| React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
		| SelectChangeEvent<string>;

	const handleChange =
		(field: string) => (event: ChangeEvents | Dayjs | null) => {
			const value = field.startsWith("date")
				? event
				: (event as ChangeEvents).target.value;
			setFormData((prevData) => ({
				...prevData,
				[field]: value,
			}));
		};

	const handleChangeFormField = (field: string) => (event: ChangeEvents) => {
		const value = event.target.value;
		const form = responseFormsData?.filter(
			(form) => form.id.toString() == value,
		)[0];
		const created_at = form?.created_at || formData["date_application"];
		setFormData((prevData) => ({
			...prevData,
			date_application: dayjs(created_at),
			[field]: value,
		}));
	};

	const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		setFormData((prev) => ({
			...prev,
			is_open: e.target.checked,
		}));
	};

	const [years, setYears] = useState<number[]>([]);
	useEffect(() => {
		const currentYear = new Date().getFullYear();
		setYears(Array.from({ length: 6 }, (_, i) => currentYear + i));
	}, []);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		try {
			const response = await fetch("edicts/api", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(formData),
			});

			if (!response.ok) {
				const errorData = await response.json();
				showSnackbar(
					`Erro: ${errorData.error?.detail[0].input + " " + errorData.error?.detail[0].msg || "Erro ao criar o edital"}`,
					"error",
				);
				return;
			}
			const edict = await response.json();

			showSnackbar(`Edital criado com sucesso!`, "success");
			setProcessId(edict.id);

			//router.push("/");
		} catch (error) {
			showSnackbar(
				`Erro: ${error instanceof Error ? error.message : "Erro desconhecido"}`,
				"error",
			);
		}
	};

	const [candidateFormMappingCreated, setCandidateFormMappingCreated] =
		useState(false);

	if (processId) {
		if (!candidateFormMappingCreated) {
			return (
				<MappingCreator
					setCandidateFormMappingCreated={
						setCandidateFormMappingCreated
					}
					formId={formData.candidate_forms}
					processId={processId}
					version={1}
					properties={CANDIDATE_MAPPING_PARAMS}
					formType="candidate"
				/>
			);
		} else {
			return (
				<MappingCreator
					setCandidateFormMappingCreated={
						setCandidateFormMappingCreated
					}
					formId={formData.recommenders_forms}
					processId={processId}
					properties={RECOMMENDER_MAPPING_PARAMS}
					version={1}
					formType="recommender"
				/>
			);
		}
	}

	return (
		<Stack
			direction="column"
			justifyContent="center"
			alignItems="center"
			spacing={4}
			sx={{ mb: 10 }}
		>
			<Typography variant="h6" color="primary">
				Insira as informações do edital:
			</Typography>
			<LocalizationProvider dateAdapter={AdapterDayjs}>
				<form
					onSubmit={handleSubmit}
					style={{ maxWidth: "600px", margin: "0 auto" }}
				>
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
							multiline
							rows={4}
							value={formData.description}
							onChange={handleChange("description")}
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
						<FormControl fullWidth>
							<Typography
								variant="body2"
								color="primary"
								sx={{ mb: "6px" }}
							>
								Formulário de inscrição *
							</Typography>
							<Select
								labelId="candidate_forms"
								name="candidate_forms"
								value={formData.candidate_forms}
								onChange={handleChangeFormField(
									"candidate_forms",
								)}
								required
							>
								{responseFormsData?.map((data) => {
									if (
										Object.keys(data.tags).includes(
											"Publico",
										) &&
										Object(data.tags)["Publico"] ==
											"candidatos"
									) {
										return (
											<MenuItem
												key={data.id}
												value={data.id}
											>
												<Box>
													<Typography
														variant="body1"
														sx={{
															fontWeight: "bold",
														}}
													>
														({data.id})
													</Typography>
													<Typography variant="body2">
														{data.title}
													</Typography>
													<Typography variant="body2">
														{data.phase}
													</Typography>
												</Box>
											</MenuItem>
										);
									}
								})}
							</Select>
						</FormControl>
						<FormControl fullWidth>
							<Typography
								variant="body2"
								color="primary"
								sx={{ mb: "6px" }}
							>
								Formulário de recomendação *
							</Typography>
							<Select
								labelId="recommenders_forms"
								name="recommenders_forms"
								value={formData.recommenders_forms}
								onChange={handleChange("recommenders_forms")}
								required
							>
								{responseFormsData?.map((data) => {
									if (
										Object.keys(data.tags).includes(
											"Publico",
										) &&
										Object(data.tags)["Publico"] ==
											"recomendadores"
									) {
										return (
											<MenuItem
												key={data.id}
												value={data.id}
											>
												<Box>
													<Typography
														variant="body1"
														sx={{
															fontWeight: "bold",
														}}
													>
														({data.id})
													</Typography>
													<Typography variant="body2">
														{data.title}
													</Typography>
													<Typography variant="body2">
														{data.phase}
													</Typography>
												</Box>
											</MenuItem>
										);
									}
								})}
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
								enableAccessibleFieldDOMStructure={false}
								slots={{ textField: MUITextField }}
								sx={{ flexGrow: 1 }}
							/>
							<DatePicker
								label="Data de homologação"
								value={formData.date_verification}
								onChange={handleChange("date_verification")}
								enableAccessibleFieldDOMStructure={false}
								slots={{ textField: MUITextField }}
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
								enableAccessibleFieldDOMStructure={false}
								slots={{ textField: MUITextField }}
								sx={{ flexGrow: 1 }}
							/>
						</Stack>
						<Stack
							direction="column"
							justifyContent="center"
							alignItems="center"
							spacing={2}
						>
							<Typography variant="body2" color="primary">
								Status do Edital (Aberto/Fechado):
							</Typography>
							<Switch
								checked={formData.is_open}
								onChange={handleSwitchChange}
							/>
						</Stack>
						<Button
							type="submit"
							variant="contained"
							sx={{ backgroundColor: "black" }}
							fullWidth
						>
							Criar edital
						</Button>
					</Stack>
				</form>
			</LocalizationProvider>
		</Stack>
	);
};

export default Edicts;
