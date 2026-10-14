import * as React from "react";
import PagedCandidates from "../model/paged-candidates";
import { CandidateFieldProps } from "../model/candidate-field";
import {
	ApplicantItem,
	ApprovalState,
	BiddingState,
} from "../model/application-candidate";
import { MRT_Localization_PT_BR } from "material-react-table/locales/pt-BR";
import Phases from "../[processId]/models/phases";
import User, { isAdminRole, RolesUser } from "../model/user";

import {
	MaterialReactTable,
	useMaterialReactTable,
} from "material-react-table";
import { useEffect, useMemo, useState, useCallback } from "react";
import { Box, IconButton, Tooltip, useMediaQuery } from "@mui/material";
import { RestartAlt, Download } from "@mui/icons-material";
import theme from "../theme";
import { downloadCSV } from "@/lib/csv";

import useCandidateDetails from "../[processId]/submissions/[submissionId]/hooks/use-candidate-details";
import CandidateComments from "../[processId]/submissions/[submissionId]/components/CandidateComments";
import ActivitiesViewer, {
	ActivityViewerOptionsEnum,
} from "../[processId]/submissions/[submissionId]/components/ActivitiesViewer";

interface EnhancedTableProps {
	data: PagedCandidates;
	columns: CandidateFieldProps[];
	onToggleFavorite: (applicant: ApplicantItem) => void;
	onCandidateClick: (candidateId: string) => any;
	currentUser?: User;
	phase: string | undefined;
	setResetKey: React.Dispatch<React.SetStateAction<number>>;
	sidebarIsOpen?: boolean;
}

const sxBodyCellProps = {
	sx: {
		whiteSpace: "nowrap",
		overflow: "hidden",
		textOverflow: "ellipsis",
	},
};

const sxHeadCellProps = {
	sx: {
		whiteSpace: "nowrap",
		overflow: "hidden",
		textOverflow: "ellipsis",
		"& .Mui-TableHeadCell-Content-Wrapper": {
			whiteSpace: "nowrap",
			overflow: "hidden",
			textOverflow: "ellipsis",
			display: "flex",
			alignItems: "center",
			justifyContent: "space-between",
		},
		"& .Mui-TableHeadCell-Content-Wrapper button": {
			opacity: 0,
			visibility: "hidden",
			transition: "opacity 0.2s ease, visibility 0.2s ease",
		},
		"&:hover .Mui-TableHeadCell-Content-Wrapper button": {
			opacity: 1,
			visibility: "visible",
		},
	},
};

const sxHeadRowProps = {
	sx: {
		backgroundColor: "#f9fafb",
	},
};

const statsByPhase: Record<Phases, string[]> = {
	[Phases.avaliacao]: [
		ApprovalState.Approved,
		ApprovalState.Refused,
		ApprovalState.UnderReview,
		ApprovalState.Waitlist,
	],
	[Phases.homologacao]: [ApprovalState.Refused, ApprovalState.UnderReview],
	[Phases.inscricoes]: [],
	[Phases.encerrado]: [
		ApprovalState.Approved,
		ApprovalState.Refused,
		ApprovalState.UnderReview,
		ApprovalState.Waitlist,
	],
};

