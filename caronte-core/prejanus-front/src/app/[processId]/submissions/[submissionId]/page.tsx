"use client";

import CandidateDetailsPage from "@/app/[processId]/submissions/[submissionId]/candidate-details-page";
import { useUser } from "@/provider/UserProvider";

export default function Page() {
	const { user } = useUser();

	return <CandidateDetailsPage currentUser={user} />;
}
