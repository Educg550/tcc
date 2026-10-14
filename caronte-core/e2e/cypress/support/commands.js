// Sets the value of a CodeMirror 6 editor whose content is managed by <resizer-text>.
// The component syncs CodeMirror→textarea via updatePreview() on docChanged.
// We dispatch a transaction directly so the sync runs and textarea.value is correct at submit.
Cypress.Commands.add('setCodeMirrorValue', (selector, value) => {
  cy.get(selector, { force: true }).then($textarea => {
    const resizerEl = $textarea[0].closest('resizer-text')
    // Schema loading is async; wait until the EditorView is mounted before dispatching
    // .should() yields the raw DOM element; .then() yields a jQuery wrapper — handle both
    const unwrap = el => el[0] || el
    cy.wrap(resizerEl).should(el => {
      expect(unwrap(el).view, 'CodeMirror view').to.not.be.undefined
    })
    cy.wrap(resizerEl).then(el => {
      const domEl = unwrap(el)
      domEl.view.dispatch({
        changes: { from: 0, to: domEl.view.state.doc.length, insert: value },
      })
    })
  })
})
