import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v14-appRouter";
import { ThemeProvider } from "@mui/material/styles";
import theme from "./theme";
import Header from "@/components/Header";
import { SWRProvider } from "@/lib/swr";
import { Box } from "@mui/material";
import { SnackbarProvider } from "@/provider/messageContext";
import { UserProvider } from "@/provider/UserProvider";

const roboto = Roboto({
	weight: ["500", "700"],
	subsets: ["latin"],
	display: "swap",
	variable: "--font-roboto",
});

export const metadata: Metadata = {
	title: {
		default: "Prejanus",
		template: "%s | Prejanus",
	},
	description: "Sistema de seleção da pós-graduação do ime",
	icons: {
		icon: `${process.env.NEXT_PUBLIC_BASE_PATH}/favicon.ico`,
	},
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="pt-br" className={roboto.variable}>
			<body
				style={{
					overscrollBehaviorX: "contain",
				}}
			>
				<AppRouterCacheProvider>
					<ThemeProvider theme={theme}>
						<SnackbarProvider>
							<UserProvider>
								<Header />
								<SWRProvider>
									<Box
										sx={{
											display: "flex",
											flexDirection: "column",
											padding: 4,
											paddingBottom: 8,
											width: 1,
											height: "100vh",
										}}
									>
										{children}
									</Box>
								</SWRProvider>
							</UserProvider>
						</SnackbarProvider>
					</ThemeProvider>
				</AppRouterCacheProvider>
			</body>
		</html>
	);
}
