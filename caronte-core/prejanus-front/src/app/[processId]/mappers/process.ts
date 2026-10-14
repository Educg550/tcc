import { TProcessDTO } from "../dtos/process.dto";
import Phases from "../models/phases";
import { TPhase, TProcess } from "../models/process";
import { LabelPhase } from "./phases";

export function ToProcessDomain(raw: TProcessDTO): TProcess {
	let phases: { [key: string]: TPhase } = {};

	if (raw.phases) {
		raw.phases.forEach((value, index) => {
			let label = LabelPhase(value.phase as Phases);

			const today = new Date();
			today.setHours(0, 0, 0, 0);

			phases = {
				...phases,
				[value.phase]: {
					id: value.id,
					label: label,
					closed_date: value.closed_date,
				},
			};
		});
	}

	return {
		processId: raw.id,
		title: raw.title,
		recommender_form_id:raw.recommender_form_id,
		candidate_form_id:raw.candidate_form_id,
		semester: raw.semester,
		year: raw.year,
		date: {
			year: raw.year,
			semester: raw.semester,
		},
		dates: {
			closed_date: raw.closed_date,
		},
		phases: phases,
		description: raw.description,
		type: raw.type,
		phase: raw.phase,
		is_open: raw.is_open,
		slots: raw.slots,
	};
}
