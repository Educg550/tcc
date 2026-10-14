export function flattenObject(
	obj: Record<string, any>,
	parentKey = "",
	result: Record<string, any> = {},
): Record<string, any> {
	for (const key in obj) {
		const value = obj[key];
		const newKey = parentKey ? `${parentKey}.${key}` : key;

		if (value && typeof value === "object" && !Array.isArray(value)) {
			flattenObject(value, newKey, result);
		} else {
			result[newKey] = value;
		}
	}

	return result;
}

export function escapeCSVValue(value: unknown): string {
	if (value === null || value === undefined) return "";
	const str = String(value);

	if (/[",\n]/.test(str)) {
		return `"${str.replace(/"/g, '""')}"`;
	}
	return str;
}

export function filterColumns<T extends Record<string, any>>(
	data: T[],
	remove: (keyof T)[],
): Partial<T>[] {
	return data.map((row) => {
		const newRow: Partial<T> = {};
		for (const key in row) {
			if (!remove.includes(key)) {
				newRow[key] = row[key];
			}
		}
		return newRow;
	});
}

export function toCSV<T extends Record<string, any>>(data: T[]): string {
	if (!data.length) return "";

	const flatData = data.map((item) => flattenObject(item));

	const headers = Array.from(
		new Set(flatData.flatMap((obj) => Object.keys(obj))),
	);

	const rows = flatData.map((row) =>
		headers.map((h) => escapeCSVValue(row[h])).join(","),
	);

	return [headers.join(","), ...rows].join("\n");
}

export function downloadCSV<T extends Record<string, any>>(
	data: T[],
	filename: string = "data.csv",
	removeColumns: (keyof T)[] = [],
): void {
	const filtered = removeColumns.length
		? filterColumns(data, removeColumns)
		: data;

	const csv = toCSV(filtered as T[]);
	const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });

	const url = URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
}
