export const getBrightness = (r: number, g: number, b: number) => {
	return (r * 299 + g * 587 + b * 114) / 1000;
};

export const getTextColor = (backgroundColor: string) => {
	let r, g, b;

	if (backgroundColor.startsWith("#")) {
		const hex = backgroundColor.slice(1);
		r = parseInt(hex.substring(0, 2), 16);
		g = parseInt(hex.substring(2, 4), 16);
		b = parseInt(hex.substring(4, 6), 16);
	} else if (backgroundColor.startsWith("rgb")) {
		const rgbValues = backgroundColor.match(/\d+/g)?.map(Number) ?? [
			0, 0, 0,
		];
		[r, g, b] = rgbValues;
	} else {
		return "black";
	}

	const brightness = getBrightness(r, g, b);
	return brightness > 150 ? "black" : "white";
};

export function stringToColor(string: string) {
	const number = string
		.split("")
		.map((letter) => letter.charCodeAt(0))
		.reduce((accumulator, currentValue) => accumulator + currentValue, 0);
	const hue = Math.floor(number % 360);
	const saturation = 51;
	const luminiosity = 39;
	return {
		color: `hsl(${hue}, ${saturation}%, ${luminiosity}%)`,
		hue,
		saturation,
		luminiosity,
	};
}
