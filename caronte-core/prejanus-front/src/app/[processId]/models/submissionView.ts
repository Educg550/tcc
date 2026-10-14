import { UserDTO } from "../../../lib/getCurrentUser";
import ApplicantDto from "../../submissions/[submissionId]/api/dto/applicant-dto";

export type SubmissionView = {
	id: number;
	user_id: number;
	submission_id: number;
	created_at: string; // ISO
	updated_at?: string | null; // ISO

	submission?: ApplicantDto;
	user?: UserDTO;
};
