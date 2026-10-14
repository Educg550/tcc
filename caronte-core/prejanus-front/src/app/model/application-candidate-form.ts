export interface I18nText {
	en?: string;
	pt?: string;
}

// Tipos de campos suportados pelo sistema
export type FieldType =
	| "Text"
	| "LongText"
	| "Number"
	| "Date"
	| "Radio"
	| "CheckBox"
	| "File";

// Representa um campo individual dentro de uma seção
export interface FormField {
	id: number;
	section_id: number;
	section_title: I18nText;
	label: I18nText;
	name: string;
	type: FieldType;
	prefix: string | null;
	value: string;
}

// Representa uma seção do formulário (ex: Dados Pessoais, Acadêmicos)
export interface FormSection {
	id: number;
	title: I18nText;
	fields: FormField[];
}

export type CandidateFormResponse = FormSection[];
