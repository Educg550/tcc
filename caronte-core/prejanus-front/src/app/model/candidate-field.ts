import {
	CandidateLink,
	formatBoolean,
} from "@/app/components/applicant-field-value";
import FavoriteButton from "../components/favorite-button";
import { formattedDate } from "../submissions/[submissionId]/api/utils";
import ChipLabel from "../components/chip-label";
import SelectStats from "../components/select-stats";
import {
	ApplicantItem,
	ApprovalState,
	BiddingState,
} from "./application-candidate";
import {
	approvalLabels,
	biddingLabels,
} from "../[processId]/mappers/applicant";
import ChipPerfil from "../components/chip-perfil";
import { MRT_ColumnDef } from "material-react-table";
import User from "./user";
import CheckboxItem from "../components/checkbox-item";

export default interface CandidateField {
	label: string;
	isSelected: boolean;
}

export type CandidateFieldProps = MRT_ColumnDef<ApplicantItem> & {
	isSelected?: boolean;
	columns?: (MRT_ColumnDef<ApplicantItem> & {
		isSelected?: boolean;
	})[];
};

export const DefaultCandidateFields: CandidateFieldProps[] = [
	{
		accessorKey: "isFavorite",
		header: "Favorito",
		enableSorting: false,
		enableColumnFilter: false,
		enableHiding: false,
		Cell: FavoriteButton,
		enableResizing: false,
		size: 100,
		visibleInShowHideMenu: false,
		accessorFn: (row) => {
			return { applicant: row, isFavorite: row.isFavorite };
		},
	},
	{
		accessorKey: "labels",
		header: "Rótulos",
		size: 150,
		enableHiding: false,
		Cell: ChipLabel,
		accessorFn: (row) => row.labels.map((label) => label.label),
	},
	{
		id: "candidate-info",
		header: "Informações do Candidato",
		columns: [
			{
				accessorKey: "name",
				header: "Nome",
				size: 150,
				isSelected: true,
			},
			{
				accessorKey: "email",
				header: "E-mail",
				enableClickToCopy: true,
				size: 300,
			},
			{
				accessorKey: "lattesCurriculum",
				header: "Lattes",
				enableSorting: false,
				enableColumnFilter: false,
				Cell: CandidateLink,
				size: 100,
			},
			{
				accessorKey: "graduationInstitution",
				header: "Instituição de graduação",
				size: 200,
				accessorFn: (row) => row.graduation.institution,
				isSelected: true,
			},
			{
				accessorKey: "graduationCourse",
				header: "Curso de graduação",
				size: 200,
				accessorFn: (row) => row.graduation.course,
				isSelected: true,
			},
			{
				accessorKey: "researchFieldPrimary",
				header: "Campo de pesquisa primário",
				size: 200,
				accessorFn: (row) => row.research.field.primary,
				isSelected: true,
			},
			{
				accessorKey: "nationality",
				header: "Nacionalidade",
			},
			{
				accessorKey: "personalWebsite",
				header: "Site pessoal",
				enableColumnFilter: false,
			},
			{
				accessorKey: "gender",
				header: "Gênero",
			},
			{
				accessorKey: "phoneNumber",
				header: "Telefone",
			},
			{
				accessorKey: "birthDate",
				header: "Data de nascimento",
				size: 150,
				accessorFn: (row) => formattedDate(row.birthDate),
			},
			{
				accessorKey: "graduationCountry",
				header: "País de graduação",
				accessorFn: (row) => row.graduation.country,
			},
			{
				accessorKey: "graduationYear",
				header: "Ano de graduação",
				accessorFn: (row) => row.graduation.year,
			},
			{
				accessorKey: "poscompYear",
				header: "POSCOMP - Ano",
				accessorFn: (row) => row.poscomp?.year,
			},
			{
				accessorKey: "poscompScore",
				header: "POSCOMP - Nota",
				accessorFn: (row) => row.poscomp?.score,
			},
			{
				accessorKey: "currentOccupation",
				header: "Ocupação",
				size: 150,
			},
			{
				accessorKey: "researchFieldSecondary",
				header: "Campo de pesquisa secundário",
				size: 200,
				accessorFn: (row) => row.research.field.secondary,
			},
			{
				accessorKey: "researchSemester",
				header: "Semestre",
				accessorFn: (row) => row.research.semester,
			},
			{
				accessorKey: "researchWillApplyScholarship",
				header: "Aplicar para bolsa",
				accessorFn: (row) => row.research.willApplyScholarship,
				Cell: formatBoolean,
			},
			{
				accessorKey: "researchDedicationLevel",
				header: "Dedicação",
				accessorFn: (row) => row.research.dedicationLevel,
			},
			{
				accessorKey: "disabilities",
				header: "Pessoa portadora de deficiência",
				accessorFn: (row) => row.disabilities,
				Cell: CheckboxItem,
				filterVariant: "select",
				filterSelectOptions: [
					{ label: "Sim", value: true },
					{ label: "Não", value: false },
				],
				filterFn: (row, id, filterValue) => {
					if (filterValue === undefined) return true;
					return (
						(row.getValue(id) as boolean).toString() ===
						(filterValue as boolean).toString()
					);
				},
			},
			{
				accessorKey: "ethnicityRace",
				header: "Autoidentificação como pessoa preta, parda ou indígena (PPI)",
				accessorFn: (row) => row.ethnicityRace,
				Cell: CheckboxItem,
				filterVariant: "select",
				filterSelectOptions: [
					{ label: "Sim", value: true },
					{ label: "Não", value: false },
				],
				filterFn: (row, id, filterValue) => {
					if (filterValue === undefined) return true;
					return (
						(row.getValue(id) as boolean).toString() ===
						(filterValue as boolean).toString()
					);
				},
			},
		],
	},
	{
		id: "candidate-process",
		header: "Processo do Candidato",
		columns: [
			{
				accessorKey: BiddingState.AGREED,
				header: `${biddingLabels[BiddingState.AGREED]}`,
				accessorFn: (row) => row.biddingUsers[BiddingState.AGREED],
				Cell: ChipPerfil,
				visibleInShowHideMenu: false,
				enableColumnFilter: false,
				sortingFn: (rowA, rowB, columnId) => {
					const v1: User[] = rowA.getValue(columnId);
					const v2: User[] = rowB.getValue(columnId);
					if (v1.length < v2.length) return -1;
					if (v1.length > v2.length) return 1;
					return 0;
				},
			},
			{
				accessorKey: BiddingState.INTERESTED_SCHOLARSHIP,
				header: `${biddingLabels[BiddingState.INTERESTED_SCHOLARSHIP]}`,
				accessorFn: (row) =>
					row.biddingUsers[BiddingState.INTERESTED_SCHOLARSHIP],
				Cell: ChipPerfil,
				visibleInShowHideMenu: false,
				enableColumnFilter: false,
				sortingFn: (rowA, rowB, columnId) => {
					const v1: User[] = rowA.getValue(columnId);
					const v2: User[] = rowB.getValue(columnId);
					if (v1.length < v2.length) return -1;
					if (v1.length > v2.length) return 1;
					return 0;
				},
			},
			{
				accessorKey: BiddingState.INTERESTED,
				header: `${biddingLabels[BiddingState.INTERESTED]}`,
				accessorFn: (row) => row.biddingUsers[BiddingState.INTERESTED],
				Cell: ChipPerfil,
				visibleInShowHideMenu: false,
				enableColumnFilter: false,
				sortingFn: (rowA, rowB, columnId) => {
					const v1: User[] = rowA.getValue(columnId);
					const v2: User[] = rowB.getValue(columnId);
					if (v1.length < v2.length) return -1;
					if (v1.length > v2.length) return 1;
					return 0;
				},
			},
			{
				accessorKey: BiddingState.AVAILABLE,
				header: `${biddingLabels[BiddingState.AVAILABLE]}`,
				accessorFn: (row) => row.biddingUsers[BiddingState.AVAILABLE],
				Cell: ChipPerfil,
				visibleInShowHideMenu: false,
				enableColumnFilter: false,
				sortingFn: (rowA, rowB, columnId) => {
					const v1: User[] = rowA.getValue(columnId);
					const v2: User[] = rowB.getValue(columnId);
					if (v1.length < v2.length) return -1;
					if (v1.length > v2.length) return 1;
					return 0;
				},
			},
			{
				accessorKey: BiddingState.DECLINE,
				header: `${biddingLabels[BiddingState.DECLINE]}`,
				accessorFn: (row) => row.biddingUsers[BiddingState.DECLINE],
				Cell: ChipPerfil,
				visibleInShowHideMenu: false,
				enableColumnFilter: false,
				sortingFn: (rowA, rowB, columnId) => {
					const v1: User[] = rowA.getValue(columnId);
					const v2: User[] = rowB.getValue(columnId);
					if (v1.length < v2.length) return -1;
					if (v1.length > v2.length) return 1;
					return 0;
				},
			},
			{
				accessorKey: "stats",
				header: "Status",
				size: 200,
				Cell: SelectStats,
				visibleInShowHideMenu: false,
				sortingFn: (rowA, rowB, columnId) => {
					const v1: string = rowA.original.stats.toLowerCase();
					const v2: string = rowB.original.stats.toLowerCase();
					const orderByStats: Record<string, number> = {
						[ApprovalState.UnderReview]: 0,
						[ApprovalState.Approved]: 1,
						[ApprovalState.Waitlist]: 2,
						[ApprovalState.Refused]: 3,
					};

					if (orderByStats[v1] < orderByStats[v2]) return -1;
					if (orderByStats[v1] > orderByStats[v2]) return 1;
					return 0;
				},
				filterFn: (row, id, filterValue) => {
					const value =
						approvalLabels[
							row.original.stats.toLowerCase() as ApprovalState
						] || "";
					return value
						.toLowerCase()
						.startsWith(filterValue.toLowerCase());
				},
			},
			{
				accessorKey: "acceptInfo",
				header: "Informações sobre a vaga",
				isSelected: false,
			},
		],
	},
];
