function daysUntil(deadline) {
  const parsed = new Date(deadline);
  if (Number.isNaN(parsed.getTime())) return null;

  const now = new Date();
  const startOfNow = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfDeadline = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());

  return Math.round((startOfDeadline.getTime() - startOfNow.getTime()) / (24 * 60 * 60 * 1000));
}

function formatCurrency(value) {
  return `Rs.${Number(value || 0).toLocaleString("en-IN")}`;
}

function buildProfileCompletionAlert(eligibleResult) {
  const count = eligibleResult.totalEligibleSchemes;
  const amount = formatCurrency(eligibleResult.totalPotentialAnnualBenefit);

  return {
    type: "profile_completion",
    message: `Your profile is complete. We found ${count} government schemes worth ${amount}/year that you qualify for. Tap to see.`,
  };
}

function buildIncomeChangeAlert(newlyEligibleSchemes) {
  if (!newlyEligibleSchemes || newlyEligibleSchemes.length === 0) return null;
  const top = newlyEligibleSchemes[0];

  return {
    type: "income_change",
    schemeId: top.id,
    message: `Income update detected. You are now eligible for ${top.name}. Tap to apply.`,
  };
}

function buildDeadlineAlerts(eligibleSchemes) {
  return (eligibleSchemes || [])
    .filter((scheme) => scheme.deadline && scheme.deadline !== "rolling")
    .map((scheme) => ({ scheme, days: daysUntil(scheme.deadline) }))
    .filter((entry) => entry.days === 30)
    .map((entry) => ({
      type: "deadline",
      schemeId: entry.scheme.id,
      message: `${entry.scheme.name} renewal due in 30 days. Complete required payment or application to keep your benefits active.`,
    }));
}

function buildMonthlyDiscoveryNudge(eligibleSchemes, appliedSchemeIds = []) {
  const now = new Date();
  if (now.getDate() !== 1) return null;

  const unseen = (eligibleSchemes || []).filter(
    (scheme) => !appliedSchemeIds.includes(scheme.id) && scheme.eligibility && scheme.eligibility.status === "eligible"
  );

  if (unseen.length === 0) return null;

  const pick = unseen[Math.floor(Math.random() * unseen.length)];
  return {
    type: "monthly_discovery",
    schemeId: pick.id,
    message: `Did you know? You qualify for ${pick.name}. ${formatCurrency(pick.annualBenefitAmount)} benefit waiting. Takes 10 minutes to apply.`,
  };
}

function buildAutoAlerts({ eligibleResult, previousEligibleIds = [], appliedSchemeIds = [] }) {
  const eligibleSchemes = (eligibleResult.schemes || []).filter((scheme) => scheme.eligibility.status === "eligible");
  const currentEligibleIds = eligibleSchemes.map((scheme) => scheme.id);

  const newlyEligible = eligibleSchemes.filter((scheme) => !previousEligibleIds.includes(scheme.id));
  const alerts = [
    buildProfileCompletionAlert(eligibleResult),
    buildIncomeChangeAlert(newlyEligible),
    ...buildDeadlineAlerts(eligibleSchemes),
    buildMonthlyDiscoveryNudge(eligibleSchemes, appliedSchemeIds),
  ].filter(Boolean);

  return {
    alerts,
    currentEligibleIds,
  };
}

module.exports = {
  buildAutoAlerts,
};
