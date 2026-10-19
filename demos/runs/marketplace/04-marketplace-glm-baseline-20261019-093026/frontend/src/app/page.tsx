"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Grid from "@mui/material/Grid";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Pagination from "@mui/material/Pagination";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import ListingCard from "@/components/ListingCard";
import { api, CATEGORIES, CONDITIONS } from "@/lib/api";
import type { Listing, Paginated } from "@/lib/types";

export default function HomePage() {
  return (
    <Suspense fallback={<Box sx={{ p: 4 }}><Typography>Carregando...</Typography></Box>}>
      <HomeContent />
    </Suspense>
  );
}

function HomeContent() {
  const params = useSearchParams();
  const [data, setData] = useState<Paginated<Listing> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState(params.get("q") || "");
  const [category, setCategory] = useState(params.get("category") || "");
  const [condition, setCondition] = useState(params.get("condition") || "");
  const [sort, setSort] = useState(params.get("sort") || "recent");
  const [page, setPage] = useState(Number(params.get("page") || 1));

  const load = useCallback(async () => {
    setError(null);
    const query = new URLSearchParams();
    if (q) query.set("q", q);
    if (category) query.set("category", category);
    if (condition) query.set("condition", condition);
    if (sort) query.set("sort", sort);
    query.set("page", String(page));
    try {
      setData(await api<Paginated<Listing>>(`/api/listings?${query.toString()}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar anúncios");
    }
  }, [q, category, condition, sort, page]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.limit)) : 1;

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 1200, mx: "auto" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Compre e venda de pessoa para pessoa
      </Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <TextField
              label="Buscar produtos"
              value={q}
              onChange={(e) => {
                setPage(1);
                setQ(e.target.value);
              }}
              fullWidth
            />
            <FormControlFilter label="Categoria">
              <Select
                value={category}
                onChange={(e) => {
                  setPage(1);
                  setCategory(e.target.value);
                }}
              >
                <MenuItem value="">Todas</MenuItem>
                {CATEGORIES.map((c) => (
                  <MenuItem key={c.value} value={c.value}>
                    {c.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControlFilter>
            <FormControlFilter label="Condição">
              <Select
                value={condition}
                onChange={(e) => {
                  setPage(1);
                  setCondition(e.target.value);
                }}
              >
                <MenuItem value="">Todas</MenuItem>
                {CONDITIONS.map((c) => (
                  <MenuItem key={c.value} value={c.value}>
                    {c.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControlFilter>
            <FormControlFilter label="Ordenar por">
              <Select value={sort} onChange={(e) => setSort(e.target.value)}>
                <MenuItem value="recent">Mais recentes</MenuItem>
                <MenuItem value="price_asc">Menor preço</MenuItem>
                <MenuItem value="price_desc">Maior preço</MenuItem>
              </Select>
            </FormControlFilter>
          </Stack>
        </CardContent>
      </Card>

      {error && (
        <Typography color="error" role="alert">
          {error}
        </Typography>
      )}
      {!data && !error && <Typography>Carregando anúncios...</Typography>}
      {data && data.items.length === 0 && (
        <Typography>Nenhum anúncio encontrado.</Typography>
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
            count={totalPages}
            page={page}
            onChange={(_, value) => setPage(value)}
          />
        </Stack>
      )}
    </Box>
  );
}

function FormControlFilter({
  label,
  children,
}: {
  label: string;
  children: React.ReactElement;
}) {
  return (
    <Box sx={{ minWidth: { xs: "100%", md: 180 } }}>
      <InputLabel>{label}</InputLabel>
      {children}
    </Box>
  );
}
