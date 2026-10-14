import { ApprovalState, BiddingState } from "@/app/model/application-candidate";

export default interface BiddingUserDto extends UserDto {
	slots: string;
}

export enum SentStatus {
	NOT_SENT = "not_sent",
	SENT = "sent",
	REPLIED = "replied",
}

export default interface ApplicantDto {
	id: number;
	token: string;
	name: string;
	email: string;
	nationality: string;
	lattes_curriculum: string;
	personal_website?: string;
	gender: string;
	birth_date: string;
	phone_number: string;
	relevant_information: string;
	entry_semester: string;
	graduation: {
		country: string;
		institution: string;
		year: number;
		course: string;
	};
	poscomp?: {
		year: number;
		score: number;
	};
	current_occupation?: string;
	research: {
		program: string;
		semester: string;
		field: {
			primary: string;
			secondary: string;
		};
		will_apply_scholarship: boolean;
		dedication_level: string;
	};
	recommenders: RecommenderDto[];
	comments: CommentDto[];
	documents: DocumentDto[];
	application_date: string;
	is_favorite?: boolean;
	stats: ApprovalState;
	user_bidding: BiddingState;
	bidding_users: {
		data: Record<BiddingState, BiddingUserDto[]>;
	};
	private_note: string;
	labels: LabelDto[];
	disabilities: boolean;
	ethnicity_race: boolean;
	accept: {
		sent: SentStatus;
		accept: string;
		comments: string;
	};
	letter_sent: boolean
}

export interface LabelDto {
	label: string;
	color: string;
	id: number;
}

export interface RecommenderDto {
	fullname_candidate: string;
	fullname: string;
	affiliation: string;
	known_time: string;
	relationship: string[];
	rating: string;
	email: string;
	sent: boolean;
}

export interface DocumentDto {
	title: string;
	url: string;
	label: string;
}

export enum CommentType {
	Comment = "comment",
	Activity = "activity",
	Favorite = "favorite",
	Interest = "interest",
	Advisor = "advisor",
	Custom = "custom",
	ExternalComment = "external_comment"
}

export interface CommentDto {
	id: number;
	user: UserDto;
	comment: string;
	created_at: string;
	type: CommentType;
}

export interface UserDto {
	id: number;
	name: string;
	email: string;
	role: string;
}
