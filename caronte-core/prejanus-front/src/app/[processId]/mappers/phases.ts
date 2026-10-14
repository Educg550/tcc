import Phases from "../models/phases";

const phases_labels: Record<Phases, string> = {
	[Phases.inscricoes]: "Inscrições",
	[Phases.homologacao]: "Homologação",
	[Phases.avaliacao]: "Avaliação",
	[Phases.encerrado]: "Encerrado",
};

export function LabelPhase(phase_type: Phases) {
	const phase_label = Object.keys(phases_labels).find((key) => {
		if (phase_type) return phase_type.startsWith(key);
		else return false;
	});
	return phases_labels[phase_label as Phases];
}
