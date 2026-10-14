import { Link } from "@mui/material";

export function CandidateLink(param: any) {
	return param.cell.getValue() ? (
		<Link href={param.cell.getValue()} target="_blank" color="secondary">
			Abrir
		</Link>
	) : (
		<>N/A</>
	);
}

export function formatBoolean(param: any) {
	return param.cell.getValue() ? "Sim" : "Não";
}
