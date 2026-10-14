describe('Form creation via Visual builder — form-level inputs', () => {
	beforeEach(() => {
		cy.visit('/pt/form/')
		cy.get('.visualization__new--item').click()
		cy.get('popup-element form-builder', { timeout: 10000 }).should('exist')
		cy.get('popup-element #tab-visual').click()
		cy.get('form-builder #builder-form-fields input', {
			timeout: 10000,
		}).should('exist')
	})

	it('validates form-level inputs and tag constraints', () => {
		// AC1: inputs and tags section visible
		cy.get('form-builder #builder-form-fields')
			.find('input')
			.should('have.length.gte', 2)
		cy.get('form-builder #builder-tags').should('exist')
		cy.get('form-builder #builder-tags [data-add-tag]').should('exist')

		// AC2: Save disabled on load
		cy.get('[data-builder-save]').should('be.disabled')

		// AC3: Save still disabled with only title filled
		cy.get('form-builder #builder-form-fields input')
			.first()
			.type('My Form Title')
		cy.get('[data-builder-save]').should('be.disabled')

		// AC5: last tag delete button is disabled; enabled when a second tag exists; disabled again after delete
		cy.get('form-builder #builder-tags [data-delete-tag]').should('be.disabled')
		cy.get('form-builder #builder-tags [data-add-tag]').click()
		cy.get('form-builder #builder-tags [data-delete-tag]').should(
			'not.be.disabled',
		)
		cy.get('form-builder #builder-tags [data-delete-tag]').first().click()
		cy.get('form-builder #builder-tags [data-delete-tag]').should('be.disabled')

		// AC4: Save enabled after title + valid tag key/value + a section with a title and a field
		cy.get('form-builder #builder-tags').find('input').eq(0).type('my-key')
		cy.get('form-builder #builder-tags').find('input').eq(1).type('my-value')
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.type('My Section')
		// A section with no field keeps Save disabled, so add one before asserting
		cy.get('[data-builder-save]').should('be.disabled')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type-select]')
			.select('Text')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field-confirm]')
			.click()
		// A field with no label.pt keeps Save disabled; expand config and fill it
		cy.get('[data-builder-save]').should('be.disabled')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-toggle-field-config]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-field-config] input[required]')
			.type('My Label')
		cy.get('[data-builder-save]').should('not.be.disabled')
	})

	it('creates a form via Visual tab', () => {
		const title = `Test Visual Form ${Date.now()}`
		cy.get('form-builder #builder-form-fields input').first().type(title)
		cy.get('form-builder #builder-tags').find('input').eq(0).type('my-key')
		cy.get('form-builder #builder-tags').find('input').eq(1).type('my-value')
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.type('My Section')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type-select]')
			.select('Text')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field-confirm]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-toggle-field-config]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-field-config] input[required]')
			.type('My Label')
		cy.get('[data-builder-save]').click()
		cy.url().should('include', '/pt/form/')
		cy.contains(title).should('exist')

		// Section now carries a field, so the viewer renders the form (no longer 404)
		cy.contains(title).click()
		cy.url().should('include', '/pt/form/viewer/')
		cy.get('h1').should('contain', title)
	})
})

