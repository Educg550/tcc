import { checkValidity } from './builder.js'

function createTagInput(tag, idx, field, placeholder, state, saveBtn) {
	const input = document.createElement('input')
	input.type = 'text'
	input.placeholder = placeholder
	input.value = tag[field]
	input.addEventListener('input', () => {
		state._tagIds[idx][field] = input.value
		checkValidity(state, saveBtn)
	})
	return input
}

function createDeleteBtn(idx, state, i18n, container, saveBtn) {
	const btn = document.createElement('button')
	btn.type = 'button'
	btn.setAttribute('data-delete-tag', '')
	btn.setAttribute('id', 'delete-tag-button')
	btn.textContent = i18n.deleteTag || 'Remove Tag'
	btn.disabled = state._tagIds.length <= 1
	btn.addEventListener('click', () => {
		state._tagIds.splice(idx, 1)
		renderTagList(state, i18n, container, saveBtn)
		checkValidity(state, saveBtn)
	})
	return btn
}

function createTagRow(tag, idx, state, i18n, container, saveBtn) {
	const li = document.createElement('li')
	li.appendChild(
		createTagInput(tag, idx, 'key', i18n.key || 'Key', state, saveBtn),
	)
	li.appendChild(
		createTagInput(tag, idx, 'value', i18n.value || 'Value', state, saveBtn),
	)
	li.appendChild(createDeleteBtn(idx, state, i18n, container, saveBtn))
	return li
}

function renderTagList(state, i18n, container, saveBtn) {
	const ul = container.querySelector('ul') || document.createElement('ul')
	ul.innerHTML = ''
	state._tagIds.forEach((tag, idx) =>
		ul.appendChild(createTagRow(tag, idx, state, i18n, container, saveBtn)),
	)
	if (!container.contains(ul)) container.appendChild(ul)
}

export function renderTags(state, i18n, container, saveBtn) {
	const addBtn = document.createElement('button')
	addBtn.type = 'button'
	addBtn.setAttribute('data-add-tag', '')
	addBtn.setAttribute('id', 'add-tag-button')
	addBtn.textContent = i18n.addTag || 'Add Tag'
	addBtn.addEventListener('click', () => {
		state._tagIds.push({ id: crypto.randomUUID(), key: '', value: '' })
		renderTagList(state, i18n, container, saveBtn)
		checkValidity(state, saveBtn)
	})
	container.appendChild(addBtn)
	renderTagList(state, i18n, container, saveBtn)
}
