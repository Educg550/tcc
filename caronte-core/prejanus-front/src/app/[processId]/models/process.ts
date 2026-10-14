export type TPhase = {
	id: number;
	label: string;
	closed_date: string;
};

export type TProcess = {
	processId: number;
	title: string;
	candidate_form_id:string,
	recommender_form_id:string,
	date: {
		year: number;
		semester: number;
	};
	dates: {
		closed_date: string;
	};
	year: number;
	semester: number;
	description: string;
	type: string;
	is_open: boolean;
	phase: string;
	slots: string;
	phases: { [key: string]: TPhase };
};
