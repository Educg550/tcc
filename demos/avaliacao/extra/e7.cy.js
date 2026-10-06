describe("E7", () => {
  it("todo campo tem placeholder, e o placeholder não repete o rótulo", () => {
    cy.visit("/");
    cy.get("input:visible, textarea:visible").each(($el) => {
      const el = $el[0];
      const dica = (el.placeholder || "").trim();
      expect(dica, `placeholder de ${el.name || el.id || el.outerHTML.slice(0, 60)}`).to.not.be.empty;
      const rotulo = (el.labels && el.labels[0] ? el.labels[0].textContent : "").trim();
      if (rotulo) {
        expect(dica.toLocaleUpperCase("pt-BR")).to.not.equal(rotulo.toLocaleUpperCase("pt-BR"));
      }
    });
  });
});
