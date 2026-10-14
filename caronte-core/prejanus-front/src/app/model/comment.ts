import User from "@/app/model/user";
import { CommentType } from "../submissions/[submissionId]/api/dto/applicant-dto";

export default interface Comment {
	id: number;
	user: User;
	text: string;
	postedWhenTime: Date;
	postedWhen: string;
	type: CommentType;
}
