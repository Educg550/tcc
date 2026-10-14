import { checkValidity, LANGUAGES } from './builder.js'

const SKIP_FIELD_PROPS = new Set(['name', 'type', 'position'])

const FIELD_LABEL_KEYS = {
	label: { pt: 'fieldLabelPt', en: 'fieldLabelEn' },
	description: { pt: 'fieldDescPt', en: 'fieldDescEn' },
	error_message: { pt: 'fieldErrorPt', en: 'fieldErrorEn' },
	placeholder: 'fieldPlaceholder',
	required: 'fieldRequired',
	disabled: 'fieldDisabled',
	validation: 'fieldValidation',
	prefix: 'fieldPrefix',
	position: 'fieldPosition',
}

function slugify(str) {
	return str
		.trim()
		.toLowerCase()
		.replace(/\s+/g, '_')
		.replace(/[^a-z0-9_]/g, '')
}

// helper para atualizar o preview dinamicamente
function updatePreviewDynamic(field, i18n, container) {
	const currentPreview = container.querySelector('.field-preview')
	if (currentPreview?.parentElement) {
		const parent = currentPreview.parentElement
		const newPreview = renderFieldPreview(field, i18n)
		parent.replaceChild(newPreview, currentPreview)
	}
}

export function addField(state, sectionIdx, type) {
	state.sections[sectionIdx].fields.push({
		_id: crypto.randomUUID(),
		type,
		name: '',
		label: { pt: '', en: '' },
		required: false,
		disabled: false,
		placeholder: '',
		description: { pt: '', en: '' },
		validation: '',
		prefix: '',
		error_message: { pt: '', en: '' },
		position: state.sections[sectionIdx].fields.length,
		options: [],
	})
}

export function renderFields(
	state,
	sectionIdx,
	config,
	i18n,
	container,
	saveBtn,
	preview,
) {
	container.innerHTML = ''
	const fields = state.sections[sectionIdx].fields
	fields.forEach((field, idx) => {
		const card = document.createElement('div')
		card.className = 'field-card'
		card.dataset.fieldType = field.type

		const fieldsDiv = document.createElement('div')
		fieldsDiv.className = 'field-buttons'

		const nameDisplay = document.createElement('span')
		nameDisplay.dataset.fieldNameDisplay = ''

		nameDisplay.textContent = ''
		//'Nome único: ' + slugify(field.label.pt) || 'Campo sem nome'

		fieldsDiv.appendChild(nameDisplay)

		const buttonsDiv = document.createElement('div')
		buttonsDiv.className = 'field-option-buttons'

		const moveUpBtn = document.createElement('button')
		moveUpBtn.type = 'button'
		moveUpBtn.dataset.moveUp = ''
		moveUpBtn.textContent = i18n.moveUp || 'Move Up'
		moveUpBtn.disabled = idx === 0
		moveUpBtn.addEventListener('click', () =>
			moveField(
				state,
				sectionIdx,
				idx,
				-1,
				config,
				i18n,
				container,
				saveBtn,
				preview,
			),
		)

		buttonsDiv.appendChild(moveUpBtn)

		const moveDownBtn = document.createElement('button')
		moveDownBtn.type = 'button'
		moveDownBtn.dataset.moveDown = ''
		moveDownBtn.textContent = i18n.moveDown || 'Move Down'
		moveDownBtn.disabled = idx === fields.length - 1
		moveDownBtn.addEventListener('click', () =>
			moveField(
				state,
				sectionIdx,
				idx,
				1,
				config,
				i18n,
				container,
				saveBtn,
				preview,
			),
		)

		buttonsDiv.appendChild(moveDownBtn)

		const deleteBtn = document.createElement('button')
		deleteBtn.type = 'button'
		deleteBtn.dataset.deleteField = ''
		deleteBtn.textContent = i18n.deleteField || 'Delete Field'
		deleteBtn.disabled = fields.length <= 1
		deleteBtn.addEventListener('click', () =>
			deleteField(state, sectionIdx, idx, config, i18n, container, saveBtn),
		)
		buttonsDiv.appendChild(deleteBtn)

		const toggleBtn = document.createElement('button')
		toggleBtn.type = 'button'
		toggleBtn.dataset.toggleFieldConfig = ''
		toggleBtn.textContent = i18n.expandConfig || 'Configure'

		buttonsDiv.appendChild(toggleBtn)

		fieldsDiv.appendChild(buttonsDiv)

		const panel = document.createElement('div')
		panel.dataset.fieldConfig = ''
		panel.hidden = true

		const fieldPreview = renderFieldPreview(field, i18n)

		toggleBtn.addEventListener('click', () => {
			if (!panel.dataset.configRendered) {
				renderFieldConfig(
					field,
					config,
					i18n,
					panel,
					state,
					saveBtn,
					nameDisplay,
					card,
				)
				panel.dataset.configRendered = '1'
			}

			panel.hidden = !panel.hidden
		})

		card.appendChild(fieldPreview)
		card.appendChild(panel)
		card.appendChild(fieldsDiv)

		container.appendChild(card)
	})
}

