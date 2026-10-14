import { test } from "@jest/globals";
import { getDaysFromDate } from "@/app/submissions/[submissionId]/api/utils";
import expect from "expect";

test("given current date, when called getDaysFromDate, then returns Hoje", () => {
	const date = new Date();

	const result = getDaysFromDate(date.toISOString());

	expect(result).toEqual("Hoje");
});

test("given day before current date, when called getDaysFromDate, then returns Ontem", () => {
	const date = new Date();
	date.setDate(date.getDate() - 1);

	const result = getDaysFromDate(date.toISOString());

	expect(result).toEqual("Ontem");
});

test("given day before yesterday, when called getDaysFromDate, then returns 2 dias atrás", () => {
	const date = new Date();
	date.setDate(date.getDate() - 2);

	const result = getDaysFromDate(date.toISOString());

	expect(result).toEqual("2 dias atrás");
});