describe('Form creation via Visual builder — section management', () => {
	beforeEach(() => {
		cy.visit('/pt/form/')
		cy.get('.visualization__new--item').click()
		cy.get('popup-element form-builder', { timeout: 10000 }).should('exist')
		cy.get('popup-element #tab-visual').click()
		cy.get('form-builder #builder-form-fields input', {
			timeout: 10000,
		}).should('exist')
	})

	it('manages sections — add, reorder, delete', () => {
		// AC1: Add Section button exists; click it; assert 1 card with 4 inputs
		cy.get('[data-add-section]').should('exist')
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections').children().should('have.length', 1)
		cy.get('#builder-sections').find('input').should('have.length', 4)

		// AC4: Delete disabled when only 1 section
		cy.get('[data-delete-section]').should('be.disabled')

		// Add second section; both delete buttons now enabled
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections [data-delete-section]').each(($btn) => {
			cy.wrap($btn).should('not.be.disabled')
		})

		// Type titles so reorder assertions are unambiguous
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.type('Section A')
		cy.get('#builder-sections')
			.children()
			.eq(1)
			.find('input')
			.eq(0)
			.type('Section B')

		// AC3: Move first card down — Section B should now be first
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-move-down]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.should('have.value', 'Section B')
		cy.get('#builder-sections')
			.children()
			.eq(1)
			.find('input')
			.eq(0)
			.should('have.value', 'Section A')

		// AC2: Move second card up — order restored
		cy.get('#builder-sections').children().eq(1).find('[data-move-up]').click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.should('have.value', 'Section A')
		cy.get('#builder-sections')
			.children()
			.eq(1)
			.find('input')
			.eq(0)
			.should('have.value', 'Section B')

		// AC5: Delete second section — only Section A remains
		cy.get('#builder-sections')
			.children()
			.eq(1)
			.find('[data-delete-section]')
			.click()
		cy.get('#builder-sections').children().should('have.length', 1)
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.should('have.value', 'Section A')
	})

	it('happy path — creates form with a section via Visual tab', () => {
		const title = `Test Visual Form Section ${Date.now()}`
		cy.get('form-builder #builder-form-fields input').first().type(title)
		cy.get('form-builder #builder-tags').find('input').eq(0).type('my-key')
		cy.get('form-builder #builder-tags').find('input').eq(1).type('my-value')
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.type('My Section')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type-select]')
			.select('Text')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field-confirm]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-toggle-field-config]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-field-config] input[required]')
			.type('My Label')
		cy.get('[data-builder-save]').click()
		cy.url().should('include', '/pt/form/')
		cy.contains(title).should('exist')
	})
})

describe('Form creation via Visual builder — field management', () => {
	// Mirrors typeRegistry keys in
	// static-assets/scripts/components/FormBuilder/schema-config.js
	const TYPE_KEYS = [
		'Text',
		'LongText',
		'Number',
		'Radio',
		'CheckBox',
		'Date',
		'File',
	]

	beforeEach(() => {
		cy.visit('/pt/form/')
		cy.get('.visualization__new--item').click()
		cy.get('popup-element form-builder', { timeout: 10000 }).should('exist')
		cy.get('popup-element #tab-visual').click()
		cy.get('form-builder #builder-form-fields input', {
			timeout: 10000,
		}).should('exist')
		// Story 2.3 manages fields within a section, so start with one section present
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections').children().should('have.length', 1)
	})

	it('manages fields — add, type selector, reorder, delete', () => {
		const section = () => cy.get('#builder-sections').children().eq(0)
		// Field cards are the only elements carrying a data-field-type attribute
		const cards = () => section().find('[data-field-type]')

		// AC1: Add Field reveals a type select populated from the registry (and no others)
		section().find('[data-add-field]').click()
		section().find('[data-field-type-select]').should('be.visible')
		section()
			.find('[data-field-type-select] option')
			.then(($opts) => {
				const values = [...$opts].map((o) => o.value)
				expect(values).to.deep.equal(TYPE_KEYS)
			})

		// AC2: select a type, confirm -> one field card with that type at the bottom
		section().find('[data-field-type-select]').select('Text')
		section().find('[data-add-field-confirm]').click()
		cards().should('have.length', 1)
		cards().eq(0).should('have.attr', 'data-field-type', 'Text')

		// AC5: Delete Field disabled when exactly one field exists
		section().find('[data-delete-field]').should('be.disabled')

		// Add a second, distinct field type so reorder assertions are unambiguous
		section().find('[data-add-field]').click()
		section().find('[data-field-type-select]').select('LongText')
		section().find('[data-add-field-confirm]').click()
		cards().should('have.length', 2)
		section()
			.find('[data-delete-field]')
			.each(($btn) => {
				cy.wrap($btn).should('not.be.disabled')
			})

		// AC4: Move first field down -> LongText leads, Text follows
		cards().eq(0).find('[data-move-down]').click()
		cards().eq(0).should('have.attr', 'data-field-type', 'LongText')
		cards().eq(1).should('have.attr', 'data-field-type', 'Text')

		// AC3: Move second field up -> original order restored
		cards().eq(1).find('[data-move-up]').click()
		cards().eq(0).should('have.attr', 'data-field-type', 'Text')
		cards().eq(1).should('have.attr', 'data-field-type', 'LongText')

		// AC6: Delete second field -> only Text remains
		cards().eq(1).find('[data-delete-field]').click()
		cards().should('have.length', 1)
		cards().eq(0).should('have.attr', 'data-field-type', 'Text')
	})

	it('happy path — creates form with section and field via Visual tab', () => {
		const title = `Test Visual Form Field ${Date.now()}`
		cy.get('form-builder #builder-form-fields input').first().type(title)
		cy.get('form-builder #builder-tags').find('input').eq(0).type('my-key')
		cy.get('form-builder #builder-tags').find('input').eq(1).type('my-value')
		// section was added in beforeEach
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.type('My Section')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type-select]')
			.select('Text')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field-confirm]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-toggle-field-config]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-field-config] input[required]')
			.type('My Label')
		cy.get('[data-builder-save]').click()
		cy.url().should('include', '/pt/form/')
		cy.contains(title).should('exist')
	})
})

