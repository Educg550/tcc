"use client";

import { useRouter } from "next/navigation";

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

import ListingForm from "@/components/ListingForm";
import { useAuth } from "@/lib/auth";

export default function NewListingPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  if (loading) return <Typography sx={{ p: 4 }}>Carregando...</Typography>;
  if (!user) {
    router.push("/login?next=/listings/new");
    return null;
  }

  return (
    <Box sx={{ maxWidth: 640, mx: "auto", p: 2, mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Anunciar
      </Typography>
      <ListingForm />
    </Box>
  );
}
