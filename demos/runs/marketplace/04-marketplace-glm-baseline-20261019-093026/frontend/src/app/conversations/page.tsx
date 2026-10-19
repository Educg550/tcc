"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { api, formatDate } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Conversation } from "@/lib/types";

export default function ConversationsPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [conversations, setConversations] = useState<Conversation[] | null>(null);

  useEffect(() => {
    if (user) {
      api<Conversation[]>("/api/conversations").then(setConversations).catch(() =>
        setConversations([])
      );
    }
  }, [user]);

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push("/login?next=/conversations");
    return null;
  }

  return (
    <Box sx={{ maxWidth: 720, mx: "auto", p: 2 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Conversas
      </Typography>
      {!conversations && <Typography>Carregando...</Typography>}
      {conversations && conversations.length === 0 && (
        <Typography>Nenhuma conversa ainda.</Typography>
      )}
      <Stack spacing={2}>
        {conversations?.map((conv) => (
          <Card key={conv.id}>
            <CardContent>
              <Typography fontWeight="bold">{conv.other_user.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                Anúncio: {conv.listing_title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Iniciada em {formatDate(conv.created_at)}
              </Typography>
              <Link href={`/conversations/${conv.id}`}>Abrir conversa</Link>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Box>
  );
}
