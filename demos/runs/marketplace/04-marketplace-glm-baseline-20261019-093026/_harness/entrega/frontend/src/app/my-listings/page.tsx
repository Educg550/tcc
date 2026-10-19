"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid";
import Pagination from "@mui/material/Pagination";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { api, formatPrice } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Listing, Paginated } from "@/lib/types";

export default function MyListingsPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [data, setData] = useState<Paginated<Listing> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    try {
      setData(await api<Paginated<Listing>>(`/api/me/listings?page=${page}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar");
    }
  }, [page]);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push("/login?next=/my-listings");
    return null;
  }

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 1100, mx: "auto" }}>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1">
          Meus anúncios
        </Typography>
        <Button component={Link} href="/listings/new" variant="contained">
          Anunciar
        </Button>
      </Stack>
      {error && <Alert severity="error" role="alert">{error}</Alert>}
      {!data && !error && <Typography>Carregando...</Typography>}
      {data && data.items.length === 0 && (
        <Typography>Você ainda não tem anúncios.</Typography>
      )}
      <Grid container spacing={2}>
        {data?.items.map((listing) => (
          <Grid key={listing.id} size={{ xs: 12, sm: 6, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" noWrap>{listing.title}</Typography>
                <Typography color="primary" fontWeight="bold">
                  {formatPrice(listing.price_cents)}
                </Typography>
                <Stack direction="row" spacing={1} sx={{ my: 1 }}>
                  <Chip
                    size="small"
                    color={listing.status === "active" ? "success" : "default"}
                    label={listing.status === "active" ? "Ativo" : "Inativo"}
                  />
                  <Chip size="small" label={`Estoque: ${listing.stock}`} />
                </Stack>
                <Button
                  component={Link}
                  href={`/listings/${listing.id}/edit`}
                  variant="outlined"
                  size="small"
                >
                  Editar
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      {data && data.total > data.limit && (
        <Stack alignItems="center" sx={{ mt: 3 }}>
          <Pagination
            count={Math.ceil(data.total / data.limit)}
            page={page}
            onChange={(_, value) => setPage(value)}
          />
        </Stack>
      )}
    </Box>
  );
}
