"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Pagination from "@mui/material/Pagination";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import ListingCard from "@/components/ListingCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Listing, Paginated } from "@/lib/types";

export default function FavoritesPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [data, setData] = useState<Paginated<Listing> | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    try {
      setData(await api<Paginated<Listing>>(`/api/favorites?page=${page}`));
    } catch {
      setData({ items: [], total: 0, page: 1, limit: 12 });
    }
  }, [page]);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push("/login?next=/favorites");
    return null;
  }

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 1100, mx: "auto" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Favoritos
      </Typography>
      {!data && <Typography>Carregando...</Typography>}
      {data && data.items.length === 0 && (
        <Typography>Nenhum anúncio favoritado.</Typography>
      )}
      <Grid container spacing={2}>
        {data?.items.map((listing) => (
          <Grid key={listing.id} size={{ xs: 12, sm: 6, md: 3 }}>
            <ListingCard listing={listing} />
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
