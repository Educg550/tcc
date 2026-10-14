import React from "react";
import { Checkbox } from "@mui/material";

export default function CheckboxItem(params: any) {
	return (
		<Checkbox
			value={params.cell.getValue()}
			checked={params.cell.getValue()}
			disabled
		/>
	);
}
