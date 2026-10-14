export const smartLink = (url: string) => {
	const regEx = /^http/;

	return regEx.test(url) ? url : `https://${url}`;
};
