import EdictsListPage from "@/app/components/edict-list-page";
import LandingPage from "./components/landing-page";
import { Metadata } from "next";
import { getCurrentUser } from "@/lib/getCurrentUser";

export async function generateMetadata(): Promise<Metadata> {
	const user = await getCurrentUser();
	return { title: user === null ? null : "Editais" };
}

//Render while fetch vs fetch on render
export default async function HomePage() {
	const user = await getCurrentUser();

	return user === null ? <LandingPage /> : <EdictsListPage />;
}
