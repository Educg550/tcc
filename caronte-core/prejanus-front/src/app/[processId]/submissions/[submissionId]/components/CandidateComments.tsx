import Phases from "@/app/[processId]/models/phases";
import LockOpenIcon from "@mui/icons-material/LockOpen";
import { Button, Stack, TextField, Tooltip, Typography } from "@mui/material";
import { useCallback, useState } from "react";
import SendIcon from "@mui/icons-material/Send";
import User, { isAdminRole, RolesUser } from "@/app/model/user";
import { TProcess } from "@/app/[processId]/models/process";
import { useSWRConfig } from "swr";
import { useSnackbar } from "../../../../../provider/messageContext";
import useComments from "@/app/hooks/useComments";

interface Props {
	currentUser?: User;
	submissionId: string;
	processData?: TProcess;
	handleReesendInformationsSend: (comment: string) => void;
}

export default function CandidateComments({
	submissionId,
	currentUser,
	processData,
	handleReesendInformationsSend,
}: Props) {
	const [comment, setComment] = useState("");
	const { showSnackbar } = useSnackbar();
	const {
		addComment,
		deleteComment,
		comments,
		error,
		isLoading,
		mutate,
		isAddingComment,
	} = useComments(submissionId);

	const handleCommentChange = useCallback(
		(e: { target: { value: React.SetStateAction<string> } }) => {
			setComment(e.target.value);
		},
		[],
	);

	if (!currentUser || !processData) return <></>;

	if (processData.phase === Phases.avaliacao) {
		return (
			<Stack
				component="form"
				noValidate
				autoComplete="off"
				direction="column"
				sx={{ alignItems: "start", gap: 1, py: 2 }}
			>
				<TextField
					multiline
					maxRows={4}
					value={comment}
					placeholder="Escreva um comentário público"
					onChange={handleCommentChange}
					fullWidth
				/>

				<Stack direction="row" alignItems="center" gap={1}>
					<Button
						loading={isAddingComment}
						variant="contained"
						endIcon={<SendIcon />}
						disabled={comment.trim().length === 0}
						onClick={async () => {
							await addComment(comment);
							setComment("");
						}}
					>
						Comentar
					</Button>
					<Tooltip
						title={
							<Typography color="inherit">
								Disponível para os outros
								Coordenadores/Professores
							</Typography>
						}
					>
						<LockOpenIcon color="action" fontSize="small" />
					</Tooltip>
				</Stack>
			</Stack>
		);
	} else if (
		processData.phase === Phases.homologacao &&
		isAdminRole(currentUser.role as RolesUser)
	) {
		return (
			<Stack
				component="form"
				noValidate
				autoComplete="off"
				direction="column"
				sx={{ alignItems: "start", gap: 1, py: 2 }}
			>
				<pre>Prezado(a) Candidato(a), &#123;email_sent&#125;,</pre>
				<br />

				<pre>
					Notamos que seu formulário de inscrição precisa de alguns
					ajustes antes de podermos avaliá-lo.
				</pre>

				<pre>Motivo da solicitação:</pre>

				<TextField
					multiline
					maxRows={4}
					value={comment}
					onChange={handleCommentChange}
					fullWidth
				/>

				<pre>
					Para revisar e enviar novamente seu formulário, acesse o
					link abaixo:
				</pre>
				<pre>Revisar formulário</pre>
				<br />

				<pre>
					Por favor, verifique se todos os campos obrigatórios foram
					preenchidos antes de reenviar.
				</pre>
				<br />

				<pre>Atenciosamente,</pre>
				<br />

				<pre>Comissão Coordenadora</pre>
				<pre>Programa de Mestrado em Ciência da Computação</pre>
				<pre>
					Instituto de Matemática, Estatística e Ciência da Computação
				</pre>
				<pre>Universidade de São Paulo</pre>

				<Stack direction="row" alignItems="center" gap={1}>
					<Button
						loading={false}
						variant="contained"
						endIcon={<SendIcon />}
						disabled={comment.trim().length === 0}
						onClick={(_) => {
							handleReesendInformationsSend(comment);
							setComment("");
						}}
					>
						Solicitar reenvio ao candidato
					</Button>
					<Tooltip
						title={
							<Typography color="inherit">
								Acesso público ao candidato
							</Typography>
						}
					>
						<LockOpenIcon color="action" fontSize="small" />
					</Tooltip>
				</Stack>
			</Stack>
		);
	}
}
