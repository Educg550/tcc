"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import Rating from "@mui/material/Rating";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import ListingCard from "@/components/ListingCard";
import { api, formatDate, formatPrice } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Listing, Review } from "@/lib/types";

const CONDITION_LABEL: Record<string, string> = { novo: "Novo", usado: "Usado" };

export default function ListingDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [listing, setListing] = useState<Listing | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [buyOpen, setBuyOpen] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [address, setAddress] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setListing(await api<Listing>(`/api/listings/${params.id}`));
      setReviews(await api<Review[]>(`/api/listings/${params.id}/reviews`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar anúncio");
    }
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load]);

  function requireLogin(): boolean {
    if (user) return true;
    router.push(`/login?next=/listing/${params.id}`);
    return false;
  }

  async function buy() {
    setActionError(null);
    try {
      const order = await api<{ id: number }>("/api/orders", {
        method: "POST",
        body: JSON.stringify({
          listing_id: Number(params.id),
          quantity,
          address,
        }),
      });
      setBuyOpen(false);
      router.push(`/orders/${order.id}`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Erro ao comprar");
    }
  }

  async function startConversation() {
    if (!requireLogin()) return;
    setActionError(null);
    try {
      const conv = await api<{ id: number }>("/api/conversations", {
        method: "POST",
        body: JSON.stringify({ listing_id: Number(params.id) }),
      });
      router.push(`/conversations/${conv.id}`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Erro ao abrir conversa");
    }
  }

  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" role="alert">{error}</Alert>
        <Button component={Link} href="/" sx={{ mt: 2 }}>
          Voltar ao catálogo
        </Button>
      </Box>
    );
  }
  if (!listing) return <Typography sx={{ p: 4 }}>Carregando anúncio...</Typography>;

  const isSeller = user?.id === listing.seller.id;

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 1100, mx: "auto" }}>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardMedia
              component="img"
              image={listing.image_url || "/placeholder.svg"}
              alt={listing.title}
              sx={{ maxHeight: 420 }}
            />
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Stack spacing={2}>
            <Typography variant="h4" component="h1">
              {listing.title}
            </Typography>
            <Typography variant="h5" color="primary">
              {formatPrice(listing.price_cents)}
            </Typography>
            <Stack direction="row" spacing={1}>
              <Chip label={CONDITION_LABEL[listing.condition] || listing.condition} />
              <Chip label={listing.city} />
              <Chip label={`Estoque: ${listing.stock}`} />
            </Stack>
            <Typography variant="body1" whiteSpace="pre-wrap">
              {listing.description}
            </Typography>
            <Divider />
            <Typography>
              Vendido por{" "}
              <Link href={`/sellers/${listing.seller.id}`}>
                {listing.seller.name}
              </Link>
            </Typography>
            <Typography variant="body2">
              Publicado em {formatDate(listing.created_at)}
            </Typography>
            {actionError && <Alert severity="error" role="alert">{actionError}</Alert>}
            {!authLoading && !isSeller && (
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => {
                    if (requireLogin()) {
                      setQuantity(1);
                      setActionError(null);
                      setBuyOpen(true);
                    }
                  }}
                >
                  Comprar
                </Button>
                <Button variant="outlined" size="large" onClick={startConversation}>
                  Conversar
                </Button>
              </Stack>
            )}
            {isSeller && (
              <Button component={Link} href={`/listings/${listing.id}/edit`} variant="outlined">
                Editar anúncio
              </Button>
            )}
          </Stack>
        </Grid>
      </Grid>

      <Typography variant="h5" sx={{ mt: 5, mb: 2 }}>
        Avaliações ({reviews.length})
      </Typography>
      {reviews.length === 0 && <Typography>Nenhuma avaliação ainda.</Typography>}
      <Stack spacing={2}>
        {reviews.map((review) => (
          <Card key={review.id}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between">
                <Typography fontWeight="bold">{review.buyer_name}</Typography>
                <Rating value={review.rating} readOnly />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                {formatDate(review.created_at)}
              </Typography>
              {review.comment && <Typography sx={{ mt: 1 }}>{review.comment}</Typography>}
            </CardContent>
          </Card>
        ))}
      </Stack>

      {listing.seller_listings && listing.seller_listings.length > 0 && (
        <>
          <Typography variant="h5" sx={{ mt: 5, mb: 2 }}>
            Outros anúncios de {listing.seller.name}
          </Typography>
          <Grid container spacing={2}>
            {listing.seller_listings.map((item) => (
              <Grid key={item.id} size={{ xs: 12, sm: 6, md: 3 }}>
                <ListingCard listing={item} />
              </Grid>
            ))}
          </Grid>
        </>
      )}

      <Dialog open={buyOpen} onClose={() => setBuyOpen(false)} fullWidth>
        <DialogTitle>Confirmar compra</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {actionError && <Alert severity="error" role="alert">{actionError}</Alert>}
            <Typography>
              {listing.title} — {formatPrice(listing.price_cents)} cada
            </Typography>
            <TextField
              label="Quantidade"
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              inputProps={{ min: 1, max: listing.stock }}
              required
            />
            <TextField
              label="Endereço de entrega"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              multiline
              rows={3}
              required
              helperText="Máximo de 500 caracteres"
            />
            <Typography fontWeight="bold">
              Total: {formatPrice(listing.price_cents * quantity)}
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBuyOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={buy} disabled={!address.trim() || quantity < 1}>
            Confirmar compra
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
