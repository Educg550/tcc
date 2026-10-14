export type MappingTypeLeaf =
	| "Text"
	| "LongText"
	| "Number"
	| "Date"
	| "Checkbox"
	| "Radio";

export type MappingTypeNode = {
	[key: string]: MappingTypeNode | MappingTypeLeaf;
};

export type MappingLeaf = {
	field: number | null;
	section: number | null;
};

export type MappingNode = {
	[key: string]: MappingNode | MappingLeaf;
};

export type TMapping = {
	id: number;
	form_id: number;
	edict_id: number;
	form_version: string;
	is_active: boolean;
	form_type: "recommender" | "candidate";
	created_at: string;
	mapping: MappingNode;
};
