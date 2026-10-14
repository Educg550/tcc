import { TApplicantDTO } from "../dtos/applicant.dto";
import { TApplicant } from "../models/applicant";
import ApplicantDto, {
	SentStatus,
} from "@/app/submissions/[submissionId]/api/dto/applicant-dto";
import {
	ApplicantItem,
	ApprovalState,
	BiddingState,
} from "@/app/model/application-candidate";
import { commentsFromDto } from "@/app/shared/data/mapper";

export const approvalLabels: Record<ApprovalState, string> = {
	[ApprovalState.Approved]: "Selecionado",
	[ApprovalState.Refused]: "Não Selecionado",
	[ApprovalState.UnderReview]: "Em análise",
	[ApprovalState.Waitlist]: "Lista de Espera",
};

export const biddingLabels: Record<BiddingState, string> = {
	[BiddingState.AGREED]:
		"Orientação previamente acordada com o candidato (5)",
	[BiddingState.INTERESTED_SCHOLARSHIP]:
		"Tenho interesse em orientar este candidato e em oferecer-lhe uma bolsa vinculada aos meus projetos (4)",
	[BiddingState.INTERESTED]: "Tenho interesse em orientar este candidato (3)",
	[BiddingState.AVAILABLE]: "Posso orientar, se necessário (2)",
	[BiddingState.DECLINE]: "Não pretendo orientar este candidato (1)",
};

export const sentLabels: Record<SentStatus, string> = {
	[SentStatus.NOT_SENT]: "Não enviado",
	[SentStatus.SENT]: "Enviado",
	[SentStatus.REPLIED]: "Respondido",
};

export function ToApplicantDomain(raw: TApplicantDTO[]): TApplicant[] {
	function parserToDomain(applicantDTO: TApplicantDTO): TApplicant {
		return {
			id: applicantDTO.id,
			name: applicantDTO.name,
			email: applicantDTO.email,
			fields: {
				primary: applicantDTO.primary_field,
				secondary: applicantDTO.secondary_field,
			},
			graduation: applicantDTO.graduation,
			poscomp: {
				year: applicantDTO.poscomp_year ?? 0,
				score: applicantDTO.poscomp_score ?? 0,
			},
			advisor: applicantDTO.advisor ?? "",
			dedicationLevel: applicantDTO.dedication_level,
			scholarshipInterest: applicantDTO.scholarship_interest,
		};
	}

	return raw?.map(parserToDomain) ?? [];
}

export function applicantDtoToApplicantItem(
	applicant: ApplicantDto,
): ApplicantItem {
	return {
		phoneNumber: applicant.phone_number,
		applicationDate: applicant.application_date,
		birthDate: applicant.birth_date,
		comments: commentsFromDto(applicant),
		currentOccupation: applicant.current_occupation,
		gender: applicant.gender,
		graduation: {
			country: applicant.graduation.country,
			institution: applicant.graduation.institution,
			year: applicant.graduation.year,
			course: applicant.graduation.course,
		},
		id: applicant.id,
		token: applicant.token,
		lattesCurriculum: applicant.lattes_curriculum,
		name: applicant.name,
		email: applicant.email,
		nationality: applicant.nationality,
		personalWebsite: applicant.personal_website,
		poscomp: applicant.poscomp,
		research: {
			semester: applicant.research.semester,
			dedicationLevel: applicant.research.dedication_level,
			field: applicant.research.field,
			program: applicant.research.program,
			willApplyScholarship: applicant.research.will_apply_scholarship,
		},
		submittedDocs: applicant.documents ?? [],
		isFavorite: !!applicant.is_favorite,
		stats: applicant.stats,
		labels: applicant.labels ?? [],
		userBidding: applicant.user_bidding,
		biddingUsers: applicant.bidding_users.data,
		disabilities: applicant.disabilities,
		ethnicityRace: applicant.ethnicity_race,
		acceptInfo: applicant.accept.accept ?? ""
	};
}
