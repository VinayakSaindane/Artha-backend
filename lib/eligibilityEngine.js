const STATUS_PRIORITY = {
  eligible: 0,
  partial: 1,
  not_eligible: 2,
};

const HARD_CRITERIA_TYPES = new Set([
  "age_range",
  "income_max",
  "income_min",
  "gender",
  "occupation",
  "caste",
  "state",
  "house_status",
  "children",
]);

function toBoolean(value, fallback = false) {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "yes", "1"].includes(normalized)) return true;
    if (["false", "no", "0"].includes(normalized)) return false;
  }
  if (typeof value === "number") return value > 0;
  return fallback;
}

function toNumber(value, fallback = 0) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const clean = value.replace(/[,_\s]/g, "");
    const parsed = Number(clean);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function normalizeText(value) {
  return String(value || "").trim().toLowerCase();
}

function normalizeProfile(profile = {}) {
  const annualIncomeFromMonthly = toNumber(profile.monthly_income || profile.monthlyIncome) * 12;
  const annualIncome = toNumber(profile.annualIncome ?? profile.annual_income ?? annualIncomeFromMonthly, annualIncomeFromMonthly);

  return {
    id: profile.id || profile._id || null,
    age: toNumber(profile.age, 0),
    annualIncome,
    monthlyIncome: toNumber(profile.monthly_income ?? profile.monthlyIncome, annualIncome / 12),
    gender: normalizeText(profile.gender),
    occupation: normalizeText(profile.occupation),
    caste: normalizeText(profile.caste || profile.casteCategory),
    maritalStatus: normalizeText(profile.maritalStatus || profile.marital_status),
    childrenCount: toNumber(profile.childrenCount ?? profile.numberOfChildren ?? profile.number_of_children, 0),
    hasChildren: toBoolean(profile.hasChildren, toNumber(profile.childrenCount || 0) > 0),
    state: normalizeText(profile.state || profile.stateOfResidence),
    hasHouse: toBoolean(profile.hasHouse ?? profile.ownsHouse),
    hasBankAccount: toBoolean(profile.hasBankAccount ?? profile.bankAccountActive),
    cibilScore: toNumber(profile.cibilScore ?? profile.cibil_score, 0),
    existingEmis: toNumber(profile.existingEmis ?? profile.existing_emis, 0),
    preferredLanguage: normalizeText(profile.preferredLanguage || profile.language || ""),
    city: profile.city || "",
    hasGirlChildBelow10: toBoolean(profile.hasGirlChildBelow10),
    isVulnerableCitizen: toBoolean(profile.isVulnerableCitizen),
  };
}

function evaluateSoftCustom(profile, params = {}) {
  if (params.custom === "gender_or_caste") {
    const isWoman = profile.gender === "female";
    const caste = normalizeText(profile.caste);
    const isScSt = caste === "sc" || caste === "st";
    return {
      met: isWoman || isScSt,
      reason: isWoman || isScSt
        ? "You match preferred beneficiary category."
        : "Preferential benefit for women or SC/ST applicants.",
    };
  }

  return {
    met: true,
    reason: "Optional preference.",
  };
}

