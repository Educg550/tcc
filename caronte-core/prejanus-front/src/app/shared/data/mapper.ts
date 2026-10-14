import InfoField from "@/app/shared/model/info-field";
import ApplicantDto, {
	CommentType,
	SentStatus,
	UserDto,
} from "@/app/submissions/[submissionId]/api/dto/applicant-dto";
import { getDaysFromDate } from "@/app/submissions/[submissionId]/api/utils";
import User from "@/app/model/user";
import ApplicationCandidate, {
	CandidateDocument,
} from "@/app/model/application-candidate";
import Comment from "@/app/model/comment";
import { sentLabels } from "@/app/[processId]/mappers/applicant";

export function userFromDto(dto: UserDto): User {
	return { id: dto.id, name: dto.name, email: dto.email, role: dto.role };
}

export default function applicantDtoToModel(
	dto: ApplicantDto,
): ApplicationCandidate {
	const personalInfo = personalInfoFromApplicantDto(dto);
	const applicationInfo = applicationInfoFromApplicantDto(dto);
	const recommendersInfo = recommendersInfoApplicantDto(dto);
	const acceptInfo = acceptInfoApplicantDto(dto);
	const comments = commentsFromDto(dto);
	const documents = documentsFromDto(dto);

	return {
		id: dto?.id,
		name: dto?.name,
		email: dto?.email,
		personalInfo: personalInfo,
		lattesCurriculum: dto?.lattes_curriculum,
		personalWebsite: dto?.personal_website,
		applicationInfo: applicationInfo,
		submittedDocs: documents,
		recommendersInfo: recommendersInfo,
		acceptInfo: acceptInfo,
		comments: comments,
		applicationDate: new Date(dto.application_date),
		isFavorite: !!dto?.is_favorite,
		stats: dto?.stats,
		userBidding: dto?.user_bidding,
		privateNotes: dto?.private_note,
		labels: dto?.labels,
		biddingUsers: dto?.bidding_users?.data,
		entrySemester: dto?.entry_semester,
		letterSent: dto?.letter_sent,
	};
}

export function documentsFromDto(dto: ApplicantDto): CandidateDocument[] {
	return (
		dto.documents
			?.map((doc) => ({
				title: doc.title,
				url: doc.url,
				label: doc.label,
			}))
			?.filter((doc) => !!doc.url) ?? []
	);
}

export function commentsFromDto(dto: ApplicantDto): Comment[];
export function commentsFromDto(comments: ApplicantDto["comments"]): Comment[];

export function commentsFromDto(
	input: ApplicantDto | ApplicantDto["comments"],
): Comment[] {
	const comments: ApplicantDto["comments"] = Array.isArray(input)
		? input
		: input.comments;

	return (
		comments
			?.map((comment) => {
				if (
					comment.type === CommentType.Comment ||
					comment.type === CommentType.ExternalComment ||
					comment.type === CommentType.Custom
				) {
					return {
						id: comment.id,
						user: userFromDto(comment.user),
						text: comment.comment,
						postedWhenTime: new Date(comment.created_at),
						postedWhen: getDaysFromDate(comment.created_at),
						type: comment.type,
					};
				} else if (comment.type === CommentType.Favorite) {
					return {
						id: comment.id,
						user: userFromDto(comment.user),
						text: `Favoritado por ${comment.user.name}`,
						postedWhenTime: new Date(comment.created_at),
						postedWhen: getDaysFromDate(comment.created_at),
						type: CommentType.Favorite,
					};
				} else if (comment.type === CommentType.Interest) {
					return {
						id: comment.id,
						user: userFromDto(comment.user),
						text: `Interessado por ${comment.user.name}`,
						postedWhenTime: new Date(comment.created_at),
						postedWhen: getDaysFromDate(comment.created_at),
						type: CommentType.Interest,
					};
				} else if (comment.type === CommentType.Advisor) {
					return {
						id: comment.id,
						user: userFromDto(comment.user),
						text: `Selecionado para ${comment.user.name}`,
						postedWhenTime: new Date(comment.created_at),
						postedWhen: getDaysFromDate(comment.created_at),
						type: CommentType.Advisor,
					};
				}
			})
			.filter((v): v is Comment => v !== undefined) ?? []
	)
		.sort((a, b) => {
			if (!a || !b) return 0;
			return a.postedWhenTime < b.postedWhenTime ? -1 : 1;
		})
		.filter(Boolean);
}

export function acceptInfoApplicantDto(dto: ApplicantDto) {
	const acceptInfo: InfoField[] = [
		{
			name: "accept.sent",
			label: "Situação",
			value: sentLabels[dto.accept.sent],
		},
	];
	if (dto.accept.sent == SentStatus.REPLIED) {
		acceptInfo.push({
			name: "accept.accept",
			label: "Candidatura aceita?",
			value: String(dto.accept.accept),
		});
		acceptInfo.push({
			name: "accept.comments",
			label: "Observações adicionais sobre a escolha",
			value: String(dto.accept.comments),
		});
	}

	return acceptInfo;
}

