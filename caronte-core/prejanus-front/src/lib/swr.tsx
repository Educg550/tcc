"use client";

import { SWRConfig } from "swr";
import { JSX, useCallback } from "react";
import clearSession from "@/app/shared/session/clearSession";
import { useSnackbar } from "@/provider/messageContext";
import { useUser } from "@/provider/UserProvider";

export const SWRProvider = ({ children }: { children: JSX.Element }) => {
	const { showSnackbar } = useSnackbar();
	const { setUser } = useUser();

	const fetcher = useCallback(
		async (url: string) => {
			const res = await fetch(
				`${process.env.NEXT_PUBLIC_BASE_PATH}${url}`,
			);
			if (res.status === 401) {
				setUser(undefined);
				showSnackbar(
					"Sua sessão expirou ou é necessário realizar login para acessar essa página",
					"error",
				);
				await clearSession();

				const error = new Error("Unauthorized");
				(error as any).status = 401;
				throw error;
			}

			if (!res.ok) {
				const error = new Error(res.statusText);
				(error as any).info = await res.json().catch(() => null);
				(error as any).status = res.status;
				throw error;
			}

			return res.json();
		},
		[showSnackbar, setUser],
	);
	return (
		<SWRConfig
			value={{
				fetcher: fetcher,
			}}
		>
			{children}
		</SWRConfig>
	);
};