function evaluateCriterion(profile, criterion) {
  const { type, params = {}, label = "Criterion" } = criterion;

  switch (type) {
    case "age_range": {
      const min = toNumber(params.min, 0);
      const max = toNumber(params.max, 150);
      const met = profile.age >= min && profile.age <= max;
      return {
        met,
        reason: met
          ? `Age ${profile.age} is within ${min}-${max}.`
          : `Age ${profile.age} is outside ${min}-${max}.`,
      };
    }

    case "income_max": {
      const max = toNumber(params.max, 0);
      const met = profile.annualIncome <= max;
      return {
        met,
        reason: met
          ? `Annual income Rs.${profile.annualIncome.toLocaleString("en-IN")} is within limit.`
          : `Income exceeds Rs.${max.toLocaleString("en-IN")} limit.`,
      };
    }

    case "income_min": {
      const min = toNumber(params.min, 0);
      const met = profile.annualIncome >= min;
      return {
        met,
        reason: met
          ? `Annual income meets minimum Rs.${min.toLocaleString("en-IN")}.`
          : `Annual income is below Rs.${min.toLocaleString("en-IN")}.`,
      };
    }

    case "gender": {
      const target = normalizeText(params.value);
      const met = !target || profile.gender === target;
      return {
        met,
        reason: met ? "Gender criterion satisfied." : `Requires gender ${target}.`,
      };
    }

    case "occupation": {
      const values = Array.isArray(params.values) ? params.values.map(normalizeText) : [];
      const met = values.length === 0 || values.includes(profile.occupation);
      return {
        met,
        reason: met
          ? "Occupation criterion satisfied."
          : `Required occupation: ${values.join(", ")}.`,
      };
    }

    case "caste": {
      const values = Array.isArray(params.values) ? params.values.map(normalizeText) : [];
      const met = values.length === 0 || values.includes(profile.caste);
      return {
        met,
        reason: met ? "Caste criterion satisfied." : `Required category: ${values.join(", ")}.`,
      };
    }

    case "state": {
      const value = normalizeText(params.value || "all");
      const met = value === "all" || profile.state === value;
      return {
        met,
        reason: met ? "State criterion satisfied." : `Available for ${value} residents.`,
      };
    }

    case "house_status": {
      const expected = toBoolean(params.ownsHouse, false);
      const met = profile.hasHouse === expected;
      return {
        met,
        reason: met
          ? "Housing ownership criterion satisfied."
          : expected ? "Requires owned house." : "Requires no owned house.",
      };
    }

    case "children": {
      const min = toNumber(params.min, 0);
      const max = params.max == null ? Number.POSITIVE_INFINITY : toNumber(params.max, Number.POSITIVE_INFINITY);
      const count = profile.childrenCount;
      const met = count >= min && count <= max;
      return {
        met,
        reason: met ? "Children criterion satisfied." : `Needs children count between ${min} and ${max}.`,
      };
    }

    case "always_eligible": {
      return {
        met: true,
        reason: "This criterion is informational.",
      };
    }

    case "soft_requirement": {
      if (params.custom) {
        return evaluateSoftCustom(profile, params);
      }

      const field = params.field;
      const expected = params.equals;
      const actual = profile[field];
      const met = expected === undefined ? Boolean(actual) : actual === expected;
      return {
        met,
        reason: met
          ? "Optional requirement met."
          : params.tip || `${label} is not currently satisfied.`,
      };
    }

    default:
      return {
        met: false,
        reason: `Unsupported criterion type: ${type}`,
      };
  }
}

function checkEligibility(userProfile, scheme) {
  const profile = normalizeProfile(userProfile);
  const criteria = Array.isArray(scheme.eligibilityCriteria) ? scheme.eligibilityCriteria : [];

  if (criteria.length === 0) {
    return {
      status: "eligible",
      matchScore: 100,
      criteriaResults: [],
      missingCriteria: [],
      estimatedBenefit: toNumber(scheme.annualBenefitAmount, 0),
    };
  }

  const results = criteria.map((criterion) => {
    const evaluation = evaluateCriterion(profile, criterion);
    return {
      criteriaId: criterion.criteriaId,
      met: evaluation.met,
      reason: evaluation.reason,
      label: criterion.label,
      labelMarathi: criterion.labelMarathi,
      labelHindi: criterion.labelHindi,
      type: criterion.type,
      tip: criterion.params && criterion.params.tip ? criterion.params.tip : "",
    };
  });

  const metCount = results.filter((r) => r.met).length;
  const matchScore = Math.round((metCount / results.length) * 100);

  const hardCriteria = criteria.filter((c) => HARD_CRITERIA_TYPES.has(c.type));
  const hardMet = hardCriteria.every((criterion) => {
    const result = results.find((r) => r.criteriaId === criterion.criteriaId);
    return result && result.met;
  });

  let status = "not_eligible";
  if (hardMet) {
    status = "eligible";
  } else if (matchScore >= 60) {
    status = "partial";
  }

  const missingCriteria = results
    .filter((r) => !r.met)
    .map((r) => r.label);

  const fullBenefit = toNumber(scheme.annualBenefitAmount, 0);
  const estimatedBenefit = status === "eligible"
    ? fullBenefit
    : Math.round((matchScore / 100) * fullBenefit);

  return {
    status,
    matchScore,
    criteriaResults: results,
    missingCriteria,
    estimatedBenefit,
  };
}

