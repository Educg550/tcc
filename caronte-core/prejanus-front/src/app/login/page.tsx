"use client";

import { useEffect } from "react";
import { useSnackbar } from "@/provider/messageContext";
import { Typography } from "@mui/material";
import { useUser } from "@/provider/UserProvider";

const Login = () => {
	const { showSnackbar } = useSnackbar();
	const { refreshUser } = useUser();
	const handleClick = () => {
		refreshUser();
		window.location.href = `${process.env.NEXT_PUBLIC_BASE_PATH}`;
	};

	useEffect(() => {
		const controller = new AbortController();
		const signal = controller.signal;

		let id: NodeJS.Timeout;

		fetch("login/api", {
			method: "GET",
			credentials: "include",
			signal,
		})
			.then((response) => {
				if (!response.ok) {
					throw new Error(`Erro na requisição: ${response.status}`);
				}
				return response.json();
			})
			.then((json) => {
				if (json.url) {
					const windowFeatures =
						"popup=true,status=NO, toolbar=NO, location=NO, directories=NO, resisable=NO, scrollbars=NO, top=10, left=10, width=1000, height=520";
					const popup = window.open(
						json.url,
						"senhaunica",
						windowFeatures,
					);

					if (
						!popup ||
						popup.closed ||
						typeof popup.closed === "undefined"
					) {
						console.error(
							"A janela popup foi bloqueada pelo navegador.",
						);
						return;
					}

					id = setInterval(() => {
						if (popup.closed) {
							handleClick();
							clearInterval(id);
						}
					}, 500);
					popup.onerror = () => {
						clearInterval(id);
					};
				} else {
					showSnackbar("Ocorreu uma falha", "error");
				}
			});

		return () => {
			controller.abort();
			if (id) clearInterval(id);
		};
	});

	return (
		<>
			<Typography variant="h4">Login</Typography>
			<Typography>
				Se o pop-up não abrir automaticamente, por favor recarregue a
				página e tente novamente.
			</Typography>
		</>
	);
};

export default Login;