export function moveField(
	state,
	sectionIdx,
	fieldIdx,
	dir,
	config,
	i18n,
	container,
	saveBtn,
) {
	const fields = state.sections[sectionIdx].fields
	const target = fieldIdx + dir
	if (target < 0 || target >= fields.length) return
	;[fields[fieldIdx], fields[target]] = [fields[target], fields[fieldIdx]]
	fields[fieldIdx].position = fieldIdx
	fields[target].position = target
	renderFields(state, sectionIdx, config, i18n, container, saveBtn)
}

export function deleteField(
	state,
	sectionIdx,
	fieldIdx,
	config,
	i18n,
	container,
	saveBtn,
) {
	state.sections[sectionIdx].fields.splice(fieldIdx, 1)
	state.sections[sectionIdx].fields.forEach((f, i) => {
		f.position = i
	})
	renderFields(state, sectionIdx, config, i18n, container, saveBtn)
	checkValidity(state, saveBtn)
}

export function renderFieldConfig(
	field,
	config,
	i18n,
	container,
	state,
	saveBtn,
	nameDisplay,
	cardContainer,
) {
	container.innerHTML = ''
	config.fieldProperties.forEach((descriptor) => {
		if (SKIP_FIELD_PROPS.has(descriptor.name)) return

		if (descriptor.inputType === 'i18n')
			renderI18nInputs(
				descriptor,
				field,
				i18n,
				container,
				state,
				saveBtn,
				nameDisplay,
				cardContainer,
			)
		else if (descriptor.inputType === 'text')
			renderTextInput(
				descriptor,
				field,
				i18n,
				container,
				state,
				saveBtn,
				cardContainer,
			)
		else if (descriptor.inputType === 'checkbox')
			renderCheckboxInput(descriptor, field, i18n, container, state, saveBtn)
		else if (descriptor.inputType === 'number')
			renderNumberInput(descriptor, field, i18n, container, state, saveBtn)
		// unsupported inputTypes (e.g. array) are silently skipped
	})

	if (config.fieldTypes[field.type]?.hasOptions) {
		const addBtn = document.createElement('button')
		addBtn.type = 'button'
		addBtn.dataset.addOption = ''
		addBtn.textContent = i18n.addOption || 'Add Option'

		const list = document.createElement('ul')
		list.dataset.optionsList = ''

		addBtn.addEventListener('click', () =>
			addOption(field, i18n, list, cardContainer),
		)

		container.appendChild(addBtn)
		container.appendChild(list)

		renderOptionsList(field, i18n, list, cardContainer)
	}
}

export function addOption(field, i18n, listEl, cardContainer) {
	field.options.push({ value: { pt: '', en: '' } })
	renderOptionsList(field, i18n, listEl, cardContainer)
	updatePreviewDynamic(field, i18n, cardContainer)
}

export function renderOptionsList(field, i18n, listEl, cardContainer) {
	listEl.innerHTML = ''
	field.options.forEach((option, i) => {
		const li = document.createElement('li')

		const ptWrapper = document.createElement('div')
		const ptLabel = document.createElement('label')
		ptLabel.textContent = i18n.optionValuePt || 'Option Value (PT)'
		const ptInput = document.createElement('input')
		ptInput.type = 'text'
		ptInput.value = option.value.pt
		ptInput.dataset.optionPt = ''
		ptInput.addEventListener('input', () => {
			option.value.pt = ptInput.value
			const currentPreview = cardContainer?.querySelector('.field-preview')

			if (currentPreview?.parentElement) {
				const parent = currentPreview.parentElement
				const newPreview = renderFieldPreview(field, i18n)
				parent.replaceChild(newPreview, currentPreview)
			}
		})
		ptWrapper.appendChild(ptLabel)
		ptWrapper.appendChild(ptInput)

		const enWrapper = document.createElement('div')
		const enLabel = document.createElement('label')
		enLabel.textContent = i18n.optionValueEn || 'Option Value (EN)'
		const enInput = document.createElement('input')
		enInput.type = 'text'
		enInput.value = option.value.en
		enInput.dataset.optionEn = ''
		enInput.addEventListener('input', () => {
			option.value.en = enInput.value
			const currentPreview = cardContainer?.querySelector('.field-preview') // busca o preview atual
			if (currentPreview?.parentElement) {
				const parent = currentPreview.parentElement
				const newPreview = renderFieldPreview(field, i18n)
				parent.replaceChild(newPreview, currentPreview)
			}
		})
		enWrapper.appendChild(enLabel)
		enWrapper.appendChild(enInput)

		const upBtn = document.createElement('button')
		upBtn.type = 'button'
		upBtn.dataset.moveOptionUp = ''
		upBtn.textContent = i18n.moveUp || 'Move Up'
		upBtn.disabled = i === 0
		upBtn.addEventListener('click', () =>
			moveOption(field, i, -1, i18n, listEl, cardContainer),
		)

		const downBtn = document.createElement('button')
		downBtn.type = 'button'
		downBtn.dataset.moveOptionDown = ''
		downBtn.textContent = i18n.moveDown || 'Move Down'
		downBtn.disabled = i === field.options.length - 1
		downBtn.addEventListener('click', () =>
			moveOption(field, i, 1, i18n, listEl, cardContainer),
		)

		const delBtn = document.createElement('button')
		delBtn.type = 'button'
		delBtn.dataset.deleteOption = ''
		delBtn.textContent = i18n.deleteOption || 'Delete Option'
		delBtn.addEventListener('click', () =>
			deleteOption(field, i, i18n, listEl, cardContainer),
		)

		li.appendChild(ptWrapper)
		li.appendChild(enWrapper)
		li.appendChild(upBtn)
		li.appendChild(downBtn)
		li.appendChild(delBtn)
		listEl.appendChild(li)
	})
}