describe('Form creation via Visual builder — field configuration panel', () => {
	beforeEach(() => {
		cy.visit('/pt/form/')
		cy.get('.visualization__new--item').click()
		cy.get('popup-element form-builder', { timeout: 10000 }).should('exist')
		cy.get('popup-element #tab-visual').click()
		cy.get('form-builder #builder-form-fields input', {
			timeout: 10000,
		}).should('exist')
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.type('My Section')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type-select]')
			.select('Text')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field-confirm]')
			.click()
	})

	it('field config panel — inputs, required attribute, validity', () => {
		// Fill everything except label-pt so it is the sole missing save prerequisite
		cy.get('form-builder #builder-form-fields input')
			.first()
			.type('My Form Title')
		cy.get('form-builder #builder-tags').find('input').eq(0).type('my-key')
		cy.get('form-builder #builder-tags').find('input').eq(1).type('my-value')

		const card = () =>
			cy
				.get('#builder-sections')
				.children()
				.eq(0)
				.find('[data-field-type]')
				.eq(0)
		const panel = () => card().find('[data-field-config]')

		// AC1: clicking the toggle reveals the config panel
		card().find('[data-toggle-field-config]').scrollIntoView().click()
		panel().scrollIntoView().should('be.visible')

		// AC1: panel has text inputs (label-pt/en and other string properties)
		//      and checkbox inputs (required, disabled); options (array) and
		//      position (integer) are skipped — no number input
		panel().find('input[type="text"]').should('have.length.gte', 1)
		panel().find('input[type="checkbox"]').should('have.length.gte', 1)
		panel().find('input[type="number"]').should('have.length', 0)

		// AC2: label-pt is the required input and is a text input
		panel()
			.find('input[required]')
			.should('have.length', 1)
			.and('have.attr', 'type', 'text')

		// AC3: save disabled while label-pt is empty
		cy.get('[data-builder-save]').should('be.disabled')

		// AC4: filling label-pt enables save
		panel().find('input[required]').type('My Label')
		cy.get('[data-builder-save]').should('not.be.disabled')

		// AC3 round-trip: clearing label-pt disables save again
		panel().find('input[required]').clear({ force: true })
		cy.get('[data-builder-save]').should('be.disabled')
	})

	it('happy path — creates form with configured field', () => {
		const title = `Test Visual Form Config ${Date.now()}`
		cy.get('form-builder #builder-form-fields input').first().type(title)
		cy.get('form-builder #builder-tags').find('input').eq(0).type('my-key')
		cy.get('form-builder #builder-tags').find('input').eq(1).type('my-value')
		// section + field added in beforeEach
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-toggle-field-config]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-field-config] input[required]')
			.type('My Label')
		cy.get('[data-builder-save]').click()
		cy.url().should('include', '/pt/form/')
		cy.contains(title).should('exist')
	})
})

