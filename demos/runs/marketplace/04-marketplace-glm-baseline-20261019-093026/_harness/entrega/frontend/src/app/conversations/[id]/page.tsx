"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Conversation, Message } from "@/lib/types";

export default function ConversationPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user, loading } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const all = await api<Conversation[]>("/api/conversations");
      const conv = all.find((c) => c.id === Number(params.id));
      setConversation(conv || null);
      setMessages(await api<Message[]>(`/api/conversations/${params.id}/messages`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar conversa");
    }
  }, [params.id]);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (!content.trim()) return;
    setError(null);
    try {
      await api(`/api/conversations/${params.id}/messages`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
      setContent("");
      setMessages(await api<Message[]>(`/api/conversations/${params.id}/messages`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar mensagem");
    }
  }

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push(`/login?next=/conversations/${params.id}`);
    return null;
  }
  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" role="alert">{error}</Alert>
      </Box>
    );
  }
  if (!conversation) return <Typography sx={{ p: 4 }}>Carregando conversa...</Typography>;

  return (
    <Box sx={{ maxWidth: 720, mx: "auto", p: 2 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        Conversa com {conversation.other_user.name}
      </Typography>
      <Typography variant="body2" gutterBottom>
        Anúncio:{" "}
        <Link href={`/listing/${conversation.listing_id}`}>
          {conversation.listing_title}
        </Link>
      </Typography>
      <Stack spacing={1} sx={{ my: 2 }}>
        {messages.length === 0 && (
          <Typography>Nenhuma mensagem ainda. Diga um olá!</Typography>
        )}
        {messages.map((msg) => (
          <Card
            key={msg.id}
            sx={{
              alignSelf: msg.sender_id === user?.id ? "flex-end" : "flex-start",
              maxWidth: "80%",
              bgcolor: msg.sender_id === user?.id ? "primary.light" : "grey.100",
            }}
          >
            <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
              <Typography variant="body2" fontWeight="bold">
                {msg.sender_id === user?.id ? "Você" : conversation.other_user.name}
              </Typography>
              <Typography>{msg.content}</Typography>
              <Typography variant="caption" color="text.secondary">
                {formatDate(msg.created_at)}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Stack>
      <Stack component="form" onSubmit={send} direction="row" spacing={1}>
        <TextField
          label="Mensagem"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          fullWidth
          required
          inputProps={{ maxLength: 2000 }}
        />
        <Button type="submit" variant="contained">
          Enviar
        </Button>
      </Stack>
    </Box>
  );
}
