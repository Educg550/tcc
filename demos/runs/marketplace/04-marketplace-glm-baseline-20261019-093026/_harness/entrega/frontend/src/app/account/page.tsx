"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function AccountPage() {
  const { user, loading, refresh, logout } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push("/login?next=/account");
    return null;
  }
  if (!name) setName(user.name);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await api("/api/auth/me", {
        method: "PATCH",
        body: JSON.stringify({ name }),
      });
      await refresh();
      setMessage("Nome atualizado com sucesso.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar");
    }
  }

  return (
    <Box sx={{ maxWidth: 480, mx: "auto", p: 2, mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Minha conta
      </Typography>
      <Card>
        <CardContent>
          <Stack spacing={2} component="form" onSubmit={save}>
            {message && <Alert severity="success">{message}</Alert>}
            {error && <Alert severity="error" role="alert">{error}</Alert>}
            <Typography>E-mail: {user.email}</Typography>
            <TextField label="Nome" value={name} onChange={(e) => setName(e.target.value)} required />
            <Button type="submit" variant="contained">
              Salvar
            </Button>
            <Button
              color="error"
              onClick={async () => {
                await logout();
                router.push("/");
              }}
            >
              Sair da conta
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
