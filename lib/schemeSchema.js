const ALLOWED_TYPES = ["central", "state"];
const ALLOWED_STATES = ["all", "maharashtra"];
const ALLOWED_CATEGORIES = [
  "banking",
  "insurance",
  "pension",
  "housing",
  "business",
  "farming",
  "tax",
  "savings",
  "skill",
  "women",
  "health",
  "education",
  "social",
];

const ALLOWED_CRITERIA_TYPES = [
  "age_range",
  "income_max",
  "income_min",
  "gender",
  "occupation",
  "caste",
  "state",
  "house_status",
  "children",
  "always_eligible",
  "soft_requirement",
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function isValidStateValue(value) {
  if (ALLOWED_STATES.includes(value)) return true;
  return typeof value === "string" && value.trim().length > 2;
}

function validateCriterion(criterion, schemeId, index) {
  assert(criterion && typeof criterion === "object", `Scheme ${schemeId}: criterion[${index}] must be object.`);
  assert(typeof criterion.criteriaId === "string" && criterion.criteriaId.length > 1, `Scheme ${schemeId}: criterion[${index}] missing criteriaId.`);
  assert(typeof criterion.label === "string" && criterion.label.length > 1, `Scheme ${schemeId}: criterion[${index}] missing label.`);
  assert(typeof criterion.labelMarathi === "string", `Scheme ${schemeId}: criterion[${index}] missing labelMarathi.`);
  assert(typeof criterion.labelHindi === "string", `Scheme ${schemeId}: criterion[${index}] missing labelHindi.`);
  assert(ALLOWED_CRITERIA_TYPES.includes(criterion.type), `Scheme ${schemeId}: invalid criterion type ${criterion.type}.`);
  assert(criterion.params && typeof criterion.params === "object", `Scheme ${schemeId}: criterion[${index}] params must be object.`);
}

function validateScheme(scheme, index) {
  assert(scheme && typeof scheme === "object", `Scheme at index ${index} must be object.`);

  const requiredStringFields = [
    "id",
    "name",
    "nameMarathi",
    "nameHindi",
    "description",
    "descriptionMarathi",
    "descriptionHindi",
    "applicationProcess",
    "applyUrl",
    "deadline",
    "rbiCircularRef",
    "lastUpdated",
  ];

  requiredStringFields.forEach((field) => {
    assert(typeof scheme[field] === "string" && scheme[field].trim().length > 0, `Scheme ${scheme.id || index}: invalid ${field}.`);
  });

  assert(ALLOWED_TYPES.includes(scheme.type), `Scheme ${scheme.id}: type must be central/state.`);
  assert(isValidStateValue(scheme.state), `Scheme ${scheme.id}: invalid state.`);
  assert(ALLOWED_CATEGORIES.includes(scheme.category), `Scheme ${scheme.id}: invalid category ${scheme.category}.`);
  assert(typeof scheme.annualBenefitAmount === "number", `Scheme ${scheme.id}: annualBenefitAmount must be number.`);

  ["benefits", "benefitsMarathi", "benefitsHindi", "documentsRequired", "eligibilityCriteria"].forEach((arrField) => {
    assert(Array.isArray(scheme[arrField]), `Scheme ${scheme.id}: ${arrField} must be array.`);
  });

  scheme.eligibilityCriteria.forEach((criterion, criterionIndex) => {
    validateCriterion(criterion, scheme.id, criterionIndex);
  });
}

function validateSchemesDb(db) {
  assert(db && typeof db === "object", "Schemes DB must be an object.");
  assert(typeof db.version === "string" && db.version.length > 0, "Schemes DB missing version.");
  assert(typeof db.lastUpdated === "string" && db.lastUpdated.length > 0, "Schemes DB missing lastUpdated.");
  assert(Array.isArray(db.schemes), "Schemes DB missing schemes array.");
  assert(db.schemes.length >= 25, "Schemes DB must contain at least 25 schemes.");

  const ids = new Set();
  db.schemes.forEach((scheme, index) => {
    validateScheme(scheme, index);
    assert(!ids.has(scheme.id), `Duplicate scheme id: ${scheme.id}`);
    ids.add(scheme.id);
  });

  return true;
}

module.exports = {
  validateSchemesDb,
};
