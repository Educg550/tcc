import { ApprovalState } from "@/app/model/application-candidate";
import { DefaultCandidateFields } from "@/app/model/candidate-field";
import PagedCandidates from "@/app/model/paged-candidates";
import { useState } from "react";
import useSWR from "swr";

interface Props {
	processId: string | string[];
	onlyFavorites: boolean;
	stats?: ApprovalState;
}

// candidatos inscritos no edital
// * candidatos favoritos pelo professor
// * candidatos
const useSubmissionList = ({ onlyFavorites, processId, stats }: Props) => {
	const [selectedFields, setSelectedFields] = useState(
		DefaultCandidateFields,
	);

	const { data, isLoading, error, mutate } = useSWR<PagedCandidates>(
		onlyFavorites
			? `/${processId}/submissions/favorites/api`
			: `/${processId}/submissions/api?${stats ? `stats=${stats}` : ""}`,
	);

	return {
		data,
		isLoading,
		error,
		mutate,
		selectedFields,
	};
};

export default useSubmissionList;
