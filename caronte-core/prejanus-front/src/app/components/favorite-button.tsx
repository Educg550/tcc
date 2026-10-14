import React from "react";
import BookmarkAddedIcon from "@mui/icons-material/BookmarkAdded";
import BookmarkBorderIcon from "@mui/icons-material/BookmarkBorder";
import { IconButton } from "@mui/material";
import { ApplicantItem } from "../model/application-candidate";

interface FavoriteButtonProps {
	isFavorite?: boolean;
	applicant: ApplicantItem;
}

export default function FavoriteButton(params: any) {
	const { isFavorite = false, applicant }: FavoriteButtonProps = params.cell
		? params.cell.getValue()
		: params;

	return (
		<IconButton
			onClick={(event) => {
				event.stopPropagation();
				if (params.row) {
					params.row.original.toggleFavorite(params);
				} else {
					params.toggleFavorite(params);
				}
			}}
		>
			{isFavorite ? <BookmarkAddedIcon /> : <BookmarkBorderIcon />}
		</IconButton>
	);
}
