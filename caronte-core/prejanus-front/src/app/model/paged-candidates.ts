import { ApplicantItem } from "./application-candidate";

export default interface PagedCandidates {
	page: number;
	itemCount: number;
	totalItems: number;
	candidates: ApplicantItem[];
}
