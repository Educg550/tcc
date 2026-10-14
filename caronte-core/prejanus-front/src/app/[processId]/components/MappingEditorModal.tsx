import { Box, Modal, Typography } from "@mui/material";
import MappingCreator from "../../components/MappingCreator";
import { MappingNode, TMapping } from "../models/mapping";
import { MappingType } from "../../../services/mappingService";
import {
	CANDIDATE_MAPPING_PARAMS,
	RECOMMENDER_MAPPING_PARAMS,
} from "../../shared/data/mapping_params";

type MappingEditorModalProps = {
	onClose: () => void;
	open: boolean;
	formId: number | string;
	processId: number | string;
	version: number | string;
	defaultMapping?: MappingNode | undefined;
	formType: MappingType;
	mapping: TMapping | null;
};
export default function MappingEditorModal({
	open,
	onClose,
	formId,
	processId,
	version,
	mapping,
	formType,
}: MappingEditorModalProps) {
	return (
		<Modal
			open={open}
			onClose={onClose}
			aria-labelledby="mapping-modal-title"
		>
			<Box
				sx={{
					position: "absolute",
					top: "50%",
					left: "50%",
					transform: "translate(-50%, -50%)",
					maxHeight: "100%",
					overflowY: "auto",
					borderRadius: 2,
					p: 2,
					backgroundColor: "#fafafa",
				}}
			>
				<Typography
					id="mapping-modal-title"
					variant="h6"
					component="h2"
				>
					{mapping ? "Editar mapeamento" : "Criar mapeamento"}
				</Typography>

				{open && (
					<MappingCreator
						key={`${formId}-${version}-${mapping?.id ?? "new"}`}
						formId={formId}
						processId={processId}
						version={Number(version)}
						defaultMapping={mapping?.mapping}
						properties={
							formType == "candidate"
								? CANDIDATE_MAPPING_PARAMS
								: RECOMMENDER_MAPPING_PARAMS
						}
						setCandidateFormMappingCreated={() => {}}
						formType={formType}
						mappingId={mapping?.id}
					/>
				)}
			</Box>
		</Modal>
	);
}
