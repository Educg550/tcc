import { List, Pagination } from "@mui/material";
import { TEdict } from "../model/edict";
import EdictItem from "./edict-item";

export type EdictListProps = {
	filteredEdicts?: TEdict[];
	edictsCount: number;
	page: number;
	handlePageChange: (
		event: React.ChangeEvent<unknown>,
		value: number,
	) => void | undefined;
	handleClickEdict: (id: number) => void;
	itemsPerPage: number;
};

export default function EdictList({
	filteredEdicts,
	page,
	edictsCount,
	itemsPerPage,
	handlePageChange,
	handleClickEdict,
}: EdictListProps) {
	const amount_pages = Math.ceil(edictsCount / itemsPerPage);
	return (
		<>
			<List>
				{filteredEdicts?.map((process, i) => (
					<EdictItem
						handleClickEdict={handleClickEdict}
						key={i}
						edict={process}
					/>
				))}
			</List>
			{amount_pages > 1 ? (
				<Pagination
					sx={{
						display: "flex",
						justifyContent: "center",
					}}
					count={amount_pages}
					page={page}
					onChange={handlePageChange}
				/>
			) : (
				<></>
			)}
		</>
	);
}