export function recommendersInfoApplicantDto(dto: ApplicantDto) {
	const recommendersInfo: InfoField[][] = [];
	dto.recommenders.forEach((recommender) => {
		if (recommender.email || recommender.fullname) {
			const recommenderInfo = [
				{
					name: "recommender.fullname",
					label: "Nome completo",
					value: String(recommender.fullname),
				},
				{
					name: "recommender.sent",
					label: "Não Enviado",
					value: String(recommender.sent),
				},
				{
					name: "recommender.email",
					label: "E-mail",
					value: String(recommender.email),
				},
			];
			if (recommender.affiliation) {
				recommenderInfo.push({
					name: "recommender.affiliation",
					label: "Afiliação e posição atual",
					value: String(recommender.affiliation),
				});
			}
			if (recommender.known_time) {
				recommenderInfo.push({
					name: "recommender.known_time",
					label: "Há quanto tempo conhece o candidato?",
					value: String(recommender.known_time),
				});
			}
			if (recommender.relationship) {
				recommenderInfo.push({
					name: "recommender.relationship",
					label: "Em quais contextos o conheceu?",
					value: String(recommender.relationship),
				});
			}
			if (recommender.rating) {
				recommenderInfo.push({
					name: "recommender.rating",
					label: "Avaliação do candidato",
					value: String(recommender.rating),
				});
			}
			recommendersInfo.push(recommenderInfo);
		}
	});
	return recommendersInfo;
}

export function personalInfoFromApplicantDto(dto: ApplicantDto) {
	const personalInfo: InfoField[] = [
		{
			name: "graduation.year",
			label: "Ano de graduação",
			value: String(dto?.graduation.year),
		},
		{
			name: "graduation.institution",
			label: "Instituição de ensino da graduação",
			value: dto?.graduation?.institution,
		},
		{
			name: "graduation.country",
			label: "País da instituição de ensino da graduação",
			value: dto?.graduation?.country,
		},
		{
			name: "graduation.course",
			label: "Curso de ensino da graduação",
			value: dto?.graduation?.course,
		},
		{ name: "nationality", label: "Nacionalidade", value: dto.nationality },
		{
			name: "gender",
			label: "Gênero",
			value: FormattedGender[dto?.gender] ?? dto?.gender,
		},
		{
			name: "birth_date",
			label: "Data de nascimento",
			value: new Date(dto.birth_date).toLocaleDateString(undefined, {
				year: "numeric",
				month: "2-digit",
				day: "2-digit",
			}),
		},
		{
			name: "phone_number",
			label: "Telefone",
			value: String(dto?.phone_number),
		},
	];

	if (dto.relevant_information)
		personalInfo.push({
			name: "relevant_information",
			label: "Informações relevantes",
			value: dto?.relevant_information,
		});

	if (dto.current_occupation)
		personalInfo.push({
			name: "current_occupation",
			label: "Atividade remunerada atual",
			value: dto?.current_occupation,
		});

	if (dto.poscomp) {
		personalInfo.push({
			name: "poscomp.score",
			label: "Nota no POSCOMP",
			value: String(dto?.poscomp?.score),
		});
		personalInfo.push({
			name: "poscomp.year",
			label: "Ano de realização da POSCOMP",
			value: String(dto?.poscomp?.year),
		});
	}
	if (dto.disabilities) {
		personalInfo.push({
			name: "disabilities",
			label: "Pessoa portadora de deficiência",
			value: dto?.disabilities ? "Sim" : "Não",
		});
	}
	if (dto?.ethnicity_race) {
		personalInfo.push({
			name: "ethnicity_race",
			label: "Autoidentificação como pessoa preta, parda ou indígena (PPI)",
			value: dto.ethnicity_race ? "Sim" : "Não",
		});
	}

	return personalInfo;
}

function applicationInfoFromApplicantDto(dto: ApplicantDto): InfoField[] {
	return [
		{
			name: "research.program",
			label: "Programa",
			value: dto.research.program,
		},
		{
			name: "research.field",
			label: "Área de interesse primária",
			value: dto.research.field.primary,
		},
		{
			name: "research.field",
			label: "Área de interesse secundária",
			value: dto.research.field.secondary,
		},
		{
			name: "research.dedication_level",
			label: "Grau de dedicação",
			value:
				FormattedDedicationLevel[dto.research.dedication_level] ??
				dto.research.dedication_level,
		},
		{
			name: "research.semester",
			label: "Semestre",
			value: dto.research.semester,
		},
		{
			name: "research.will_apply_scholarship",
			label: "Concorrerá a bolsa de estudos",
			value: dto.research.will_apply_scholarship ? "Sim" : "Não",
		},
	];
}

const FormattedGender: { [gender: string]: string } = {
	CIS_MALE: "Homem cisgênero",
	TRANS_MALE: "Homem transgênero",
	CIS_FEMALE: "Mulher cisgênero",
	TRANS_FEMALE: "Mulher transgênero",
};

const FormattedDedicationLevel: { [level: string]: string } = {
	PARTIAL: "Parcial",
	FULL: "Integral",
};
