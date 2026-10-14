import useSWR from "swr";
import User from "@/app/model/user";
import { useSnackbar } from "@/provider/messageContext";
import { TProcess } from "@/app/[processId]/models/process";
import Label from "@/app/model/label";
import UserInfo from "@/app/model/user-info";

export default function useUserInformations(submissionId?: string | string[]): {
	data?: UserInfo;
	error: boolean;
	isLoading: boolean;
} {
	const { showSnackbar } = useSnackbar();

	const { data, error, isLoading, mutate } = useSWR<UserInfo>(
		submissionId ? `/submissions/${submissionId}/api/label/get-all` : null,
		{ keepPreviousData: true },
	);

	return {
		data: data,
		error: !!error,
		isLoading: isLoading,
	};
}
