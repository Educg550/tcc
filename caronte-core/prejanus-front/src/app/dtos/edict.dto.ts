import { EEdictType, EEdictStatus } from "../model/edict";

export type EdictDTO = {
	id: number;
	title: string;
	year: number;
	semester: number;
	edict_type: EEdictType;
	is_open: EEdictStatus;
};
