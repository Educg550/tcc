export type TApplicantsDTO = {
	applicant_list: TApplicantDTO[];
};

export type TApplicantDTO = {
	id: number;
	name: string;
	email: string;
	graduation: string;
	primary_field: string;
	secondary_field: string;
	dedication_level: string;
	poscomp_year?: number;
	poscomp_score?: number;
	advisor?: string;
	scholarship_interest: boolean;
};
