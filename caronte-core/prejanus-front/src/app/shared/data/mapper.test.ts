import {
	personalInfoFromApplicantDto,
	recommendersInfoApplicantDto,
} from "@/app/shared/data/mapper";
import ApplicantDto, {
	CommentType,
	SentStatus,
} from "@/app/submissions/[submissionId]/api/dto/applicant-dto";
import assert from "node:assert";
import expect from "expect";
import { ApprovalState, BiddingState } from "../../model/application-candidate";

const baseApplicantDto = {
	id: 1,
	token: "",
	stats: ApprovalState.Approved,
	poscomp: {
		score: 0,
		year: 2000,
	},
	phone_number: "11999999999",
	user_bidding: BiddingState.AVAILABLE,
	bidding_users: {
		data: {
			[BiddingState.AVAILABLE]: [],
			[BiddingState.INTERESTED]: [],
			[BiddingState.INTERESTED_SCHOLARSHIP]: [],
			[BiddingState.AGREED]: [],
			[BiddingState.DECLINE]: [],
		},
	},
	private_note: "",
	labels: [],
	disabilities: false,
	ethnicity_race: false,
	accept: {
		sent: SentStatus.NOT_SENT,
		accept: "",
		comments: "",
	},
	letter_sent: false,
	relevant_information: "",
	entry_semester: "2024/1",
	current_occupation: "",
	recommenders: [],
	name: "Paulo Meirelles",
	email: "paulomeirelles@email.com",
	nationality: "Brasileiro",
	birth_date: "24/09/1982",
	lattes_curriculum: "https://lattes.cnpq.br/2193972715230641",
	personal_website: "",
	gender: "CIS_MALE",
	graduation: {
		country: "Estados Unidos da América",
		institution: "University of Illinois",
		year: 2005,
		course: "Computer Science",
	},
	research: {
		dedication_level: "PARTIAL",
		semester: "1",
		field: {
			primary: "Engenharia de Software",
			secondary: "Inteligência Artificial",
		},
		program: "Mestrado Acadêmico em Ciência da Computação",
		will_apply_scholarship: false,
	},
	documents: [
		{
			title: "Diploma de graduação",
			url: "https://....",
			label: "Diploma de graduação",
		},
	],
	comments: [
		{
			id: 1,
			user: {
				id: 2,
				name: "Fabio Kon",
				email: "fabiokon@email.com",
				role: "TEACHER",
			},
			comment: "Comentário",
			created_at: "2024-09-19T18:37:21.742Z",
			type: CommentType.Comment,
		},
	],
	application_date: "2024-10-04T01:43:38.680Z",
	is_favorite: false,
} as unknown as ApplicantDto;

test("given candidate without poscomp, when personalInfoFromApplicantDto is called, then result must not contain poscomp year and score", () => {
	const candidateWithoutPoscomp: ApplicantDto = {
		...baseApplicantDto,
		poscomp: undefined,
	};
	const result = personalInfoFromApplicantDto(candidateWithoutPoscomp);

	assert(!result.some((field) => field.name === "poscomp.score"));
	assert(!result.some((field) => field.name === "poscomp.year"));
});

test("given recommenders with sent=true and sent=false, recommendersInfoApplicantDto maps them correctly", () => {
	const dto: ApplicantDto = {
		...baseApplicantDto,
		recommenders: [
			{
				fullname_candidate: "Paulo Meirelles",
				fullname: "Prof. Recommender",
				email: "recommender@email.com",
				affiliation: "USP",
				known_time: "5 anos",
				relationship: ["Orientador"],
				rating: "Excelente",
				sent: true,
			},
			{
				fullname_candidate: "Paulo Meirelles",
				fullname: "Prof. Pending",
				email: "pending@email.com",
				affiliation: "",
				known_time: "",
				relationship: [],
				rating: "",
				sent: false,
			},
		],
	};

	const result = recommendersInfoApplicantDto(dto);
	expect(result.length).toBe(2);

	const rec1Sent = result[0].find((f) => f.name === "recommender.sent");
	expect(rec1Sent?.value).toBe("true");

	const rec2Sent = result[1].find((f) => f.name === "recommender.sent");
	expect(rec2Sent?.value).toBe("false");
});

test("given recommender without email or without fullname, recommendersInfoApplicantDto does not drop it", () => {
	const dto: ApplicantDto = {
		...baseApplicantDto,
		recommenders: [
			{
				fullname_candidate: "Paulo Meirelles",
				fullname: "Prof. Only Name",
				email: "",
				affiliation: "",
				known_time: "",
				relationship: [],
				rating: "",
				sent: true,
			},
		],
	};

	const result = recommendersInfoApplicantDto(dto);
	expect(result.length).toBe(1);
	expect(result[0].find((f) => f.name === "recommender.fullname")?.value).toBe("Prof. Only Name");
});

test("given candidate with poscomp, when personalInfoFromApplicantDto is called, then result must contain poscomp year and score", () => {
	const candidateWithPoscomp: ApplicantDto = {
		...baseApplicantDto,
		poscomp: { year: 2020, score: 30 },
	};

	const result = personalInfoFromApplicantDto(candidateWithPoscomp);

	expect(result.some((field) => field.name === "poscomp.score"));
	expect(result.some((field) => field.name === "poscomp.year"));
});

test("given candidate without occupation, when personalInfoFromApplicantDto is called, then result must not contain occupation", () => {
	const result = personalInfoFromApplicantDto(baseApplicantDto);

	expect(!result.some((field) => field.name === "current_occupation"));
});

test("given candidate with occupation, when personalInfoFromApplicantDto is called, then result must contain occupation", () => {
	const candidateWithPoscomp: ApplicantDto = {
		...baseApplicantDto,
		current_occupation: "Occupation",
	};

	const result = personalInfoFromApplicantDto(candidateWithPoscomp);

	expect(result.some((field) => field.name === "current_occupation"));
});
