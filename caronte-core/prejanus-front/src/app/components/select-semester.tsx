import React, { useEffect, useState } from "react";
import { MenuItem, Select, SelectChangeEvent } from "@mui/material";
import { useSnackbar } from "@/provider/messageContext";

import { GridStateColDef } from "@mui/x-data-grid/internals";

export default function SelectSemester(
	params: { cell?: any; table?: any; row?: any; colDef?: GridStateColDef } & {
		callback?: () => void;
	},
) {
	const callback = params.callback;
	const applicant = params.row.original ? params.row.original : params.row;

	const { showSnackbar } = useSnackbar();
	const [entrySemester, setEntrySemester] = useState<string>(
		applicant.entrySemester,
	);
	useEffect(() => {
		setEntrySemester(applicant.entrySemester);
	}, [applicant]);
	const [isLoading, setLoading] = useState(false);

	function submissionsEntrySemesterHandler(event: SelectChangeEvent) {
		setLoading(true);

		const value = event.target.value as string;

		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${applicant.id}/api/entry-semester`,
			{
				method: "POST",
				body: JSON.stringify({
					semester: value ?? "",
				}),
			},
		)
			.then(async (res) => {
				if (res.ok && res.status === 200) {
					setEntrySemester(value ?? "");
				} else {
					showSnackbar(
						"Não foi possível atualizar o semestre de entrada :(",
						"warning",
					);
				}
				setLoading(false);
				if (callback) callback();
			})
			.catch(() => {
				setLoading(false);
				showSnackbar(
					"Não foi possível atualizar o semestre de entrada :(",
					"error",
				);
				if (callback) callback();
			});
	}

	return (
		<>
			<Select
				value={entrySemester}
				size="small"
				onClick={(e) => e.stopPropagation()}
				onChange={submissionsEntrySemesterHandler}
				defaultValue={""}
				fullWidth
				disabled={isLoading}
			>
				{[
					<MenuItem
						key={`menuitem--first`}
						value={"Primeiro semestre."}
					>
						Primeiro semestre.
					</MenuItem>,
					<MenuItem
						key={`menuitem--second`}
						value={"Segundo semestre."}
					>
						Segundo semestre.
					</MenuItem>,
				]}
			</Select>
		</>
	);
}