export function moveOption(field, idx, dir, i18n, listEl, cardContainer) {
	const target = idx + dir
	if (target < 0 || target >= field.options.length) return
	;[field.options[idx], field.options[target]] = [
		field.options[target],
		field.options[idx],
	]
	renderOptionsList(field, i18n, listEl, cardContainer)
	updatePreviewDynamic(field, i18n, cardContainer)
}

export function deleteOption(field, idx, i18n, listEl, cardContainer) {
	field.options.splice(idx, 1)
	renderOptionsList(field, i18n, listEl, cardContainer)

	updatePreviewDynamic(field, i18n, cardContainer)
}

function renderI18nInputs(
	descriptor,
	field,
	i18n,
	container,
	state,
	saveBtn,
	nameDisplay,
	cardContainer,
) {
	if (
		typeof field[descriptor.name] !== 'object' ||
		field[descriptor.name] === null
	) {
		throw new Error(
			`renderI18nInputs: field.${descriptor.name} is not an i18n object. Add it to addField().`,
		)
	}

	const keys = FIELD_LABEL_KEYS[descriptor.name] || {}

	const wrapper = document.createElement('div')
	wrapper.className = 'i18n-field'

	const title = document.createElement('label')
	title.className = 'i18n-field-label'
	title.textContent = i18n[keys.pt] || i18n[keys.en] || descriptor.name

	wrapper.appendChild(title)

	const tabs = document.createElement('div')
	tabs.className = 'i18n-tabs'

	const inputs = document.createElement('div')
	inputs.className = 'i18n-inputs'

	let activeLanguage = LANGUAGES[0]

	function renderLanguage(lang) {
		inputs.innerHTML = ''

		const input = document.createElement('input')
		input.type = 'text'
		input.value = field[descriptor.name][lang]

		input.className = 'i18n-input'

		if (descriptor.isRequired && lang === 'pt') {
			input.required = true
		}

		input.addEventListener('input', () => {
			field[descriptor.name][lang] = input.value

			if (descriptor.name === 'label' && lang === 'pt') {
				const slug = slugify(input.value)

				field.name = slug

				if (nameDisplay) {
					nameDisplay.textContent = slug
				}
			}

			updatePreviewDynamic(field, i18n, cardContainer)
			checkValidity(state, saveBtn)
		})

		inputs.appendChild(input)
	}

	LANGUAGES.forEach((lang) => {
		const tab = document.createElement('button')

		tab.type = 'button'
		tab.className = 'i18n-tab'
		tab.textContent = lang.toUpperCase()

		tab.addEventListener('click', () => {
			activeLanguage = lang

			tabs.querySelectorAll('.i18n-tab').forEach((button) => {
				button.classList.remove('active')
			})

			tab.classList.add('active')

			renderLanguage(activeLanguage)
		})

		tabs.appendChild(tab)
	})

	const firstTab = tabs.querySelector('.i18n-tab')

	if (firstTab) {
		firstTab.classList.add('active')
	}

	wrapper.appendChild(tabs)
	wrapper.appendChild(inputs)

	container.appendChild(wrapper)

	renderLanguage(activeLanguage)
}

