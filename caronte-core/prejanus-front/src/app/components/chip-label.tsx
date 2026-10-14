import React from "react";
import { Chip } from "@mui/material";
import { getTextColor } from "../[processId]/submissions/[submissionId]/utils/utils";

export default function ChipLabel(params: any) {
	return params.cell.row.original.labels.map(
		(value: { label: string; color: string }, index: number) => (
			<Chip
				key={index}
				label={value.label}
				sx={{
					color: getTextColor(value.color),
					backgroundColor: value.color,
					marginRight: 1,
				}}
			/>
		),
	);
}
