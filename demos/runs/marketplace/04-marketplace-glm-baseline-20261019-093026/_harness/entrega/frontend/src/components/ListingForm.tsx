"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";

import { api, CATEGORIES, CONDITIONS } from "@/lib/api";
import type { Listing } from "@/lib/types";

export interface ListingFormValues {
  title: string;
  description: string;
  price: string;
  stock: string;
  category: string;
  condition: string;
  city: string;
  image_url: string;
}

export default function ListingForm({
  initial,
  listingId,
}: {
  initial?: Listing;
  listingId?: number;
}) {
  const router = useRouter();
  const [values, setValues] = useState<ListingFormValues>({
    title: initial?.title || "",
    description: initial?.description || "",
    price: initial ? (initial.price_cents / 100).toFixed(2) : "",
    stock: initial ? String(initial.stock) : "1",
    category: initial?.category || "eletronicos",
    condition: initial?.condition || "novo",
    city: initial?.city || "",
    image_url: initial?.image_url || "",
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function set<K extends keyof ListingFormValues>(key: K, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const price_cents = Math.round(parseFloat(values.price.replace(",", ".")) * 100);
    if (!Number.isFinite(price_cents) || price_cents <= 0) {
      setError("Informe um preço válido maior que zero.");
      return;
    }
    const payload = {
      title: values.title,
      description: values.description,
      price_cents,
      stock: parseInt(values.stock, 10),
      category: values.category,
      condition: values.condition,
      city: values.city,
      image_url: values.image_url || null,
    };
    setSaving(true);
    try {
      const saved = await api<Listing>(
        listingId ? `/api/listings/${listingId}` : "/api/listings",
        { method: listingId ? "PATCH" : "POST", body: JSON.stringify(payload) }
      );
      router.push(`/listing/${saved.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar anúncio");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardContent>
        <Stack spacing={2} component="form" onSubmit={submit}>
          {error && <Alert severity="error" role="alert">{error}</Alert>}
          <TextField
            label="Título"
            value={values.title}
            onChange={(e) => set("title", e.target.value)}
            required
            helperText="De 3 a 120 caracteres"
          />
          <TextField
            label="Descrição"
            value={values.description}
            onChange={(e) => set("description", e.target.value)}
            multiline
            rows={5}
            required
            helperText="De 10 a 5000 caracteres"
          />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              label="Preço (R$)"
              value={values.price}
              onChange={(e) => set("price", e.target.value)}
              required
              inputProps={{ inputMode: "decimal" }}
            />
            <TextField
              label="Estoque"
              type="number"
              value={values.stock}
              onChange={(e) => set("stock", e.target.value)}
              required
              inputProps={{ min: 1, max: 999 }}
            />
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Categoria</InputLabel>
              <Select
                value={values.category}
                onChange={(e) => set("category", e.target.value)}
                label="Categoria"
              >
                {CATEGORIES.map((c) => (
                  <MenuItem key={c.value} value={c.value}>{c.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Condição</InputLabel>
              <Select
                value={values.condition}
                onChange={(e) => set("condition", e.target.value)}
                label="Condição"
              >
                {CONDITIONS.map((c) => (
                  <MenuItem key={c.value} value={c.value}>{c.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <TextField
            label="Cidade"
            value={values.city}
            onChange={(e) => set("city", e.target.value)}
            required
          />
          <TextField
            label="URL da imagem (opcional)"
            value={values.image_url}
            onChange={(e) => set("image_url", e.target.value)}
          />
          <Box>
            <Button type="submit" variant="contained" disabled={saving}>
              {listingId ? "Salvar alterações" : "Publicar anúncio"}
            </Button>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
