const assert = require("assert");
const fs = require("fs");
const path = require("path");
const {
  checkEligibility,
  evaluateAllSchemes,
  normalizeProfile,
} = require("./eligibilityEngine");

const db = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, "..", "data", "schemes.json"), "utf-8")
);

function getScheme(id) {
  const scheme = db.schemes.find((entry) => entry.id === id);
  if (!scheme) throw new Error(`Missing scheme ${id} in test fixture`);
  return scheme;
}

function testFullyEligible() {
  const user = normalizeProfile({
    age: 32,
    annualIncome: 540000,
    gender: "male",
    occupation: "salaried",
    caste: "general",
    state: "maharashtra",
    hasHouse: false,
    hasBankAccount: true,
    numberOfChildren: 1,
    hasGirlChildBelow10: true,
  });

  const result = checkEligibility(user, getScheme("pmjjby"));
  assert.strictEqual(result.status, "eligible");
  assert.ok(result.matchScore >= 50);
}

function testPartiallyEligible() {
  const user = normalizeProfile({
    age: 30,
    annualIncome: 300000,
    gender: "male",
    occupation: "salaried",
    caste: "general",
    state: "maharashtra",
    hasBankAccount: false,
  });

  const result = checkEligibility(user, getScheme("pmsby"));
  assert.strictEqual(result.status, "eligible");
  assert.ok(result.criteriaResults.some((r) => r.met === false));
}

function testIncomeBoundary() {
  const user = normalizeProfile({
    age: 28,
    annualIncome: 250000,
    gender: "female",
    occupation: "self-employed",
    state: "maharashtra",
  });

  const result = checkEligibility(user, getScheme("ladki_bahin"));
  assert.strictEqual(result.status, "eligible");
}

function testAgeBoundary() {
  const user = normalizeProfile({
    age: 18,
    annualIncome: 180000,
    gender: "male",
    occupation: "unemployed",
    hasBankAccount: true,
    state: "karnataka",
  });

  const result = checkEligibility(user, getScheme("apy"));
  assert.strictEqual(result.status, "eligible");
}

function testStateSpecificFilter() {
  const user = normalizeProfile({
    age: 29,
    annualIncome: 400000,
    gender: "female",
    occupation: "self-employed",
    state: "gujarat",
    hasBankAccount: true,
  });

  const result = evaluateAllSchemes(user, db.schemes);
  assert.ok(result.schemes.every((scheme) => scheme.state === "all" || scheme.state === "gujarat"));
  const mahaswayamShown = result.schemes.some((scheme) => scheme.id === "mahaswayam");
  assert.strictEqual(mahaswayamShown, false);
}

function run() {
  testFullyEligible();
  testPartiallyEligible();
  testIncomeBoundary();
  testAgeBoundary();
  testStateSpecificFilter();
  // eslint-disable-next-line no-console
  console.log("eligibilityEngine.test.js: all tests passed");
}

run();
