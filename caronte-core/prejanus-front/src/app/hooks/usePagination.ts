import { useState } from "react";
import { TEdict } from "../model/edict";

export type PaginationProps = {
	items: TEdict[];
	itemsPerPage: number;
};

const usePagination = ({ items, itemsPerPage }: PaginationProps) => {
	const [page, setPage] = useState<number>(1);

	const startIndex = (page - 1) * itemsPerPage;
	const endIndex = startIndex + itemsPerPage;
	const currentItems = items?.slice(startIndex, endIndex);

	const handlePageChange = (
		event: React.ChangeEvent<unknown>,
		value: number,
	) => {
		setPage(value);
	};

	return {
		page,
		handlePageChange,
		currentItems,
	};
};

export default usePagination;
