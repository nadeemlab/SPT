/// <reference types="cypress" />

// Welcome to Cypress!
//
// This spec file contains a variety of sample tests
// for a todo list app that are designed to demonstrate
// the power of writing tests in Cypress.
//
// To learn more about how Cypress works and
// what makes it such an awesome testing tool,
// please read our getting started guide:
// https://on.cypress.io/introduction-to-cypress

function selectRandomStudy(wait) {
  if (wait) {
    cy.intercept("GET", "**/study-names/").as("getStudyName");
    cy.wait("@getStudyName", { timeout: 0 });
  }

  cy.get("span#selectButton").contains("Select ").click();

  cy.get("div.relative.shadow-2xl div")
    .should("have.length.at.least", 5)
    .its("length")
    .then((n) => Cypress._.random(0, n - 1))
    .then((k) => {
      cy.log(`picked random index ${k}`);
      cy.get("div.relative.shadow-2xl div")
        .eq(k)
        .click()
        .then((e) => {
          cy.get("h3.bg-primary-yellow", { timeout: 10000 })
            .should("contain.text", e.text())
            .then(() => {
              cy.log("All right");
            });
        });
    });
}

describe("normal flow", () => {
  beforeEach(() => {
    cy.visit("http://localhost:5173");
    selectRandomStudy(true);
  });

  it("test analysis", () => {
    cy.get("p").contains("Next").parent().click();

    cy.intercept("GET", "**/phenotype-criteria/*").as("getPhenotypeCriteria");

    cy.get("span.px-2.hovertext")
      .should("have.length.at.least", 3)
      .its("length")
      .then((n) => [
        Cypress._.random(0, n - 1),
        Cypress._.random(0, n - 1),
        Cypress._.random(0, n - 1),
      ])
      .then((k) => {
        cy.log(`picked random index ${k}`);
        cy.get("span.px-2.hovertext").eq(k[0]).click();
        cy.get("span.px-2.hovertext").eq(k[1]).click();
        cy.get("span.px-2.hovertext").eq(k[2]).click();
      });

    cy.get("span").contains("Next").parent().click();

    cy.intercept("GET", "**/anonymous-phenotype-counts-fast/*").as(
      "getPhenotypesData",
    );

    cy.wait("@getPhenotypesData", { timeout: 20000 }).then(() => {
      cy.get("td#cell-count")
        .invoke("text")
        .should("match", /^[0-9]\d*(\.\d+)?$/);
    });
  });

  it("test restart study", () => {
    cy.get("p").contains("Reset").parent().click();

    cy.get("span")
      .contains("Select a study")
      .then(() => {
        selectRandomStudy(false);
      });
  });

  it("test view visualization plots", () => {
    cy.intercept("GET", "**/visualization-plots/*").as("visualizationPlots");

    cy.get("div#visualization").eq(1).click();

    cy.wait("@visualizationPlots", { timeout: 50000 }).then(() => {
      cy.wait(1000);
      cy.get("img.umap-image").should("have.length.at.least", 5);
    });
  });
});
