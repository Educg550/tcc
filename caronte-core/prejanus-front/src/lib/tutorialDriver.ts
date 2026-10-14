"use client";
import { driver } from "driver.js";

export default function TutorialDriver() {
	const hasSeenTour = localStorage.getItem("tutorial-seen");
	if (hasSeenTour) return;

	const hoverTarget = document.querySelector(
		'.tutorialDriver--datagrid .MuiDataGrid-columnHeader[data-field="name"]',
	);
	const button = document.querySelector(".tutorialDriver--verticon__button");

	hoverTarget?.classList.add("Mui-hovered");
	hoverTarget
		?.querySelector(".MuiDataGrid-menuIcon")
		?.classList.add("MuiDataGrid-menuOpen");

	const tour = driver({
		showProgress: true,
		showButtons: ["next", "previous", "close"],
		animate: true,
		overlayColor: "rgba(0,0,0,0.7)",
		steps: [
			{
				element: ".tutorialDriver--tab__all",
				popover: {
					title: "Alterar forma de listagem",
					description:
						"Todos, favoritos (fase de avaliação), aprovados, reprovados, em análise e na lista de espera (fase de encerramento).",
				},
			},
			{
				element:
					".tutorialDriver--datagrid .MuiTableRow-head:nth-child(2) .MuiTableCell-head:nth-child(2)",
				popover: {
					title: "Coluna de dados [Nome]",
					description:
						"Possível realizar a ordenação e a filtragem específica por coluna, e também adicionar novas colunas para visualização.",
				},
			},
			{
				element:
					".tutorialDriver--datagrid tbody .MuiTableRow-root:nth-child(2)",
				popover: {
					title: "Submissão do candidato",
					description:
						"Possível visualizar com mais detalhes cada candidato.",
				},
				onHighlighted: () => {
					button?.dispatchEvent(
						new MouseEvent("click", {
							bubbles: true,
							cancelable: true,
						}),
					);
				},
			},
			{
				element: ".tutorialDriver--verticon .MuiMenu-list",
				popover: {
					title: "Mais opções para o edital",
				},
			},
		],
		onDestroyed: () => {
			hoverTarget?.classList.remove("Mui-hovered");
			hoverTarget
				?.querySelector(".MuiDataGrid-menuIcon")
				?.classList.remove("MuiDataGrid-menuOpen");
			localStorage.setItem("tutorial-seen", "true");
		},
	});

	tour.drive();
}
