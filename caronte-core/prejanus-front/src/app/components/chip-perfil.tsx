import React from "react";
import { Avatar, AvatarGroup, hslToRgb } from "@mui/material";
import {
	getTextColor,
	stringToColor,
} from "../[processId]/submissions/[submissionId]/utils/utils";

const SIZE_AVATAR = 27;

export default function ChipPerfil(params: any) {
	let max = Math.floor(params.column.getSize() / SIZE_AVATAR) - 1;
	if (max <= 0) max = 1;

	return (
		<>
			<AvatarGroup
				max={max}
				sx={{
					"& .MuiAvatar-root": {
						width: SIZE_AVATAR,
						height: SIZE_AVATAR,
						fontSize: 15,
					},
				}}
			>
				{params.cell
					.getValue()
					?.map((value: { name: string }, index: number) => {
						const { color: bgColor } = stringToColor(value.name);
						const fontColor = getTextColor(hslToRgb(bgColor));
						return (
							<Avatar
								key={index}
								alt={value.name}
								sx={{
									width: SIZE_AVATAR,
									height: SIZE_AVATAR,
									bgcolor: bgColor,
									color: fontColor,
								}}
								title={value.name}
							>
								{value.name[0].toUpperCase()}
							</Avatar>
						);
					})}
			</AvatarGroup>
		</>
	);
}
