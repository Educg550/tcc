import React, { useState } from "react";
import { MenuItem, Select, SelectChangeEvent } from "@mui/material";
import { useSnackbar } from "@/provider/messageContext";
import { BiddingState } from "../model/application-candidate";
import { biddingLabels } from "../[processId]/mappers/applicant";

export default function SelectBidding(
	params: { row: any } & { callback?: () => void },
) {
	const callback = params.callback;
	const applicant = params.row;
	const { showSnackbar } = useSnackbar();
	const [userBiddingState, setUserBiddingState] = useState<BiddingState>(
		applicant.userBidding != undefined ? applicant.userBidding : "",
	);
	const [isLoading, setLoading] = useState(false);

	function submissionsUserBiddingHandler(event: SelectChangeEvent) {
		setLoading(true);

		const value = event.target.value as BiddingState;

		fetch(
			`${process.env.NEXT_PUBLIC_BASE_PATH}/submissions/${applicant.id}/api/bidding`,
			{
				method: "POST",
				body: JSON.stringify({
					bidding: value,
				}),
			},
		)
			.then((res) => {
				if (!res.ok) throw new Error("");
				setUserBiddingState(value);
				if (callback) callback();
				setLoading(false);
			})
			.catch((error) => {
				showSnackbar(
					`Ocorreu um erro ao manifestar interesse.`,
					"error",
				);
				setLoading(false);
			});
	}

	return (
		<>
			<Select
				value={userBiddingState}
				size="small"
				onClick={(e) => e.stopPropagation()}
				onChange={submissionsUserBiddingHandler}
				defaultValue={""}
				fullWidth
				disabled={isLoading}
				MenuProps={{
					PaperProps: {
						sx: {
							maxWidth: 300,
							"& .MuiMenuItem-root": {
								whiteSpace: "normal",
								wordWrap: "break-word",
							},
						},
					},
				}}
			>
				[
				<MenuItem key={"menuitem--empty"} value="">
					&nbsp;
				</MenuItem>
				,
				<MenuItem
					key={`menuitem--${BiddingState.AGREED}`}
					value={BiddingState.AGREED}
				>
					{biddingLabels[BiddingState.AGREED]}
				</MenuItem>
				,
				<MenuItem
					key={`menuitem--${BiddingState.INTERESTED_SCHOLARSHIP}`}
					value={BiddingState.INTERESTED_SCHOLARSHIP}
				>
					{biddingLabels[BiddingState.INTERESTED_SCHOLARSHIP]}
				</MenuItem>
				,
				<MenuItem
					key={`menuitem--${BiddingState.INTERESTED}`}
					value={BiddingState.INTERESTED}
				>
					{biddingLabels[BiddingState.INTERESTED]}
				</MenuItem>
				,
				<MenuItem
					key={`menuitem--${BiddingState.AVAILABLE}`}
					value={BiddingState.AVAILABLE}
				>
					{biddingLabels[BiddingState.AVAILABLE]}
				</MenuItem>
				,
				<MenuItem
					key={`menuitem--${BiddingState.DECLINE}`}
					value={BiddingState.DECLINE}
				>
					{biddingLabels[BiddingState.DECLINE]}
				</MenuItem>
				]
			</Select>
		</>
	);
}
