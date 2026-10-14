import { LANGUAGES } from './builder.js'

const EMPTY_SECTION = {
	title: { pt: '', en: '' },
	description: { pt: '', en: '' },
	fields: [],
}

export function serialize(state) {
	const tags = {}
	if (Array.isArray(state._tagIds)) {
		state._tagIds.forEach((t) => {
			const k = (t.key || '').trim()
			if (k) {
				tags[k] = (t.value || '').trim()
			}
		})
	}

	return JSON.stringify({
		title: state.title,
		description: state.description,
		tags,
		sections: state.sections.map((section, sIdx) => ({
			position: sIdx,
			title: section.title,
			description: section.description,
			fields: section.fields.map((field, fIdx) => ({
				...field,
				position: fIdx,
			})),
		})),
	})
}

function emptyI18n() {
	return Object.fromEntries(LANGUAGES.map((l) => [l, '']))
}

function normalizeField(raw, idx) {
	return {
		_id: raw._id || crypto.randomUUID(),
		type: raw.type || 'text',
		name: raw.name || '',
		label: { ...emptyI18n(), ...(raw.label || {}) },
		required: raw.required ?? false,
		disabled: raw.disabled ?? false,
		placeholder: raw.placeholder ?? '',
		description: { ...emptyI18n(), ...(raw.description || {}) },
		validation: raw.validation ?? '',
		prefix: raw.prefix ?? '',
		error_message: { ...emptyI18n(), ...(raw.error_message || {}) },
		position: raw.position ?? idx,
		options: Array.isArray(raw.options)
			? raw.options.map((o) => ({
					value: { ...emptyI18n(), ...(o.value || {}) },
				}))
			: [],
	}
}

function normalizeSection(raw) {
	return {
		_id: raw._id || crypto.randomUUID(),
		title: { ...emptyI18n(), ...(raw.title || {}) },
		description: { ...emptyI18n(), ...(raw.description || {}) },
		fields: Array.isArray(raw.fields) ? raw.fields.map(normalizeField) : [],
	}
}

// Inverse of serialize(): turns a previously-saved form (as returned by
// serialize/JSON.parse) back into the internal `state` shape.
export function deserialize(raw, config) {
	const rawTags = raw.tags || {}

	// Converte {"Ano": "2100"} diretamente no array que o tags.js espera em _tagIds
	const tagList = Object.entries(rawTags).map(([key, value]) => ({
		id: crypto.randomUUID(),
		key: String(key ?? ''),
		value: String(value ?? ''),
	}))

	// Se a lista vier vazia, garante pelo menos um item inicial para não quebrar a UI
	if (tagList.length === 0) {
		tagList.push({ id: crypto.randomUUID(), key: '', value: '' })
	}

	return {
		_tagIds: tagList,
		title:
			typeof raw.title === 'object' && raw.title !== null
				? raw.title
				: { pt: raw.title || '', en: raw.title || '' },
		description:
			typeof raw.description === 'object' && raw.description !== null
				? raw.description
				: { pt: raw.description || '', en: raw.description || '' },
		sections: (raw.sections || []).map((section) => ({
			_id: crypto.randomUUID(),
			title:
				typeof section.title === 'object' && section.title !== null
					? section.title
					: { pt: section.title || '', en: section.title || '' },
			description:
				typeof section.description === 'object' && section.description !== null
					? section.description
					: { pt: section.description || '', en: section.description || '' },
			position: section.position ?? 0,
			fields: (section.fields || []).map((field, idx) => ({
				_id: crypto.randomUUID(),
				type: field.type || 'Text',
				name: field.name || '',
				label:
					typeof field.label === 'object' && field.label !== null
						? field.label
						: { pt: field.label || '', en: field.label || '' },
				required: Boolean(field.required),
				disabled: Boolean(field.disabled),
				placeholder: field.placeholder || '',
				description:
					typeof field.description === 'object' && field.description !== null
						? field.description
						: { pt: field.description || '', en: field.description || '' },
				validation: field.validation || '',
				prefix: field.prefix || '',
				error_message:
					typeof field.error_message === 'object' &&
					field.error_message !== null
						? field.error_message
						: { pt: field.error_message || '', en: field.error_message || '' },
				position: field.position ?? idx,
				options: (field.options || []).map((opt) => ({
					value:
						typeof opt === 'string'
							? { pt: opt, en: opt }
							: opt.value || { pt: '', en: '' },
				})),
			})),
		})),
	}
}
export function slugify() {}
