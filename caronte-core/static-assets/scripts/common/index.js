export const createElementFromHTML = (htmlString) => {
	const div = document.createElement('div')

	div.innerHTML = htmlString.trim()

	return div.firstElementChild
}

HTMLElement.prototype.appendDOM = function (
	stringHtml,
	position = 'beforeend',
) {
	this.insertAdjacentHTML(position, stringHtml.trim())
	if (position === 'beforeend') return this.lastElementChild
	else if (position === 'afterbegin') return this.firstElementChild
	else return this
}
