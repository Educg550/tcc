import { Search } from "@mui/icons-material";
import {
	Avatar,
	Divider,
	ListItem,
	ListItemAvatar,
	ListItemButton,
	ListItemText,
} from "@mui/material";
import { TEdict } from "../model/edict";

type EdictItemProps = {
	edict: TEdict;
	handleClickEdict: (id: number) => void;
};

export default function EdictItem({ edict, handleClickEdict }: EdictItemProps) {
	return (
		<>
			<ListItem disablePadding>
				<ListItemButton onClick={() => handleClickEdict(edict.id)}>
					<ListItemAvatar>
						<Avatar>
							<Search />
						</Avatar>
					</ListItemAvatar>
					<ListItemText
						primary={edict.title}
						secondary={
							<>
								{edict.edictType} - {edict.year}.
								{edict.semester}
							</>
						}
					/>
				</ListItemButton>
			</ListItem>
			<Divider />
		</>
	);
}
