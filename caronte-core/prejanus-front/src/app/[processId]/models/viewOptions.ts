export type ViewOptions = {
	collapsedSidebar: boolean;
};

export type UpdateViewOptionFn = <K extends keyof ViewOptions>(
	key: K,
	value: ViewOptions[K],
) => void;

export type ChildProps = {
	updateOption: UpdateViewOptionFn;
};
