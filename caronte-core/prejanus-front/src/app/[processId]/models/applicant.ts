export type TFields = {
	primary: string;
	secondary: string;
};

export type TPoscomp = {
	year: number;
	score: number;
};

export type TApplicant = {
	id: number;
	name: string;
	email: string;
	graduation: string;
	dedicationLevel: string;
	fields: TFields;
	poscomp?: TPoscomp;
	advisor: string;
	scholarshipInterest: boolean;
};
