import { checkValidity } from './builder.js'
import { addField, renderFields } from './fields.js'

export function addSection(state) {
	state.sections.push({
		_id: crypto.randomUUID(),
		title: { pt: '', en: '' },
		description: { pt: '', en: '' },
		fields: [],
	})
}

export function renderSections(state, config, i18n, container, saveBtn) {
	container.innerHTML = ''
	state.sections.forEach((section, i) => {
		const card = document.createElement('div')
		card.className = 'section-card'
		const buttons = document.createElement('div')
		buttons.className = 'section-buttons'

		const fields = [
			{ key: 'sectionTitlePt', prop: 'title', lang: 'pt' },
			{ key: 'sectionTitleEn', prop: 'title', lang: 'en' },
			{ key: 'sectionDescPt', prop: 'description', lang: 'pt' },
			{ key: 'sectionDescEn', prop: 'description', lang: 'en' },
		]
		fields.forEach(({ key, prop, lang }) => {
			const input = document.createElement('input')
			input.type = 'text'
			input.placeholder = i18n[key] || key
			input.value = section[prop][lang]
			input.addEventListener('input', () => {
				state.sections[i][prop][lang] = input.value
				checkValidity(state, saveBtn)
			})
			card.appendChild(input)
		})

		buttons.appendChild(
			createMoveUpBtn(i, state, config, i18n, container, saveBtn),
		)
		buttons.appendChild(
			createMoveDownBtn(i, state, config, i18n, container, saveBtn),
		)
		buttons.appendChild(
			createDeleteSectionBtn(i, state, config, i18n, container, saveBtn),
		)

		const fieldsContainer = document.createElement('div')
		fieldsContainer.className = 'fields-container'

		const [addFieldBtn, adder] = createAddFieldUI(
			i,
			state,
			config,
			i18n,
			fieldsContainer,
			saveBtn,
		)
		buttons.appendChild(addFieldBtn)
		buttons.appendChild(adder)
		card.appendChild(fieldsContainer)
		card.appendChild(buttons)

		renderFields(state, i, config, i18n, fieldsContainer, saveBtn)

		container.appendChild(card)
	})
}

function createMoveUpBtn(i, state, config, i18n, container, saveBtn) {
	const btn = document.createElement('button')
	btn.type = 'button'
	btn.dataset.moveUp = ''
	btn.textContent = i18n.moveUp || 'Move Up'
	btn.disabled = i === 0
	btn.addEventListener('click', () =>
		moveSection(state, config, i, -1, i18n, container, saveBtn),
	)
	return btn
}

function createMoveDownBtn(i, state, config, i18n, container, saveBtn) {
	const btn = document.createElement('button')
	btn.type = 'button'
	btn.dataset.moveDown = ''
	btn.textContent = i18n.moveDown || 'Move Down'
	btn.disabled = i === state.sections.length - 1
	btn.addEventListener('click', () =>
		moveSection(state, config, i, 1, i18n, container, saveBtn),
	)
	return btn
}

function createDeleteSectionBtn(i, state, config, i18n, container, saveBtn) {
	const btn = document.createElement('button')
	btn.type = 'button'
	btn.dataset.deleteSection = ''
	btn.textContent = i18n.deleteSection || 'Delete Section'
	btn.disabled = state.sections.length <= 1
	btn.addEventListener('click', () =>
		deleteSection(state, config, i, i18n, container, saveBtn),
	)
	return btn
}

function createAddFieldUI(i, state, config, i18n, fieldsContainer, saveBtn) {
	const btn = document.createElement('button')
	btn.type = 'button'
	btn.dataset.addField = ''
	btn.textContent = i18n.addField || 'Add Field'

	const adder = document.createElement('span')
	adder.style.display = 'none'

	const typeSelect = document.createElement('select')
	typeSelect.dataset.fieldTypeSelect = ''
	typeSelect.className = 'field-type-select'

	Object.keys(config.fieldTypes).forEach((typeKey) => {
		const option = document.createElement('option')
		option.value = typeKey
		option.textContent = config.fieldTypes[typeKey].label
		typeSelect.appendChild(option)
	})
	adder.appendChild(typeSelect)

	const confirmBtn = document.createElement('button')
	confirmBtn.type = 'button'
	confirmBtn.dataset.addFieldConfirm = ''
	confirmBtn.textContent = i18n.confirmAddField || 'Add'
	adder.appendChild(confirmBtn)

	btn.addEventListener('click', () => {
		adder.style.display = ''
	})
	confirmBtn.addEventListener('click', () => {
		addField(state, i, typeSelect.value)
		renderFields(state, i, config, i18n, fieldsContainer, saveBtn)
		checkValidity(state, saveBtn)
		adder.style.display = 'none'
	})

	return [btn, adder]
}

function moveSection(state, config, idx, dir, i18n, container, saveBtn) {
	const target = idx + dir
	if (target < 0 || target >= state.sections.length) return
	;[state.sections[idx], state.sections[target]] = [
		state.sections[target],
		state.sections[idx],
	]
	renderSections(state, config, i18n, container, saveBtn)
}

function deleteSection(state, config, idx, i18n, container, saveBtn) {
	state.sections.splice(idx, 1)
	renderSections(state, config, i18n, container, saveBtn)
	checkValidity(state, saveBtn)
}
