import { Box, Chip, Stack, Typography } from "@mui/material";
import { MappingLeaf, MappingNode } from "../models/mapping";
import { FormField, FormSection } from "../../model/application-candidate-form";

function isLeaf(node: any): node is MappingLeaf {
	return (
		node && typeof node === "object" && "field" in node && "section" in node
	);
}

export default function MappingVisualizer({
	mappingNodes,
	level = 0,
	flattenFormFields,
	flattenFormSections,
}: {
	mappingNodes: MappingNode;
	level?: number;
	flattenFormFields: { [key: string]: FormField };
	flattenFormSections: { [key: string]: FormSection };
}) {
	return (
		<Stack spacing={0.5} sx={{ pl: level * 1.5 }}>
			{Object.entries(mappingNodes).map(([key, value]) => {
				if (value == null) return;
				const leaf = isLeaf(value);

				return (
					<Box
						key={key}
						sx={{
							borderLeft: "2px solid",
							borderColor: "grey.200",
							pl: 2,
							py: leaf ? 0.75 : 1,
							my: 0.5,
							transition: "border-color 0.2s ease",
							"&:hover": {
								borderColor: "primary.light",
							},
						}}
					>
						{leaf ? (
							// Se for um nó final, renderiza tudo em uma linha
							<Stack
								direction="row"
								alignItems="center"
								spacing={2}
								flexWrap="wrap"
							>
								<Typography
									variant="body2"
									sx={{
										fontWeight: 600,
										color: "text.primary",
										minWidth: "70px",
									}}
								>
									{key}:
								</Typography>

								<Stack direction="row" spacing={1}>
									{/* Tag de Seção - Tom Neutro */}
									<Chip
										label={`Seção ${flattenFormSections[`${value.section}`]?.title?.pt}`}
										size="small"
										sx={{
											backgroundColor: "#f1f5f9",
											color: "#475569",
											fontWeight: 500,
											fontSize: "0.75rem",
											border: "none",
										}}
									/>
									<Chip
										label={`Campo ${flattenFormFields[`${value.section}:${value.field}`]?.name}`}
										size="small"
										sx={{
											backgroundColor: "#eff6ff",
											color: "#1d4ed8",
											fontWeight: 500,
											fontSize: "0.75rem",
											border: "none",
										}}
									/>
								</Stack>
							</Stack>
						) : (
							// Se tiver filhos, mantém a estrutura de árvore vertical
							<>
								<Typography
									variant="body2"
									sx={{
										fontWeight: 700,
										color: "text.primary",
										mb: 1,
									}}
								>
									{key}:
								</Typography>

								<MappingVisualizer
									flattenFormFields={flattenFormFields}
									flattenFormSections={flattenFormSections}
									mappingNodes={value}
									level={level + 1}
								/>
							</>
						)}
					</Box>
				);
			})}
		</Stack>
	);
}
