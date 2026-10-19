"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import MenuIcon from "@mui/icons-material/Menu";
import StorefrontIcon from "@mui/icons-material/Storefront";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";

import { useAuth } from "@/lib/auth";

const LINKS = [
  { href: "/favorites", label: "Favoritos" },
  { href: "/conversations", label: "Conversas" },
  { href: "/orders?role=buyer", label: "Minhas compras" },
  { href: "/orders?role=seller", label: "Minhas vendas" },
  { href: "/my-listings", label: "Meus anúncios" },
  { href: "/listings/new", label: "Anunciar" },
  { href: "/account", label: "Minha conta" },
];

export default function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  async function handleLogout() {
    await logout();
    router.push("/");
  }

  return (
    <AppBar position="sticky" color="primary">
      <Toolbar>
        <IconButton
          color="inherit"
          edge="start"
          aria-label="Abrir menu"
          onClick={() => setOpen(true)}
          sx={{ mr: 2, display: { sm: "none" } }}
        >
          <MenuIcon />
        </IconButton>
        <Button
          color="inherit"
          component={Link}
          href="/"
          startIcon={<StorefrontIcon />}
          sx={{ mr: "auto", textTransform: "none" }}
        >
          <Typography variant="h6" component="span">
            Feira Livre
          </Typography>
        </Button>
        {user ? (
          <>
            <Box sx={{ display: { xs: "none", sm: "flex" }, gap: 1, alignItems: "center" }}>
              {LINKS.map((link) => (
                <Button key={link.href} color="inherit" component={Link} href={link.href}>
                  {link.label}
                </Button>
              ))}
              <Button color="inherit" onClick={handleLogout}>
                Sair
              </Button>
            </Box>
            <Drawer open={open} onClose={() => setOpen(false)}>
              <List sx={{ width: 240 }}>
                {LINKS.map((link) => (
                  <ListItemButton
                    key={link.href}
                    component={Link}
                    href={link.href}
                    onClick={() => setOpen(false)}
                  >
                    <ListItemText primary={link.label} />
                  </ListItemButton>
                ))}
                <Divider />
                <ListItemButton onClick={handleLogout}>
                  <ListItemText primary="Sair" />
                </ListItemButton>
              </List>
            </Drawer>
          </>
        ) : (
          <>
            <Button color="inherit" component={Link} href="/login">
              Entrar
            </Button>
            <Button color="inherit" component={Link} href="/register">
              Criar conta
            </Button>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
}
