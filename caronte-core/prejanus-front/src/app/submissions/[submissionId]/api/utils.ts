const daysInMillis = 1000 * 3600 * 24;

export function getDaysFromDate(date: string): string {
	const inputDate = new Date(date);
	inputDate.setHours(0, 0, 0, 0);

	const now = new Date();
	now.setHours(0, 0, 0, 0);

	const diff = now.getTime() - inputDate.getTime();
	const days = Math.floor(diff / daysInMillis);

	if (days === 0) return "Hoje";
	if (days === 1) return "Ontem";
	if (days > 30) {
		const months = Math.floor(days / 30)
		if (months === 1) {
			return "1 mês atrás"
		}
		return `${Math.floor(days / 30)} meses atrás`
	}

	return `${days} dias atrás`;
}

export function formattedDate(date: string) {
	return new Date(date).toLocaleDateString("pt-BR");
}
