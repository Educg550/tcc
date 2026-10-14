import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { TEdict } from "../model/edict";
import usePagination, { PaginationProps } from "./usePagination";

type Props = {
	itemsPerPage: number;
};

const useEdict = ({ itemsPerPage }: Props) => {
	const [hasError, setHasError] = useState(false);
	const [isAllProgramsOpen, setIsAllProgramsOpen] = useState<boolean>(true);

	const router = useRouter();
	const handleClickEdict = (id: number) => {
		router.push(`/${id}`);
	};

	const handleCreateEdictClick = () => {
		router.push("/edicts");
	};

	const { data: edicts, error, mutate } = useSWR<TEdict[]>("/edicts/api");

	useEffect(() => {
		if (error) setHasError(true);
	}, [error]);

	const filteredEdicts = useMemo(() => {
		if (edicts && edicts.length)
			return edicts.filter((edict) =>
				isAllProgramsOpen ? true : edict.isOpen,
			);
	}, [edicts, isAllProgramsOpen]);

	const { currentItems, handlePageChange, page } = usePagination({
		items: filteredEdicts,
		itemsPerPage,
	} as PaginationProps);

	return {
		currentItems,
		page,
		filteredEdicts,
		isAllProgramsOpen,
		isLoading: !hasError && !edicts,
		isError: hasError,
		setIsAllProgramsOpen,
		handlePageChange,
		handleClickEdict,
		handleCreateEdictClick,
		mutate,
	};
};

export default useEdict;
