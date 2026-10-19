"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";

import ListingForm from "@/components/ListingForm";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Listing } from "@/lib/types";

export default function EditListingPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [listing, setListing] = useState<Listing | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Listing>(`/api/listings/${params.id}`)
      .then(setListing)
      .catch((e) => setError(e instanceof Error ? e.message : "Erro ao carregar"));
  }, [params.id]);

  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" role="alert">{error}</Alert>
      </Box>
    );
  }
  if (authLoading || !listing) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push(`/login?next=/listings/${params.id}/edit`);
    return null;
  }
  if (listing.seller.id !== user.id) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">Você não é o dono deste anúncio.</Alert>
      </Box>
    );
  }

  async function toggleStatus() {
    const next = listing!.status === "active" ? "inactive" : "active";
    await api(`/api/listings/${params.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: next }),
    });
    setListing({ ...listing!, status: next });
  }

  return (
    <Box sx={{ maxWidth: 640, mx: "auto", p: 2, mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Editar anúncio
      </Typography>
      <ListingForm initial={listing} listingId={Number(params.id)} />
      <Box sx={{ mt: 2 }}>
        <Button
          variant={listing.status === "active" ? "outlined" : "contained"}
          color="warning"
          onClick={toggleStatus}
        >
          {listing.status === "active" ? "Desativar anúncio" : "Ativar anúncio"}
        </Button>
      </Box>
    </Box>
  );
}
