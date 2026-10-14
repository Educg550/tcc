import { MappingTypeNode } from "../../[processId]/models/mapping";

export const CANDIDATE_MAPPING_PARAMS: MappingTypeNode = {
	name: "Text",
	email: "Text",
	gender: "Text",
	poscomp: {
		file: "Text",
		year: "Text",
		score: "Text",
	},
	research: {
		field: {
			primary: "Text",
			secondary: "Text",
		},
		program: "Text",
		semester: "Text",
		dedication_level: "Text",
		will_apply_scholarship: "Text",
	},
	documents: {
		research_plan: "Text",
		lattes_cv_file: "Text",
		motivation_letter: "Text",
		masters_transcript: "Text",
		studies_transcripts: "Text",
		masters_degree_diploma: "Text",
		masters_thesis_articles: "Text",
		supervisor_acceptance_letter: "Text",
	},
	birth_date: "Text",
	graduation: {
		year: "Text",
		course: "Text",
		country: "Text",
		institution: "Text",
	},
	nationality: "Text",
	disabilities: "Text",
	phone_number: "Text",
	recommenders: {
		recommender1: {
			email: "Text",
			rating: "Text",
			fullname: "Text",
			known_time: "Text",
			affiliation: "Text",
			relationship: "Text",
			fullname_candidate: "Text",
		},
		recommender2: {
			email: "Text",
			rating: "Text",
			fullname: "Text",
			known_time: "Text",
			affiliation: "Text",
			relationship: "Text",
			fullname_candidate: "Text",
		},
	},
	entry_semester: "Text",
	ethnicity_race: "Text",
	personal_website: "Text",
	lattes_curriculum: "Text",
	current_occupation: "Text",
	relevant_information: "Text",
};

export const RECOMMENDER_MAPPING_PARAMS: MappingTypeNode = {
	email: "Text",
	rating: "Text",
	fullname: "Text",
	known_time: "Text",
	affiliation: "Text",
	relationship: "Text",
	fullname_candidate: "Text",
};
