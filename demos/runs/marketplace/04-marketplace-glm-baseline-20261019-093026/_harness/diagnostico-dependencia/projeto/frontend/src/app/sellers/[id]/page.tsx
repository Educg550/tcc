"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Grid from "@mui/material/Grid";
import Rating from "@mui/material/Rating";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import ListingCard from "@/components/ListingCard";
import { api } from "@/lib/api";
import type { Listing, Paginated } from "@/lib/types";

interface SellerProfile {
  id: number;
  name: string;
  average_rating: number | null;
  reviews_count: number;
}

export default function SellerPage() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<SellerProfile | null>(null);
  const [listings, setListings] = useState<Paginated<Listing> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<SellerProfile>(`/api/sellers/${params.id}`)
      .then(setProfile)
      .catch((e) => setError(e instanceof Error ? e.message : "Erro"));
    api<Paginated<Listing>>(`/api/sellers/${params.id}/listings`)
      .then(setListings)
      .catch(() => setListings({ items: [], total: 0, page: 1, limit: 12 }));
  }, [params.id]);

  if (error) return <Typography sx={{ p: 4 }}>{error}</Typography>;
  if (!profile) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 1100, mx: "auto" }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h4" component="h1">
            {profile.name}
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
            <Rating value={profile.average_rating || 0} precision={0.5} readOnly />
            <Typography>
              {profile.average_rating !== null
                ? `${profile.average_rating.toFixed(1)} (${profile.reviews_count} avaliações)`
                : "Sem avaliações"}
            </Typography>
          </Stack>
        </CardContent>
      </Card>
      <Typography variant="h5" gutterBottom>
        Anúncios
      </Typography>
      {listings && listings.items.length === 0 && (
        <Typography>Nenhum anúncio ativo.</Typography>
      )}
      <Grid container spacing={2}>
        {listings?.items.map((listing) => (
          <Grid key={listing.id} size={{ xs: 12, sm: 6, md: 3 }}>
            <ListingCard listing={listing} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