function sortEligibilityResults(a, b) {
  const statusDelta = STATUS_PRIORITY[a.eligibility.status] - STATUS_PRIORITY[b.eligibility.status];
  if (statusDelta !== 0) return statusDelta;
  return toNumber(b.annualBenefitAmount, 0) - toNumber(a.annualBenefitAmount, 0);
}

function getPreferredLanguage(profile = {}) {
  const normalized = normalizeProfile(profile);
  if (normalized.preferredLanguage === "marathi" || normalized.preferredLanguage === "mr") return "mr";
  if (normalized.preferredLanguage === "hindi" || normalized.preferredLanguage === "hi") return "hi";
  if (normalized.state === "maharashtra") return "mr";
  return "hi";
}

function getLocalizedText(scheme, language) {
  if (language === "mr") {
    return {
      name: scheme.nameMarathi || scheme.name,
      description: scheme.descriptionMarathi || scheme.description,
      benefits: scheme.benefitsMarathi || scheme.benefits,
    };
  }

  if (language === "hi") {
    return {
      name: scheme.nameHindi || scheme.name,
      description: scheme.descriptionHindi || scheme.description,
      benefits: scheme.benefitsHindi || scheme.benefits,
    };
  }

  return {
    name: scheme.name,
    description: scheme.description,
    benefits: scheme.benefits,
  };
}

function evaluateAllSchemes(userProfile, schemes, options = {}) {
  const profile = normalizeProfile(userProfile);
  const categoryFilter = normalizeText(options.category || "");
  const language = options.language || getPreferredLanguage(profile);

  const matched = schemes
    .filter((scheme) => {
      if (categoryFilter && scheme.category !== categoryFilter) return false;
      if (scheme.state === "all") return true;
      return normalizeText(scheme.state) === profile.state;
    })
    .map((scheme) => {
      const eligibility = checkEligibility(profile, scheme);
      const localized = getLocalizedText(scheme, language);
      return {
        ...scheme,
        localized,
        eligibility,
      };
    })
    .sort(sortEligibilityResults);

  const totalEligibleSchemes = matched.filter((s) => s.eligibility.status === "eligible").length;
  const totalPotentialAnnualBenefit = matched
    .filter((s) => s.eligibility.status !== "not_eligible")
    .reduce((sum, scheme) => sum + toNumber(scheme.eligibility.estimatedBenefit, 0), 0);

  return {
    totalSchemesChecked: matched.length,
    totalEligibleSchemes,
    totalPotentialAnnualBenefit,
    schemes: matched,
  };
}

function findIncompleteProfileFields(profile = {}) {
  const normalized = normalizeProfile(profile);
  const required = [
    ["age", normalized.age > 0],
    ["annualIncome", normalized.annualIncome > 0],
    ["gender", Boolean(normalized.gender)],
    ["occupation", Boolean(normalized.occupation)],
    ["caste", Boolean(normalized.caste)],
    ["state", Boolean(normalized.state)],
  ];

  return required.filter((entry) => !entry[1]).map((entry) => entry[0]);
}

module.exports = {
  normalizeProfile,
  evaluateCriterion,
  checkEligibility,
  evaluateAllSchemes,
  sortEligibilityResults,
  getPreferredLanguage,
  getLocalizedText,
  findIncompleteProfileFields,
};
