"use client";

import Link from "next/link";
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

export default function RegisterPage() {
  const router = useRouter();
  const { refresh } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      });
      await api("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await refresh();
      router.push("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao criar conta");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box sx={{ maxWidth: 420, mx: "auto", p: 2, mt: 6 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Criar conta
      </Typography>
      <Card>
        <CardContent>
          <form onSubmit={submit}>
            <Stack spacing={2}>
              {error && <Alert severity="error" role="alert">{error}</Alert>}
              <TextField
                label="Nome"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <TextField
                label="E-mail"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <TextField
                label="Senha (mínimo 8 caracteres)"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                helperText="Ao menos 8 caracteres"
              />
              <Button type="submit" variant="contained" disabled={loading}>
                Criar conta
              </Button>
              <Typography variant="body2">
                Já tem conta? <Link href="/login">Entrar</Link>
              </Typography>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
