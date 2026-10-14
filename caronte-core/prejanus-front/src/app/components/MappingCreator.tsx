import {
	MenuItem,
	Select,
	Typography,
	FormControl,
	InputLabel,
	Accordion,
	AccordionDetails,
	Stack,
	AccordionSummary,
	Button,
} from "@mui/material";
import { useRouter } from "next/navigation";
import { Box } from "@mui/system";
import withElevationBackground from "@/components/CustomPaper";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { useState, useEffect, useMemo } from "react";
import useSWR from "swr";
import { useSnackbar } from "@/provider/messageContext";
import {
	TMapping,
	MappingTypeNode,
	MappingTypeLeaf,
} from "../[processId]/models/mapping";
import { mappingService } from "../../services/mappingService";
import {
	flatToTree,
	parseFormData,
	parseNodeKeys,
	treeToFlat,
} from "@/utils/mapping";
import { useMappings } from "../hooks/useMappings";

type FormFieldType = {
	id: number;
	name: string;
	label?: {
		pt: string;
		en?: string;
	};
};

type SectionType = {
	id: number;
	title: {
		pt: string;
		en?: string;
	};
	fields: FormFieldType[];
};

export type MappingCreatorProps = {
	formId: number | string | null;
	processId: number | string | null;
	properties: MappingTypeNode;
	setCandidateFormMappingCreated: (old: any) => void;
	formType: "candidate" | "recommender";
	defaultMapping?: TMapping["mapping"];
	mappingId?: number | string;
	version: number;
};

function FormField({
	name,
	formData,
	form_struct,
	getFieldsBySection,
	handleSectionChange,
	handleFieldChange,
}: {
	name: string;
	formData: Record<string, { section: number | null; field: number | null }>;
	form_struct: SectionType[];
	getFieldsBySection: (sectionId: number | null) => FormFieldType[];
	handleSectionChange: (property: string) => (event: any) => void;
	handleFieldChange: (property: string) => (event: any) => void;
}) {
	const selectedSection = formData[name]?.section ?? null;
	const selectedField = formData[name]?.field ?? null;

	const fields = getFieldsBySection(selectedSection);

	return (
		<Box
			sx={{
				display: "flex",
				flexWrap: "wrap",
				gap: 2,
				marginBottom: "10px",
				alignItems: "center",
			}}
		>
			<Typography
				sx={{
					width: 180,
					px: 2,
					flexShrink: 0,
				}}
			>
				{name}
			</Typography>

			<Box
				sx={{
					display: "flex",
					flexWrap: "wrap",
					gap: 2,
					marginBottom: "10px",
					alignItems: "center",
				}}
			>
				{/* seção */}
				<FormControl size="small" sx={{ width: 200, flexShrink: 0 }}>
					<InputLabel>Seção</InputLabel>

					<Select
						value={selectedSection}
						label="Seção"
						onChange={handleSectionChange(name)}
					>
						{form_struct.map((section) => (
							<MenuItem key={section.id} value={section.id}>
								{section.title?.pt ||
									section.title?.en ||
									`Título vazio (seção ${section.id})`}
							</MenuItem>
						))}
					</Select>
				</FormControl>

				{/* campo */}
				<FormControl
					size="small"
					disabled={selectedSection == null}
					sx={{ width: 200, flexShrink: 0 }}
				>
					<InputLabel>Campo</InputLabel>

					<Select
						value={selectedField}
						label="Campo"
						onChange={handleFieldChange(name)}
					>
						{fields.map((field) => (
							<MenuItem key={field.id} value={field.id}>
								{field.label?.pt ||
									field.label?.en ||
									field.name}
							</MenuItem>
						))}
					</Select>
				</FormControl>
			</Box>
		</Box>
	);
}

function RenderMapping({
	node,
	path = "",
	level = 0,
	formData,
	form_struct,
	getFieldsBySection,
	handleSectionChange,
	handleFieldChange,
	expandedSections,
	toggleSection,
}: {
	node: MappingTypeNode;
	path?: string;
	level?: number;
	formData: Record<string, { section: number | null; field: number | null }>;
	form_struct: SectionType[];
	getFieldsBySection: (sectionId: number | null) => FormFieldType[];
	handleSectionChange: (property: string) => (event: any) => void;
	handleFieldChange: (property: string) => (event: any) => void;
	expandedSections: Record<string, boolean>;
	toggleSection: (key: string) => void;
}) {
	const ElevatedAccordion = useMemo(
		() => withElevationBackground(Accordion),
		[],
	);

	return (
		<Box sx={{ margin: "5px" }}>
			{Object.entries(node).map(([key, value]) => {
				const fullKey = path ? `${path}.${key}` : key;

				return typeof value === "string" ? (
					<FormField
						name={fullKey}
						formData={formData}
						form_struct={form_struct}
						getFieldsBySection={getFieldsBySection}
						handleSectionChange={handleSectionChange}
						handleFieldChange={handleFieldChange}
					/>
				) : (
					<ElevatedAccordion
						sx={{ mt: 1, mb: 1 }}
						key={fullKey}
						elevation={2}
						slotProps={{ heading: { component: "p" } }}
						expanded={!!expandedSections[fullKey]}
						onChange={() => toggleSection(fullKey)}
					>
						<AccordionSummary expandIcon={<ArrowDropDownIcon />}>
							<Typography variant="h6">{key}</Typography>
						</AccordionSummary>
						<AccordionDetails>
							<RenderMapping
								node={value as MappingTypeNode}
								path={fullKey}
								level={level + 1}
								formData={formData}
								form_struct={form_struct}
								getFieldsBySection={getFieldsBySection}
								handleSectionChange={handleSectionChange}
								handleFieldChange={handleFieldChange}
								expandedSections={expandedSections}
								toggleSection={toggleSection}
							/>
						</AccordionDetails>
					</ElevatedAccordion>
				);
			})}
		</Box>
	);
}