function renderFieldPreview(field, i18n) {
	const preview = document.createElement('div')
	preview.className = 'field-preview'

	const label = document.createElement('div')
	label.className = 'field-preview-label'
	label.textContent =
		(field.label.pt || 'Sem título') + (field.required ? ' *' : '')

	preview.appendChild(label)

	if (field.description.pt) {
		const description = document.createElement('div')
		description.className = 'field-preview-description'
		description.textContent = field.description.pt
		preview.appendChild(description)
	}

	switch (field.type) {
		case 'Text':
		case 'Number':
		case 'Date':
			{
				const input = document.createElement('input')
				input.className = 'field-preview-input'
				input.type =
					field.type === 'Number'
						? 'number'
						: field.type === 'Date'
							? 'date'
							: 'text'

				input.placeholder = field.placeholder || ''
				input.disabled = true

				preview.appendChild(input)
			}
			break

		case 'LongText':
			{
				const textarea = document.createElement('textarea')
				textarea.className = 'field-preview-input'
				textarea.placeholder = field.placeholder || ''
				textarea.disabled = true

				preview.appendChild(textarea)
			}
			break

		case 'Radio':
			const radioDiv = document.createElement('div')
			radioDiv.className = 'preview-checkboxes'
			field.options.forEach((option) => {
				const label = document.createElement('label')

				const input = document.createElement('input')
				input.type = 'radio'
				input.disabled = true

				label.appendChild(input)
				label.append(` ${option.value.pt || option.value.en || ''}`)

				radioDiv.appendChild(label)
			})
			preview.appendChild(radioDiv)
			break

		case 'CheckBox':
			const checkboxDiv = document.createElement('div')
			checkboxDiv.className = 'preview-checkboxes'
			field.options.forEach((option) => {
				const label = document.createElement('label')

				const input = document.createElement('input')
				input.type = 'checkbox'
				input.disabled = true

				label.appendChild(input)
				label.append(` ${option.value.pt || option.value.en || ''}`)

				checkboxDiv.appendChild(label)
			})
			preview.appendChild(checkboxDiv)
			break

		case 'File':
			{
				const input = document.createElement('input')
				input.className = 'field-preview-input'
				input.type = 'file'
				input.disabled = true

				preview.appendChild(input)
			}
			break
	}

	return preview
}

function updateFieldPreview(field, preview) {
	if (!preview) return

	const label = preview.querySelector('.field-preview-label')

	if (label) {
		label.textContent =
			(field.label.pt || 'Sem título') + (field.required ? ' *' : '')
	}

	const description = preview.querySelector('.field-preview-description')

	if (description) {
		description.textContent = field.description.pt || ''
		description.hidden = !field.description.pt
	}

	const input = preview.querySelector('.field-preview-input')

	if (input) {
		input.placeholder = field.placeholder || ''
		input.disabled = field.disabled
	}
}

function renderTextInput(
	descriptor,
	field,
	i18n,
	container,
	state,
	saveBtn,
	cardContainer,
) {
	const wrapper = document.createElement('div')
	const lbl = document.createElement('label')
	lbl.textContent = i18n[FIELD_LABEL_KEYS[descriptor.name]] || descriptor.name
	const input = document.createElement('input')
	input.type = 'text'
	input.value = field[descriptor.name]
	if (descriptor.isRequired) input.required = true
	input.addEventListener('input', () => {
		field[descriptor.name] = input.value

		updatePreviewDynamic(field, i18n, cardContainer)
		checkValidity(state, saveBtn)
	})
	wrapper.appendChild(lbl)
	wrapper.appendChild(input)
	container.appendChild(wrapper)
}

function renderCheckboxInput(
	descriptor,
	field,
	i18n,
	container,
	state,
	saveBtn,
) {
	const wrapper = document.createElement('div')
	const lbl = document.createElement('label')
	lbl.textContent = i18n[FIELD_LABEL_KEYS[descriptor.name]] || descriptor.name
	const input = document.createElement('input')
	input.type = 'checkbox'
	input.checked = field[descriptor.name]
	if (descriptor.isRequired) input.required = true
	input.addEventListener('change', () => {
		field[descriptor.name] = input.checked
		checkValidity(state, saveBtn)
	})
	wrapper.appendChild(lbl)
	wrapper.appendChild(input)
	container.appendChild(wrapper)
}

function renderNumberInput(descriptor, field, i18n, container, state, saveBtn) {
	const wrapper = document.createElement('div')
	const lbl = document.createElement('label')
	lbl.textContent = i18n[FIELD_LABEL_KEYS[descriptor.name]] || descriptor.name
	const input = document.createElement('input')
	input.type = 'number'
	input.value = field[descriptor.name]
	if (descriptor.isRequired) input.required = true
	input.addEventListener('input', () => {
		const n = Number(input.value)
		if (!Number.isNaN(n)) field[descriptor.name] = n
		checkValidity(state, saveBtn)
	})
	wrapper.appendChild(lbl)
	wrapper.appendChild(input)
	container.appendChild(wrapper)
}
