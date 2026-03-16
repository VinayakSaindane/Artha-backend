const express = require("express");
const auth = require("../middleware/auth");

const router = express.Router();

router.get("/profile", auth, async (req, res) => {
  const annualIncome = req.user.annual_income || (req.user.monthly_income || 0) * 12;

  res.send({
    id: req.user._id,
    name: req.user.name,
    email: req.user.email,
    age: req.user.age,
    monthlyIncome: req.user.monthly_income || 0,
    annualIncome,
    gender: req.user.gender || "",
    occupation: req.user.occupation || "",
    caste: req.user.caste || "",
    maritalStatus: req.user.marital_status || "",
    childrenCount: req.user.number_of_children || 0,
    state: req.user.state || "",
    city: req.user.city || "",
    hasHouse: Boolean(req.user.has_house),
    hasBankAccount: Boolean(req.user.has_bank_account),
    cibilScore: req.user.cibil_score || 0,
    existingEmis: req.user.existing_emis || 0,
    preferredLanguage: req.user.preferred_language || "",
    hasGirlChildBelow10: Boolean(req.user.has_girl_child_below_10),
    isVulnerableCitizen: Boolean(req.user.is_vulnerable_citizen),
  });
});

module.exports = router;
