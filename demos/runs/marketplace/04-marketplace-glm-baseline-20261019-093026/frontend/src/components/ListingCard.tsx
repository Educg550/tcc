"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import Chip from "@mui/material/Chip";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import FavoriteIcon from "@mui/icons-material/Favorite";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { api, formatPrice } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Listing } from "@/lib/types";

const CONDITION_LABEL: Record<string, string> = { novo: "Novo", usado: "Usado" };

export default function ListingCard({ listing }: { listing: Listing }) {
  const { user } = useAuth();
  const router = useRouter();
  const [favorite, setFavorite] = useState(Boolean(listing.is_favorite));

  useEffect(() => {
    setFavorite(Boolean(listing.is_favorite));
  }, [listing.is_favorite]);

  async function toggleFavorite(event: React.MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (!user) {
      router.push(`/login?next=/listing/${listing.id}`);
      return;
    }
    try {
      if (favorite) {
        await api(`/api/favorites/${listing.id}`, { method: "DELETE" });
        setFavorite(false);
      } else {
        await api(`/api/favorites/${listing.id}`, { method: "POST" });
        setFavorite(true);
      }
    } catch {
      /* mantém estado atual em caso de erro */
    }
  }

  return (
    <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <CardActionArea
        component={Link}
        href={`/listing/${listing.id}`}
        sx={{ flexGrow: 1, display: "flex", flexDirection: "column", alignItems: "stretch" }}
      >
        <CardMedia
          component="img"
          height={160}
          image={listing.image_url || "/placeholder.svg"}
          alt={listing.title}
        />
        <CardContent sx={{ flexGrow: 1 }}>
          <Typography variant="h6" component="div" noWrap>
            {listing.title}
          </Typography>
          <Typography variant="subtitle1" color="primary" fontWeight="bold">
            {formatPrice(listing.price_cents)}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <Chip size="small" label={CONDITION_LABEL[listing.condition] || listing.condition} />
            <Chip size="small" label={listing.city} />
          </Stack>
        </CardContent>
      </CardActionArea>
      <IconButton
        aria-label={favorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}
        onClick={toggleFavorite}
        sx={{ position: "absolute", top: 4, right: 4, bgcolor: "background.paper" }}
      >
        {favorite ? <FavoriteIcon color="error" /> : <FavoriteBorderIcon />}
      </IconButton>
    </Card>
  );
}