export default function MappingCreator({
	formId,
	processId,
	properties,
	version,
	setCandidateFormMappingCreated,
	formType,
	defaultMapping = {},
	mappingId,
}: MappingCreatorProps) {
	const { createMapping, updateMapping } = useMappings(processId ?? "", formType);
	const [formData, setFormData] = useState<
		Record<
			string,
			{
				section: number | null;
				field: number | null;
			}
		>
	>(
		Object.keys(defaultMapping).length > 0
			? treeToFlat(defaultMapping)
			: parseFormData(properties),
	);

	useEffect(() => {
		setFormData(
			Object.keys(defaultMapping).length > 0
				? treeToFlat(defaultMapping)
				: parseFormData(properties),
		);
	}, [defaultMapping, properties]);

	const isEdit = mappingId != null;

	const router = useRouter();

	const isMappingDone = useMemo(() => {
		return Object.entries(formData).every(([key, value]) => {
			return value.section != null && value.field != null;
		});
	}, [formData]);

	const formUrl = formId
		? `/api/forms/${formId}${version ? `?version=${version}` : ""}`
		: null;
	const { data: form_struct = [] } = useSWR<SectionType[]>(formUrl);

	const { showSnackbar } = useSnackbar();

	// Inicializa todos os nós intermediários como expandidos
	const [expandedSections, setExpandedSections] = useState<
		Record<string, boolean>
	>(() => {
		const nodeKeys = parseNodeKeys(properties);
		return Object.fromEntries(nodeKeys.map((k) => [k, true]));
	});

	function toggleSection(key: string) {
		setExpandedSections((prev) => ({
			...prev,
			[key]: !prev[key],
		}));
	}

	function handleSectionChange(property: string) {
		return (event: any) => {
			const sectionId = Number(event.target.value);

			setFormData((prev) => ({
				...prev,
				[property]: {
					section: sectionId,
					field: null,
				},
			}));
		};
	}

	function handleFieldChange(property: string) {
		return (event: any) => {
			const fieldId = Number(event.target.value);

			setFormData((prev) => ({
				...prev,
				[property]: {
					...prev[property],
					field: fieldId,
				},
			}));
		};
	}

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (formId == null) return;

		try {
			if (isEdit) {
				await updateMapping(version, mappingId, flatToTree(formData));
				showSnackbar("Mapeamento editado com sucesso!", "success");
				setCandidateFormMappingCreated(true);
			} else {
				await createMapping(formId, version, flatToTree(formData));
				showSnackbar("Mapeamento criado com sucesso!", "success");
				setCandidateFormMappingCreated(true);
			}
		} catch (error: any) {
			showSnackbar(
				error?.error?.detail?.[0]?.msg ??
					error?.message ??
					"Erro desconhecido",
				"error",
			);
		}
	};

	const getFieldsBySection = (sectionId: number | null) => {
		if (sectionId == null) return [];
		return form_struct.find((s) => s.id === sectionId)?.fields || [];
	};

	return (
		<Stack
			direction="column"
			justifyContent="center"
			alignItems="center"
			spacing={4}
			sx={{ mb: 10 }}
		>
			<Typography variant="h6" color="primary">
				Insira as informações do formulário de{" "}
				{formType == "candidate" ? "inscrição" : "recomendação"}:
			</Typography>
			<form
				onSubmit={handleSubmit}
				style={{ maxWidth: "600px", minWidth: "40%", margin: "0 auto" }}
			>
				<RenderMapping
					node={properties}
					formData={formData}
					form_struct={form_struct}
					getFieldsBySection={getFieldsBySection}
					handleSectionChange={handleSectionChange}
					handleFieldChange={handleFieldChange}
					expandedSections={expandedSections}
					toggleSection={toggleSection}
				/>

				<Button
					type="submit"
					variant="contained"
					//disabled={!isMappingDone}
					sx={{ backgroundColor: "black" }}
					fullWidth
				>
					{isEdit ? "Salvar alterações" : "Criar mapeamento"}
				</Button>
			</form>
		</Stack>
	);
}
