export enum EEdictStatus {
	CLOSED = 0,
	OPEN = 1,
}

export enum EEdictType {
	MASTERS = "Mestrado",
	PHD = "Doutorado",
}

export type TEdict = {
	id: number;
	title: string;
	year: number;
	semester: number;
	edictType: EEdictType;
	isOpen: EEdictStatus;
};
