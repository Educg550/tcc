import { loadSchema } from '../../common/schema.js'
import { deriveConfig } from './schema-config.js'
import {
	createInitialState,
	checkValidity,
	renderFormFields,
} from './builder.js'
import { addSection, renderSections } from './sections.js'
import { renderTags } from './tags.js'
import { serialize, deserialize } from './serializer.js'

export const element = customElements.define(
	'form-builder',
	class FormBuilder extends HTMLElement {
		async connectedCallback() {
			const saveBtn = document.querySelector('[data-builder-save]')
			if (!saveBtn) {
				this.dispatchEvent(new CustomEvent('builder:schema-error'))
				return
			}
			const tabJson = document.getElementById('tab-json')
			const tabVisual = document.getElementById('tab-visual')

			if (tabJson && tabJson.classList.contains('tab-btn--active')) {
				saveBtn.disabled = false
			}
			if (tabJson) {
				tabJson.addEventListener('click', () => {
					saveBtn.disabled = false
				})
			}
			if (tabVisual) {
				tabVisual.addEventListener('click', () => {
					this.state
						? checkValidity(this.state, saveBtn)
						: (saveBtn.disabled = true)
				})
			}

			const result = await loadSchema(this.dataset.schemaUrl)
			if (!result) {
				this.dispatchEvent(new CustomEvent('builder:schema-error'))
				return
			}
			this.config = deriveConfig(result.schema)
			if (!this.config.fieldProperties.length) {
				this.dispatchEvent(new CustomEvent('builder:schema-error'))
				return
			}
			this.validate = result.validate
			this.i18n = JSON.parse(this.dataset.i18n || '{}')

			let initialValue = null
			if (this.dataset.initialValue) {
				try {
					initialValue = JSON.parse(this.dataset.initialValue)
				} catch {
					initialValue = null
				}
			}

			this.state = initialValue
				? deserialize(initialValue, this.config)
				: createInitialState(this.config)

			const formFieldsContainer = this.querySelector('#builder-form-fields')
			const tagsContainer = this.querySelector('#builder-tags')
			const sectionsContainer = this.querySelector('#builder-sections')

			renderFormFields(
				this.state,
				this.config,
				this.i18n,
				formFieldsContainer,
				saveBtn,
			)

			if (tagsContainer) {
				const tagsTitle = document.createElement('h3')
				tagsTitle.textContent = 'Tags'
				tagsContainer.before(tagsTitle)

				renderTags(this.state, this.i18n, tagsContainer, saveBtn)
			}

			if (sectionsContainer) {
				const sectionsTitle = document.createElement('h3')
				sectionsTitle.textContent = 'Sections'
				sectionsContainer.before(sectionsTitle)

				renderSections(
					this.state,
					this.config,
					this.i18n,
					sectionsContainer,
					saveBtn,
				)
			}

			if (tabVisual && tabVisual.classList.contains('tab-btn--active')) {
				checkValidity(this.state, saveBtn)
			}

			const addSectionBtn = this.querySelector('[data-add-section]')
			if (addSectionBtn && sectionsContainer) {
				addSectionBtn.addEventListener('click', () => {
					addSection(this.state)
					renderSections(
						this.state,
						this.config,
						this.i18n,
						sectionsContainer,
						saveBtn,
					)
					checkValidity(this.state, saveBtn)
				})
			}

			const form = this.closest('form')
			if (form) {
				const textarea = form.querySelector('textarea[name="form"]')
				if (textarea && !textarea.value.trim() && initialValue) {
					textarea.value = JSON.stringify(initialValue)
				}
				form.addEventListener('submit', () => {
					if (tabVisual && tabVisual.classList.contains('tab-btn--active')) {
						if (textarea) textarea.value = serialize(this.state)
					}
				})
			}
		}
	},
)
