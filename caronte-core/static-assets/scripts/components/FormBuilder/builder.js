export const LANGUAGES = ['pt', 'en']

export function createInitialState(config) {
	const state = {
		_tagIds: [{ id: crypto.randomUUID(), key: '', value: '' }],
		sections: [],
	}
	config.topLevelI18nFields.forEach(({ name }) => {
		state[name] = Object.fromEntries(LANGUAGES.map((l) => [l, '']))
	})
	return state
}

export function checkValidity(state, saveBtn) {
	const valid =
		(state.title?.pt || '').trim() !== '' &&
		Array.isArray(state._tagIds) &&
		state._tagIds.length >= 1 &&
		state._tagIds.every(
			(t) => (t.key || '').trim() !== '' && (t.value || '').trim() !== '',
		) &&
		Array.isArray(state.sections) &&
		state.sections.length >= 1 &&
		state.sections.every(
			(s) =>
				(s.title?.pt || '').trim() !== '' &&
				Array.isArray(s.fields) &&
				s.fields.length >= 1 &&
				s.fields.every((f) => (f.label?.pt || '').trim() !== ''),
		)

	saveBtn.disabled = !valid
}
export function renderFormFields(state, config, i18n, container, saveBtn) {
	config.topLevelI18nFields.forEach(({ name, required }) => {
		LANGUAGES.forEach((lang, idx) => {
			const i18nKey = name + lang.charAt(0).toUpperCase() + lang.slice(1)

			const wrapper = document.createElement('div')
			wrapper.className = 'builder-field'

			const lbl = document.createElement('label')
			lbl.textContent = i18n[i18nKey] || `${name} (${lang.toUpperCase()})`

			console.log(name)
			const input = document.createElement(
				name === 'description' ? 'textarea' : 'input',
			)
			if (name !== 'description') input.type = 'text'
			input.value = state[name]?.[lang] ?? ''
			if (required && idx === 0) input.required = true

			input.addEventListener('input', () => {
				state[name][lang] = input.value
				checkValidity(state, saveBtn)
			})

			wrapper.appendChild(lbl)
			wrapper.appendChild(input)
			container.appendChild(wrapper)
		})
	})
}
