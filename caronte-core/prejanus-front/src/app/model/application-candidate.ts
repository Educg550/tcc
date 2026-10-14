import InfoField from "@/app/shared/model/info-field";
import Comment from "@/app/model/comment";
import User from "@/app/model/user";
import {
	DocumentDto,
	UserDto,
} from "../submissions/[submissionId]/api/dto/applicant-dto";
import Label from "./label";

export enum ApprovalState {
	Approved = "approved",
	Refused = "refused",
	UnderReview = "underreview",
	Waitlist = "waitlist",
}

export enum BiddingState {
	DECLINE = "decline",
	AVAILABLE = "available",
	INTERESTED = "interested",
	INTERESTED_SCHOLARSHIP = "interested_scholarship",
	AGREED = "agreed",
}

export default interface ApplicationCandidate {
	id: number;
	name: string;
	email: string;
	lattesCurriculum: string;
	personalWebsite?: string;
	personalInfo: InfoField[];
	applicationInfo: InfoField[];
	acceptInfo: InfoField[];
	recommendersInfo: InfoField[][];
	submittedDocs: DocumentDto[];
	comments: Comment[];
	privateNotes: string;
	isFavorite: boolean;
	stats: ApprovalState;
	userBidding: BiddingState;
	applicationDate: Date;
	labels: Label[];
	biddingUsers: Record<BiddingState, BiddingUser[]>;
	entrySemester: string;
	letterSent: boolean;
}

export interface BiddingUser extends UserDto {
	slots?: string;
}

export interface ApplicantItem {
	id: number;
	token: string;
	name: string;
	email: string;
	nationality: string;
	lattesCurriculum: string;
	personalWebsite?: string;
	gender: string;
	birthDate: string;
	phoneNumber: string;
	graduation: {
		country: string;
		institution: string;
		course: string;
		year: number;
	};
	poscomp?: {
		year: number;
		score: number;
	};
	currentOccupation?: string;
	research: {
		program: string;
		semester: string;
		field: {
			primary: string;
			secondary: string;
		};
		willApplyScholarship: boolean;
		dedicationLevel: string;
	};
	comments: Comment[];
	submittedDocs: DocumentDto[];
	applicationDate: string;
	isFavorite: boolean;
	stats: ApprovalState;
	userBidding: BiddingState;
	labels: Label[];
	biddingUsers: Record<BiddingState, BiddingUser[]>;
	disabilities: boolean;
	ethnicityRace: boolean;
	acceptInfo: string;
}

export interface CandidateDocument {
	title: string;
	label: string;
	url: string;
}