describe('Form creation via Visual builder — options panel', () => {
	beforeEach(() => {
		cy.visit('/pt/form/')
		cy.get('.visualization__new--item').click()
		cy.get('popup-element form-builder', { timeout: 10000 }).should('exist')
		cy.get('popup-element #tab-visual').click()
		cy.get('form-builder #builder-form-fields input', {
			timeout: 10000,
		}).should('exist')
		cy.get('[data-add-section]').click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('input')
			.eq(0)
			.type('My Section')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type-select]')
			.select('Radio')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field-confirm]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-toggle-field-config]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(0)
			.find('[data-field-config] input[required]')
			.type('My Radio Label')
	})

	it('options panel — add, reorder, delete, hidden for non-option types', () => {
		const fieldConfig = () =>
			cy
				.get('#builder-sections')
				.children()
				.eq(0)
				.find('[data-field-type]')
				.eq(0)
				.find('[data-field-config]')

		// AC1: [data-add-option] is visible and the options list is empty
		fieldConfig()
			.find('[data-add-option]')
			.scrollIntoView()
			.should('be.visible')
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.should('have.length', 0)

		// AC2: click Add Option -> 1 row appears with pt and en inputs
		fieldConfig().find('[data-add-option]').click()
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.should('have.length', 1)
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(0)
			.find('[data-option-pt]')
			.should('exist')
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(0)
			.find('[data-option-en]')
			.should('exist')

		// AC3: add a second option, type values, move first down, assert swap, move back
		fieldConfig().find('[data-add-option]').click()
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.should('have.length', 2)
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(0)
			.find('[data-option-pt]')
			.type('Option A')
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(1)
			.find('[data-option-pt]')
			.type('Option B')
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(0)
			.find('[data-move-option-down]')
			.click()
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(0)
			.find('[data-option-pt]')
			.should('have.value', 'Option B')
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(1)
			.find('[data-option-pt]')
			.should('have.value', 'Option A')
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(1)
			.find('[data-move-option-up]')
			.click()
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(0)
			.find('[data-option-pt]')
			.should('have.value', 'Option A')
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(1)
			.find('[data-option-pt]')
			.should('have.value', 'Option B')

		// AC4: delete second option -> only 1 row remains
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(1)
			.find('[data-delete-option]')
			.click()
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.should('have.length', 1)

		// AC5: add a Text field, expand its config, assert [data-add-option] is NOT present
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type-select]')
			.select('Text')
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-add-field-confirm]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(1)
			.find('[data-toggle-field-config]')
			.click()
		cy.get('#builder-sections')
			.children()
			.eq(0)
			.find('[data-field-type]')
			.eq(1)
			.find('[data-field-config]')
			.find('[data-add-option]')
			.should('not.exist')
	})

	it('happy path — creates form with radio field and options', () => {
		const title = `Test Visual Form Radio ${Date.now()}`
		cy.get('form-builder #builder-form-fields input').first().type(title)
		cy.get('form-builder #builder-tags').find('input').eq(0).type('my-key')
		cy.get('form-builder #builder-tags').find('input').eq(1).type('my-value')
		// section + Radio field + label filled in beforeEach
		const fieldConfig = () =>
			cy
				.get('#builder-sections')
				.children()
				.eq(0)
				.find('[data-field-type]')
				.eq(0)
				.find('[data-field-config]')
		fieldConfig().find('[data-add-option]').click()
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(0)
			.find('[data-option-pt]')
			.type('Choice 1')
		fieldConfig().find('[data-add-option]').click()
		fieldConfig()
			.find('[data-options-list]')
			.children()
			.eq(1)
			.find('[data-option-pt]')
			.type('Choice 2')
		cy.get('[data-builder-save]').click()
		cy.url().should('include', '/pt/form/')
		cy.contains(title).should('exist')
	})
})

describe('Form creation via JSON input', () => {
	it('creates a form from a valid JSON schema', () => {
		cy.fixture('valid-form.json').then((form) => {
			// Title must be a {pt, en} object — the SQL query uses title ->> 'pt' for filtering
			const ptTitle = `Cypress E2E Test Form ${Date.now()}`
			const payload = { ...form, title: { pt: ptTitle, en: ptTitle } }

			cy.visit('/pt/form/')

			cy.get('.visualization__new--item').click()
			cy.get('popup-element').should('exist')
			cy.get('popup-element #tab-json').click()

			// Wait for the popup to finish loading the create form via fetch
			cy.get('popup-element textarea[name="form"]', { timeout: 10000 }).should(
				'exist',
			)

			cy.setCodeMirrorValue(
				'popup-element textarea[name="form"]',
				JSON.stringify(payload, null, 2),
			)

			cy.get('popup-element input[type="submit"]').click()

			cy.url().should('include', '/pt/form/')
			cy.contains(ptTitle).should('exist')

			cy.contains(ptTitle).click()
			cy.url().should('include', '/pt/form/viewer/')
			cy.get('h1').should('contain', ptTitle)
		})
	})

	it('shows an error when submitting empty JSON', () => {
		cy.visit('/pt/form/')

		cy.get('.visualization__new--item').click()
		cy.get('popup-element').should('exist')
		cy.get('popup-element #tab-json').click()
		cy.get('popup-element textarea[name="form"]', { timeout: 10000 }).should(
			'exist',
		)

		// Leave the textarea empty and submit
		cy.get('popup-element input[type="submit"]').click()

		// Flask redirects back to /pt/form/ with a flash error message rendered by <message-info>
		cy.url().should('include', '/pt/form/')
		cy.get('message-info .message-info--error').should('exist')
	})
})
