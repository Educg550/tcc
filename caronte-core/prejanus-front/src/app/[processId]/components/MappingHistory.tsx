import {
	Box,
	Button,
	Paper,
	Divider,
	Chip,
	Stack,
	Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { TMapping } from "../models/mapping";
import {
	CandidateFormResponse,
	FormField,
	FormSection,
} from "../../model/application-candidate-form";
import useSWR from "swr";
import { mappingService } from "../../../services/mappingService";
import { useSnackbar } from "../../../provider/messageContext";
import MappingEditorModal from "./MappingEditorModal";
import MappingVisualizer from "./MappingVisualizer";
import { useMappings } from "../../hooks/useMappings";

type MappingHistoryProps = {
	mappings: TMapping[];
	formId: string | number;
	processId: string | number;
	formType: "candidate" | "recommender";
};

function flattenSections(form: CandidateFormResponse): {
	[key: string]: FormSection;
} {
	const flat: { [key: string]: FormSection } = {};
	form.forEach((section: FormSection) => {
		flat[`${section.id}`] = section;
	});

	return flat;
}

function flattenFields(form: CandidateFormResponse): {
	[key: string]: FormField;
} {
	const flat: { [key: string]: FormField } = {};

	form.forEach((section: FormSection) => {
		section.fields.forEach((field: FormField) => {
			flat[`${section.id}:${field.id}`] = field;
		});
	});

	return flat;
}

function MappingCard({
	mapping,
	formId,
	onEdit,
	onDelete,
}: {
	mapping: TMapping;
	formId: string | number;
	onEdit: (mapping: TMapping) => void;
	onDelete: (mapping: TMapping) => void;
}) {
	const { data: form_struct = [] } = useSWR<FormSection[]>(
		formId ? `/api/forms/${formId}?version=${mapping.form_version}` : null,
	);

	const flattenFormFields = useMemo(
		() => flattenFields(form_struct),
		[form_struct],
	);

	const flattenFormSections = useMemo(
		() => flattenSections(form_struct),
		[form_struct],
	);

	return (
		<Paper
			key={mapping.id}
			elevation={1}
			sx={{
				minWidth: 400,
				borderRadius: 2,
				p: 2,
				flexShrink: 0,
				backgroundColor: "#fafafa",
			}}
		>
			<Stack spacing={2}>
				<Stack
					spacing={2}
					direction="row"
					justifyContent="space-between"
				>
					<Box>
						<Typography
							variant="body2"
							color="text.secondary"
						>
							Versão do mapeamento:{" "}
							{mapping.form_version}
						</Typography>

						<Typography
							variant="body2"
							color="text.secondary"
						>
							Tipo: {mapping.form_type}
						</Typography>
					</Box>
				</Stack>

				<Divider />

				{Object.keys(mapping.mapping).length === 0 ? (
					<Typography color="text.secondary">
						Nenhum mapeamento.
					</Typography>
				) : (
					<MappingVisualizer
						flattenFormSections={flattenFormSections}
						flattenFormFields={flattenFormFields}
						mappingNodes={mapping.mapping}
					/>
				)}
			</Stack>

			<Stack
				direction="row"
				spacing={1.5}
				sx={{ width: "100%", mt: 3 }}
			>
				<Button
					variant="contained"
					disableElevation
					onClick={() => onEdit(mapping)}
					sx={{
						flex: 1,
						textTransform: "none",
						borderRadius: "10px",
						fontWeight: 600,
						py: 1,
						backgroundColor: "primary.main",
						"&:hover": {
							backgroundColor: "primary.dark",
						},
					}}
				>
					Editar
				</Button>

				<Button
					variant="outlined"
					color="error"
					onClick={() => onDelete(mapping)}
					sx={{
						flex: 1,
						textTransform: "none",
						borderRadius: "10px",
						fontWeight: 600,
						py: 1,
						borderColor: "error.light",
						"&:hover": {
							borderColor: "error.main",
							backgroundColor: "rgba(211, 47, 47, 0.04)",
						},
					}}
				>
					Excluir
				</Button>
			</Stack>
		</Paper>
	);
}

export default function MappingHistory({
	processId,
	formId,
	mappings,
	formType,
}: MappingHistoryProps) {
	const { deleteMapping } = useMappings(processId, formType);
	const [open, setOpen] = useState(false);
	const [selectedMapping, setSelectedMapping] = useState<TMapping | null>(
		null,
	);
	const [selectedMappingVersion, setSelectedMappingVersion] =
		useState<number>(1);

	const { data: missing_versions = [] } = useSWR<number[]>(
		`/${processId}/${formType}s/forms/versions/unmapped`,
	);

	const { showSnackbar } = useSnackbar();

	const handleCreate = (version: number) => {
		setSelectedMapping(null);
		setSelectedMappingVersion(version);
		setOpen(true);
	};

	const handleEdit = (mapping: TMapping) => {
		setSelectedMapping(mapping);
		setSelectedMappingVersion(Number(mapping.form_version));
		setOpen(true);
	};

	const handleDelete = async (mapping: TMapping) => {
		try {
			await deleteMapping(
				Number(mapping.form_version),
				mapping.id,
			);
		} catch (error) {
			showSnackbar(
				"Erro ao excluir o mapeamento",
				"error",
			);
		}
	};

	const handleClose = () => {
		setOpen(false);
		setSelectedMapping(null);
	};

	return (
		<>
			<Stack
				direction="row"
				spacing={3}
				sx={{
					overflowX: "auto",
					p: 2,
				}}
			>
				{missing_versions.map((version: number) => (
					<Paper
						key={version}
						elevation={1}
						sx={{
							minWidth: 400,
							borderRadius: 2,
							p: 2,
							flexShrink: 0,
							border: "2px dashed",
							borderColor: "grey.300",
							backgroundColor: "grey.50",
						}}
					>
						<Stack spacing={2}>
							<Stack
								spacing={2}
								direction="row"
								justifyContent="space-between"
							>
								<Box>
									<Typography
										variant="body2"
										color="text.secondary"
									>
										Versão do mapeamento: {version}
									</Typography>

									<Typography
										variant="body2"
										color="text.secondary"
									>
										Tipo: {formType}
									</Typography>
								</Box>
							</Stack>

							<Divider />

							<Chip
								label="Mapeamento não configurado"
								color="default"
								variant="outlined"
							/>

							<Button
								variant="contained"
								disableElevation
								onClick={() => handleCreate(version)}
								sx={{
									flex: 1,
									textTransform: "none",
									borderRadius: "10px",
									fontWeight: 600,
									py: 1,
									backgroundColor: "#0af",
									"&:hover": {
										backgroundColor: "#0bf",
									},
								}}
							>
								Criar mapeamento
							</Button>
						</Stack>
					</Paper>
				))}

				{mappings
					.sort(
						(a, b) =>
							Number(b.form_version) - Number(a.form_version),
					)
					.map((mapping: TMapping) => (
						<MappingCard
							key={mapping.id}
							mapping={mapping}
							formId={formId}
							onEdit={handleEdit}
							onDelete={handleDelete}
						/>
					))}
			</Stack>

			<MappingEditorModal
				open={open}
				mapping={selectedMapping}
				onClose={handleClose}
				formType={formType}
				formId={formId}
				processId={processId}
				version={selectedMappingVersion}
				defaultMapping={selectedMapping?.mapping}
			/>
		</>
	);
}
