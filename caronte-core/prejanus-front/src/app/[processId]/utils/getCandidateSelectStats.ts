export default function getCandidateSelectStats(
	submissionId: number,
	stats: string,
	supervisorId?: number[],
): () => Promise<Response> {
	return () =>
		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${submissionId}/api/select`,
			{
				method: "POST",
				body: JSON.stringify({
					stats: stats,
					supervisorId: supervisorId,
				}),
			},
		);
}
