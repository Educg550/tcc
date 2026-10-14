import { styled, darken, lighten } from "@mui/material/styles";

interface CustomProps {
	elevation: number;
}

const withElevationBackground = <T extends object>(
	Component: React.ComponentType<T>,
) =>
	styled(Component, {
		shouldForwardProp: (prop) => prop !== "elevation",
	})<T & CustomProps>(({ theme, elevation }) => {
		const baseColor = theme.palette.background.paper || "#fff";
		const ratio = Math.min(elevation * 0.025, 0.5);

		return {
			backgroundColor:
				theme.palette.mode === "dark"
					? lighten(baseColor, ratio)
					: darken(baseColor, ratio),
			boxShadow: "none",
		};
	});

export default withElevationBackground;
