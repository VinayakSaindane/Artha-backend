const express = require("express");
const auth = require("../middleware/auth");
const { getAllSchemes, getSchemesMeta } = require("../../lib/schemesStore");
const {
  evaluateAllSchemes,
  normalizeProfile,
  findIncompleteProfileFields,
} = require("../../lib/eligibilityEngine");
const eligibilityCache = require("../../lib/eligibilityCache");
const { buildAutoAlerts } = require("../services/schemesAlertService");

const router = express.Router();

function parseAppliedSchemeIds(value) {
  if (!Array.isArray(value)) return [];
  return value.filter((id) => typeof id === "string");
}

router.get("/eligible", auth, async (req, res) => {
  try {
    const category = (req.query.category || "").toString().trim().toLowerCase();
    const language = (req.query.lang || "").toString().trim().toLowerCase();

    const profile = normalizeProfile(req.user.toObject ? req.user.toObject() : req.user);
    const incompleteFields = findIncompleteProfileFields(profile);

    const profileVersion = req.user.profileVersion || 0;
    const cached = eligibilityCache.get(req.user._id.toString(), category, profileVersion);
    if (cached) {
      return res.send({
        ...cached,
        incompleteProfileFields: incompleteFields,
        warning: incompleteFields.length
          ? "Complete your profile to see all eligible schemes"
          : null,
      });
    }

    const schemes = getAllSchemes();
    const evaluated = evaluateAllSchemes(profile, schemes, { category, language });

    const previousEligibleIds = Array.isArray(req.user.lastEligibleSchemeIds)
      ? req.user.lastEligibleSchemeIds
      : [];

    const alertResult = buildAutoAlerts({
      eligibleResult: evaluated,
      previousEligibleIds,
      appliedSchemeIds: parseAppliedSchemeIds(req.user.appliedSchemeIds),
    });

    req.user.lastEligibleSchemeIds = alertResult.currentEligibleIds;
    await req.user.save();

    const payload = {
      ...evaluated,
      ...getSchemesMeta(),
      lastCheckedAt: new Date().toISOString(),
      fromCache: false,
      incompleteProfileFields: incompleteFields,
      warning: incompleteFields.length
        ? "Complete your profile to see all eligible schemes"
        : null,
      alerts: alertResult.alerts,
    };

    eligibilityCache.set(req.user._id.toString(), category, profileVersion, payload);
    res.send(payload);
  } catch (error) {
    console.error("Schemes eligible route error", error);
    res.status(500).send({
      error: "Failed to evaluate scheme eligibility",
      detail: error.message,
    });
  }
});

router.get("/:schemeId", auth, async (req, res) => {
  try {
    const schemeId = req.params.schemeId;
    const schemes = getAllSchemes();
    const scheme = schemes.find((entry) => entry.id === schemeId);

    if (!scheme) {
      return res.status(404).send({ error: "Scheme not found" });
    }

    const applicationSteps = scheme.applicationProcess
      .split(".")
      .map((step) => step.trim())
      .filter(Boolean)
      .map((step, idx) => ({ stepNo: idx + 1, text: step }));

    res.send({
      ...scheme,
      applicationSteps,
      estimatedCompletionMinutes: 15,
      commonRejectionReasons: [
        "Mismatch in Aadhaar and bank details",
        "Income or caste certificate expired",
        "Incorrect beneficiary category selected",
      ],
      nearestApplicationCenter: {
        city: req.user.city || "Nearest district center",
        name: `${req.user.state || "State"} Seva Kendra`,
      },
    });
  } catch (error) {
    res.status(500).send({ error: "Failed to fetch scheme detail", detail: error.message });
  }
});

router.post("/:schemeId/help", auth, async (req, res) => {
  try {
    const scheme = getAllSchemes().find((entry) => entry.id === req.params.schemeId);
    if (!scheme) {
      return res.status(404).send({ error: "Scheme not found" });
    }

    const question = (req.body.question || "").toString().trim();
    const language = (req.body.language || req.user.preferred_language || "hi").toString().toLowerCase();

    const answers = {
      mr: `${scheme.nameMarathi}: अर्ज करताना तुमची कागदपत्रे आणि बँक तपशील जुळतात याची खात्री करा. अधिकृत पोर्टलवर नोंदणी करून चरण पूर्ण करा: ${scheme.applyUrl}. जटिल कायदेशीर प्रकरणांसाठी शासकीय हेल्पलाइनशी संपर्क करा.`,
      hi: `${scheme.nameHindi}: आवेदन करते समय अपने दस्तावेज और बैंक विवरण सही रखें। आधिकारिक पोर्टल पर चरणबद्ध प्रक्रिया पूरी करें: ${scheme.applyUrl}. जटिल मामलों में सरकारी हेल्पलाइन से संपर्क करें।`,
      en: `${scheme.name}: Keep documents and bank details consistent before applying. Complete the process step-by-step on the official portal: ${scheme.applyUrl}. For complex legal questions, contact the government helpline.`,
    };

    const key = language.startsWith("mr") ? "mr" : language.startsWith("en") ? "en" : "hi";

    res.send({
      answer: answers[key],
      question,
      systemPromptUsed: `You are ARTHA's government scheme advisor. The user is asking about ${scheme.name}. Answer in ${key}. Be specific, practical, and use simple language. Always cite the official government portal URL. Never give legal advice — direct complex cases to a government helpline.`,
      portalUrl: scheme.applyUrl,
    });
  } catch (error) {
    res.status(500).send({ error: "Failed to generate scheme help", detail: error.message });
  }
});

module.exports = {
  schemesRouter: router,
  invalidateSchemesCacheForUser: (userId) => eligibilityCache.invalidateUser(userId),
};
