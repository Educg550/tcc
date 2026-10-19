"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Rating from "@mui/material/Rating";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { api, formatDate, formatPrice, ORDER_STATUS } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Order } from "@/lib/types";

export default function OrderDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user, loading } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rating, setRating] = useState<number | null>(5);
  const [comment, setComment] = useState("");

  const load = useCallback(async () => {
    try {
      setOrder(await api<Order>(`/api/orders/${params.id}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar pedido");
    }
  }, [params.id]);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" role="alert">{error}</Alert>
      </Box>
    );
  }
  if (!user) {
    router.push(`/login?next=/orders/${params.id}`);
    return null;
  }
  if (!order) return <Typography sx={{ p: 4 }}>Carregando pedido...</Typography>;

  const isSeller = user.id === order.seller_id;
  const isBuyer = user.id === order.buyer_id;

  async function changeStatus(status: string) {
    setError(null);
    try {
      setOrder(
        await api<Order>(`/api/orders/${params.id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status }),
        })
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao atualizar status");
    }
  }

  async function submitReview(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await api(`/api/orders/${params.id}/review`, {
        method: "POST",
        body: JSON.stringify({ rating, comment }),
      });
      router.push(`/listing/${order!.listing_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao avaliar");
    }
  }

  return (
    <Box sx={{ maxWidth: 720, mx: "auto", p: 2 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Pedido #{order.id}
      </Typography>
      <Card>
        <CardContent>
          <Stack spacing={1}>
            <Stack direction="row" justifyContent="space-between">
              <Typography fontWeight="bold">
                <Link href={`/listing/${order.listing_id}`}>{order.listing_title}</Link>
              </Typography>
              <Chip label={ORDER_STATUS[order.status] || order.status} />
            </Stack>
            <Typography>Comprador: {order.buyer_name}</Typography>
            <Typography>Vendedor: {order.seller_name}</Typography>
            <Typography>
              Quantidade: {order.quantity} × {formatPrice(order.unit_price_cents)}
            </Typography>
            <Typography fontWeight="bold">
              Total: {formatPrice(order.total_cents)}
            </Typography>
            <Typography>Endereço: {order.address}</Typography>
            <Typography variant="body2" color="text.secondary">
              Criado em {formatDate(order.created_at)}
            </Typography>
            {error && <Alert severity="error" role="alert">{error}</Alert>}
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {isSeller && order.status === "pending" && (
                <Button variant="contained" onClick={() => changeStatus("confirmed")}>
                  Confirmar
                </Button>
              )}
              {isSeller && order.status === "confirmed" && (
                <Button variant="contained" onClick={() => changeStatus("shipped")}>
                  Enviar
                </Button>
              )}
              {isBuyer && order.status === "shipped" && (
                <Button variant="contained" onClick={() => changeStatus("delivered")}>
                  Marcar como entregue
                </Button>
              )}
              {isBuyer && (order.status === "pending" || order.status === "confirmed") && (
                <Button color="error" onClick={() => changeStatus("cancelled")}>
                  Cancelar
                </Button>
              )}
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {isBuyer && order.status === "delivered" && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Avaliar esta compra
            </Typography>
            <Stack component="form" onSubmit={submitReview} spacing={2}>
              <Rating
                value={rating}
                onChange={(_, value) => setRating(value)}
                aria-label="Nota"
              />
              <TextField
                label="Comentário (opcional)"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                multiline
                rows={3}
                inputProps={{ maxLength: 1000 }}
              />
              <Button type="submit" variant="contained">
                Enviar avaliação
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
