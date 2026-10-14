export enum RolesUser {
	teacher = "teacher",
	coordinator = "coordinator",
	student = "student",
	administrator = "administrator",
	secretary = "secretary",
}

export const isAdminRole = (role?: RolesUser) =>
	["coordinator", "administrator", "secretary"].includes(role || "");

export default interface User {
	id: number;
	name: string;
	email: string;
	role: string;
}
