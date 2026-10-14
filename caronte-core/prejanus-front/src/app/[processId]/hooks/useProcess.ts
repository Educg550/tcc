import { ChangeEvent, useState } from "react";
import { TProcess } from "../models/process";
import useSWR from "swr";
import { useRouter } from "next/navigation";
import { useSnackbar } from "@/provider/messageContext";

interface Props {
	processId: string | string[];
}

const useProcess = ({ processId }: Props) => {
	const [selectedSections, setSelectedSections] = useState<string[]>([]);
	const [inLoadingDownloadData, setLoadingDownloadData] = useState(false);
	const [inLoadingDownloadPairing, setLoadingDownloadPairing] =
		useState(false);
	const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
		const { value, checked } = event.target;
		if (checked) {
			setSelectedSections([...selectedSections, value]);
		} else {
			setSelectedSections(selectedSections.filter((v) => v !== value));
		}
	};
	const { data, error, isLoading, mutate } = useSWR<TProcess>(
		`/${processId}/api`,
		{ keepPreviousData: true },
	);
	const router = useRouter();
	const { showSnackbar } = useSnackbar();

	const sections = [
		{ id: "general_statistics", label: "Mostrar estatísticas" },
		{ id: "list_of_advisors", label: "Listar orientadores" },
		{ id: "relation", label: "Listar relação" },
		{ id: "approved", label: "Listar aprovados" },
		{ id: "refused", label: "Listar recusados/lista de espera" },
		{ id: "underreview", label: "Listar em análise" },
		{ id: "show_emails", label: "Mostrar e-mails" },
	];

	const [isAdvancingPhaseEdict, setAdvancingPhaseEdict] = useState(false);
	function handleAdvancePhaseEdict(phaseId: string) {
		setAdvancingPhaseEdict(true);
		fetch(`${processId}/api/advance-phase`, {
			method: "POST",
			body: JSON.stringify({ id: phaseId }),
			headers: {
				"Content-Type": "application/json",
			},
		})
			.then((response) => {
				if (!response.ok) throw response;
				return response.json();
			})
			.then((phase) => {
				mutate({ ...data!, phase: phase.label }, false);
				setAdvancingPhaseEdict(false);
			})
			.catch(async (error) => {
				const errorData = await error.json();
				if (errorData) {
					showSnackbar(
						errorData.message || errorData.detail,
						"error",
					);
				}
				setAdvancingPhaseEdict(false);
			});
	}

	const [isHandleSlotsEdict, setHandleSlotsEdict] = useState(false);
	function handleSlotsEdict(slots: string) {
		setHandleSlotsEdict(true);
		fetch(`${processId}/api/set-slots`, {
			method: "POST",
			body: JSON.stringify({ amount: slots }),
			headers: {
				"Content-Type": "application/json",
			},
		})
			.then((response) => {
				if (!response.ok) throw response;
				return response.json();
			})
			.then((slots) => {
				mutate({ ...data!, slots: slots.amount }, false);
				setHandleSlotsEdict(false);
			})
			.catch(async (error) => {
				const errorData = await error.json();
				if (errorData) {
					showSnackbar(
						errorData.message || errorData.detail,
						"error",
					);
				}
				setHandleSlotsEdict(false);
			});
	}

	function removeEdict() {
		fetch(`api/remove`, {
			method: "DELETE",
		}).then(() => {
			router.push("/");
		});
	}

	async function interactorEdictDownload() {
		setLoadingDownloadData(true);
		const bodyJson: Record<string, boolean> = {};
		selectedSections.forEach((selectedSection) => {
			bodyJson[selectedSection] = true;
		});
		const jobId = await fetch(`${processId}/api/data?mode=pdf`, {
			method: "POST",
			body: JSON.stringify(bodyJson),
		})
			.then((res) => res.json())
			.then((data) => data.job_id);

		let pdfBlob = null;
		let amountRequest = 0;
		while (!pdfBlob) {
			await new Promise((r) => setTimeout(r, 3000));
			pdfBlob = await fetch(
				`${processId}/api/download_pdf/${jobId}`,
			).then((res) => {
				if (res.status === 404) return null;
				return res.blob();
			});
			amountRequest++;
			if (amountRequest > 10) {
				showSnackbar("Erro ao carregar o pdf", "error");
				throw new Error("");
			}
		}

		const url = URL.createObjectURL(pdfBlob);
		const link = document.createElement("a");
		link.href = url;
		link.download = `relatorio_${processId}.pdf`;
		link.click();
		URL.revokeObjectURL(url);
		setLoadingDownloadData(false);
	}

	async function pairingBiddingsDownload() {
		setLoadingDownloadPairing(true);
		const jobId = await fetch(`${processId}/api/pairing-biddings`, {
			method: "POST",
		})
			.then((res) => res.json())
			.then((data) => data.job_id);

		let csvBlob = null;
		let amountRequest = 0;
		while (!csvBlob) {
			await new Promise((r) => setTimeout(r, 3000));
			csvBlob = await fetch(
				`${processId}/api/download-csv/${jobId}`,
			).then((res) => {
				if (res.status === 404) return null;
				return res.blob();
			});
			amountRequest++;
			if (amountRequest > 10) {
				showSnackbar("Erro ao carregar o csv", "error");
				throw new Error("");
			}
		}

		const url = URL.createObjectURL(csvBlob);
		const link = document.createElement("a");
		link.href = url;
		link.download = `pairing_biddings_${processId}.csv`;
		link.click();
		URL.revokeObjectURL(url);
		setLoadingDownloadPairing(false);
	}

	return {
		data,
		isLoading,
		error,
		mutate,
		isAdvancingPhaseEdict,
		handleAdvancePhaseEdict,
		isHandleSlotsEdict,
		handleSlotsEdict,
		removeEdict,
		interactorEdictDownload,
		pairingBiddingsDownload,
		sections: {
			sections,
			selectedSections,
			handleChange,
		},
		inLoadingDownloadData,
		inLoadingDownloadPairing,
	};
};

export default useProcess;