export default function CandidatesTable({
	data,
	columns,
	onToggleFavorite,
	onCandidateClick,
	currentUser,
	phase,
	setResetKey,
	sidebarIsOpen,
}: EnhancedTableProps) {
	const [pagination, setPagination] = useState(() => {
		const saved = localStorage.getItem("tablePagination_MRT");
		return saved ? JSON.parse(saved) : { pageIndex: 0, pageSize: 50 };
	});

	useEffect(() => {
		localStorage.setItem("tablePagination_MRT", JSON.stringify(pagination));
	}, [pagination]);

	const [sorting, setSorting] = useState(() => {
		const saved = localStorage.getItem("tableSort_MRT");
		return saved ? JSON.parse(saved) : [{ id: "stats", desc: false }];
	});

	useEffect(() => {
		localStorage.setItem("tableSort_MRT", JSON.stringify(sorting));
	}, [sorting]);

	const [columnFilters, setColumnFilters] = useState(() => {
		const saved = localStorage.getItem("tableFilters_MRT");
		return saved ? JSON.parse(saved) : [];
	});

	useEffect(() => {
		localStorage.setItem("tableFilters_MRT", JSON.stringify(columnFilters));
	}, [columnFilters]);

	const [columnVisibilityModel, setColumnVisibilityModel] = useState<
		Record<string, boolean>
	>(() => {
		const saved = localStorage.getItem("tableColumnVisibility_MRT");
		if (saved) return JSON.parse(saved);

		const model: Record<string, boolean> = {};
		columns.forEach((col: CandidateFieldProps) => {
			if (col.hasOwnProperty("columns")) {
				col["columns"]?.forEach((subcol: CandidateFieldProps) => {
					if (subcol.accessorKey) {
						model[subcol.accessorKey] = !!subcol.isSelected;
					}
				});
			} else if (col.accessorKey) {
				model[col.accessorKey] = !!col.isSelected;
			}
		});
		return model;
	});

	useEffect(() => {
		localStorage.setItem(
			"tableColumnVisibility_MRT",
			JSON.stringify(columnVisibilityModel),
		);
	}, [columnVisibilityModel]);

	const [rows, setRows] = React.useState<ApplicantItem[]>([]);
	useEffect(() => {
		setRows(data.candidates);
	}, [data.candidates, setRows]);

	const columnVisibilityByPhase: Record<Phases, String[]> = useMemo(() => {
		const biddingColumns = () => {
			if (isAdminRole((currentUser?.role as RolesUser) || undefined)) {
				return [
					BiddingState.AGREED,
					BiddingState.AVAILABLE,
					BiddingState.DECLINE,
					BiddingState.INTERESTED,
					BiddingState.INTERESTED_SCHOLARSHIP,
				];
			}
			return [];
		};
		return {
			[Phases.avaliacao]: [
				"isFavorite",
				"stats",
				"labels",
				...biddingColumns(),
			],
			[Phases.homologacao]: ["stats"],
			[Phases.inscricoes]: [],
			[Phases.encerrado]: ["stats", "labels", ...biddingColumns()],
		};
	}, [currentUser]);

	const resetTableState = useCallback(() => {
		const keys = [
			"tableSort_MRT",
			"tableFilters_MRT",
			"tableColumnVisibility_MRT",
			"tableOrder_MRT",
			"tablePagination_MRT",
		];

		keys.forEach((key) => localStorage.removeItem(key));

		setResetKey((prev) => prev + 1);
	}, [setResetKey]);

	useEffect(() => {
		if (phase) {
			setColumnVisibilityModel((prev) => ({
				...prev,
				isFavorite:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes(
						"isFavorite",
					),
				stats:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes("stats"),
				[BiddingState.AGREED]:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes(
						BiddingState.AGREED,
					),
				[BiddingState.AVAILABLE]:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes(
						BiddingState.AVAILABLE,
					),
				[BiddingState.DECLINE]:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes(
						BiddingState.DECLINE,
					),
				[BiddingState.INTERESTED]:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes(
						BiddingState.INTERESTED,
					),
				[BiddingState.INTERESTED_SCHOLARSHIP]:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes(
						BiddingState.INTERESTED_SCHOLARSHIP,
					),
				labels:
					columnVisibilityByPhase[phase as Phases] &&
					columnVisibilityByPhase[phase as Phases].includes("labels"),
			}));
		}
	}, [phase, setColumnVisibilityModel, columnVisibilityByPhase]);

	const columnsMemoized = React.useMemo<CandidateFieldProps[]>(
		() =>
			columns.map((col) => {
				col.minSize = col.minSize || 100;
				if (col.id == "candidate-process") {
					col.columns?.forEach((subcol) => {
						if (subcol.accessorKey == "stats") {
							subcol.accessorFn = (row) =>
								statsByPhase[phase as Phases];
						}
					});
				}
				if (col.columns) {
					return {
						...col,
						columns: col.columns.map((sub) => {
							if (sub.visibleInShowHideMenu == false) {
								return {
									...sub,
									visibleInShowHideMenu: (
										columnVisibilityByPhase[
											phase as Phases
										] ?? []
									).includes(sub.accessorKey ?? ""),
								};
							} else {
								return sub;
							}
						}),
					};
				}

				if (col.accessorKey && col.visibleInShowHideMenu == false) {
					return {
						...col,
						visibleInShowHideMenu: (
							columnVisibilityByPhase[phase as Phases] ?? []
						).includes(col.accessorKey),
					};
				}
				return col;
			}),
		[columns, phase, columnVisibilityByPhase],
	);

	const rowsWithActions = React.useMemo(() => {
		const toggleFavorite = (params: any) => {
			const rowId = params.row.id;
			setRows((prevRows) =>
				prevRows.map((row) =>
					row.id === rowId
						? { ...row, isFavorite: !row.isFavorite }
						: row,
				),
			);
			return onToggleFavorite(params.row.original);
		};

		return rows.map((row) => ({
			...row,
			toggleFavorite,
		}));
	}, [rows, onToggleFavorite]);

	const memoizedRowProps = React.useCallback(
		({ row }: any) => ({
			onClick: (event: any) => {
				onCandidateClick(row.original.id.toString());
			},
			sx: Object.assign(
				{},
				(() => {
					return { cursor: "pointer" };
				})(),
				(() => (phase === Phases.inscricoes ? {} : {}))(),
			),
		}),
		[onCandidateClick, phase],
	);

	const isXL = useMediaQuery(theme.breakpoints.up("xl"));

	const memoizedPaperProps = React.useCallback(
		({ table }: any) => ({
			style: {
				padding:
					table.getState().isFullScreen &&
					isXL &&
					sidebarIsOpen == true
						? "0 920px 0 0"
						: undefined,
			},
			elevation: 0,
			sx: {
				"& .MuiTableContainer-root": {
					border: "1px solid rgba(224, 224, 224, 1)",
					borderRadius: 1,
				},
			},
		}),
		[isXL, sidebarIsOpen],
	);

	const memoizedBottomToolbarProps = React.useCallback(
		({ table }: any) => ({
			style: {
				right:
					table.getState().isFullScreen &&
					isXL &&
					sidebarIsOpen == true
						? "920px"
						: undefined,
			},
		}),
		[isXL, sidebarIsOpen],
	);

	const handleExportRows = React.useCallback(() => {
		downloadCSV(rows, "rows.csv", [
			"token",
			"biddingUsers",
			"comments",
			"labels",
			"submittedDocs",
			"id",
		]);
	}, [rows]);

	const table = useMaterialReactTable({
		renderDetailPanel: ({ row }) => {
			return (
				<ActivitiesViewer
					submissionId={String(row.original.id)}
					currentUser={currentUser}
					activityViewerOption={
						ActivityViewerOptionsEnum.ALL_ACTIVITIES
					}
				></ActivitiesViewer>
			);
		},
		columns: columnsMemoized,
		data: rowsWithActions,
		state: {
			columnVisibility: columnVisibilityModel,
			pagination: pagination,
			sorting: sorting,
			columnFilters: columnFilters,
		},
		onPaginationChange: setPagination,
		onSortingChange: setSorting,
		onColumnVisibilityChange: setColumnVisibilityModel,
		onColumnFiltersChange: setColumnFilters,
		enableColumnResizing: true,
		muiPaginationProps: {
			rowsPerPageOptions: [5, 10, 50, 100],
		},
		localization: MRT_Localization_PT_BR,
		muiTableBodyRowProps: memoizedRowProps,
		muiTableBodyCellProps: sxBodyCellProps,
		muiTableHeadCellProps: sxHeadCellProps,
		muiTableHeadRowProps: sxHeadRowProps,
		muiTablePaperProps: memoizedPaperProps,
		muiBottomToolbarProps: memoizedBottomToolbarProps,
		renderTopToolbarCustomActions: () => (
			<Box
				sx={{
					display: "flex",
					gap: "16px",
					padding: "8px",
					flexWrap: "wrap",
				}}
			>
				<Tooltip title="Resetar modificadores">
					<IconButton onClick={resetTableState}>
						<RestartAlt />
					</IconButton>
				</Tooltip>
				{(() => {
					if (
						isAdminRole(
							(currentUser?.role as RolesUser) || undefined,
						)
					) {
						return (
							<Tooltip title="Download tabela">
								<IconButton onClick={handleExportRows}>
									<Download />
								</IconButton>
							</Tooltip>
						);
					}
					return <></>;
				})()}
			</Box>
		),
	});

	return (
		<Box className="tutorialDriver--datagrid">
			<MaterialReactTable table={table} />
		</Box>
	);
}
