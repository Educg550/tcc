export type TPhaseDTO = {
	id: number;
	closed_date: string;
	phase: string;
};

export type TProcessDTO = {
	id: number;
	title: string;
	description: string;
	candidate_form_id: string,
	recommender_form_id:string,
	closed_date: string;
	created_at: string;
	year: number;
	semester: number;
	type: string;
	is_open: boolean;
	phase: string;
	slots: string;
	phases: TPhaseDTO[];
};
