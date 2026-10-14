import { Box, Button, Typography } from "@mui/material";
import { FormField } from "../../../../model/application-candidate-form";

interface Props {
	submissionId?: string | string[];
	// Alterado para receber a estrutura de fields do formulário
	fields?: FormField[];
	loading: boolean;
}

export default function CandidateSubmittedDocs({
	submissionId,
	fields,
	loading,
}: Props) {
	if (loading) return null;

	// Filtramos apenas campos que possuem valor (arquivo enviado)
	const documents = fields?.filter((f) => !!f.value) || [];

	return (
		<Box px={2} py={1}>
			{documents.length > 0 ? (
				documents.map((field) => (
					<Box
						key={field.field_id}
						display="flex"
						alignItems="center"
						justifyContent="space-between"
						gap={2}
						px={2}
						mb={1.5}
						flexWrap={"wrap"}
						sx={{
							borderBottom: "1px solid",
							borderColor: "divider",
							pb: 1,
						}}
					>
						<Typography
							variant="body1"
							sx={{
								flex: 1,
								whiteSpace: "nowrap",
								overflow: "hidden",
								textOverflow: "ellipsis",
								minWidth: "200px",
							}}
						>
							{/* Prioriza o label em português (usa-se em inglês, caso o primeiro não exista) */}
							{field.label.pt || field.label.en}
						</Typography>

						<Button
							variant="outlined"
							size="small"
							onClick={() => {
								// A URL agora é composta pelo 'name' (label no backend) e o 'value' (nome do arquivo)
								const fileUrl = `${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/files/${field.name}/${field.value}`;

								fetch(fileUrl, { method: "GET" })
									.then((res) => {
										if (!res.ok)
											throw new Error(
												"Erro ao baixar arquivo",
											);
										return res.blob();
									})
									.then((blob) => {
										const url = URL.createObjectURL(blob);
										window.open(url, "_blank");
									})
									.catch((err) => console.error(err));
							}}
						>
							Visualizar
						</Button>
					</Box>
				))
			) : (
				<Typography
					variant="body2"
					color="text.secondary"
					sx={{ p: 2 }}
				>
					Nenhum documento enviado.
				</Typography>
			)}
		</Box>
	);
}
