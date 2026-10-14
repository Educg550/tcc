export default function insertIntoTarget(element, options) {
    var parent = options.target || document.head
    if (options.id) element.dataset.id = options.id
    parent.appendChild(element)
}