"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Pagination from "@mui/material/Pagination";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";

import { api, formatDate, formatPrice, ORDER_STATUS } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Order, Paginated } from "@/lib/types";

function OrdersContent() {
  const router = useRouter();
  const params = useSearchParams();
  const { user, loading } = useAuth();
  const role = params.get("role") === "seller" ? "seller" : "buyer";
  const [data, setData] = useState<Paginated<Order> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await api<Paginated<Order>>(`/api/me/orders?role=${role}&page=${page}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar pedidos");
    }
  }, [role, page]);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push(`/login?next=/orders?role=${role}`);
    return null;
  }

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 900, mx: "auto" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {role === "buyer" ? "Minhas compras" : "Minhas vendas"}
      </Typography>
      <Tabs
        value={role}
        onChange={(_, value) => router.push(`/orders?role=${value}`)}
        sx={{ mb: 2 }}
      >
        <Tab value="buyer" label="Minhas compras" />
        <Tab value="seller" label="Minhas vendas" />
      </Tabs>
      {error && <Alert severity="error" role="alert">{error}</Alert>}
      {!data && !error && <Typography>Carregando...</Typography>}
      {data && data.items.length === 0 && (
        <Typography>Nenhum pedido encontrado.</Typography>
      )}
      <Stack spacing={2}>
        {data?.items.map((order) => (
          <Card key={order.id}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" flexWrap="wrap">
                <Typography fontWeight="bold">Pedido #{order.id}</Typography>
                <Chip label={ORDER_STATUS[order.status] || order.status} />
              </Stack>
              <Typography>
                {role === "buyer"
                  ? `Vendedor: ${order.seller_name}`
                  : `Comprador: ${order.buyer_name}`}
              </Typography>
              <Link href={`/listing/${order.listing_id}`}>{order.listing_title}</Link>
              <Typography>
                {order.quantity} × {formatPrice(order.unit_price_cents)} ={" "}
                <strong>{formatPrice(order.total_cents)}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatDate(order.created_at)}
              </Typography>
              <Link href={`/orders/${order.id}`}>Ver detalhes</Link>
            </CardContent>
          </Card>
        ))}
      </Stack>
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

export default function OrdersPage() {
  return (
    <Suspense fallback={<Typography sx={{ p: 4 }}>Carregando...</Typography>}>
      <OrdersContent />
    </Suspense>
  );
}
