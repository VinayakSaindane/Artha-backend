const express = require('express');
const auth = require('../middleware/auth');
const aiService = require('../services/aiService');
const Expense = require('../models/Expense');

const router = express.Router();

const buildExpenseTrend = async (userId, months = 6) => {
  const now = new Date();
  const trend = [];

  for (let i = months - 1; i >= 0; i -= 1) {
    const start = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const end = new Date(now.getFullYear(), now.getMonth() - i + 1, 1);

    const monthDocs = await Expense.find({
      user_id: userId,
      date: { $gte: start, $lt: end }
    }).lean();

    const total = monthDocs.reduce((sum, row) => sum + (row.amount || 0), 0);
    trend.push(total);
  }

  return trend;
};

router.post('/risk-radar', auth, async (req, res) => {
  try {
    const monthlyExpenseTrend = await buildExpenseTrend(req.user._id, 6);
    const latestExpenses = monthlyExpenseTrend[monthlyExpenseTrend.length - 1] || req.body.expenses || 0;

    const payload = {
      income: req.body.income || req.user.monthly_income || 50000,
      expenses: req.body.expenses || latestExpenses,
      savings: req.body.savings,
      existing_loans: req.body.existing_loans || req.body.total_emis || 0,
      monthly_expense_trend: req.body.monthly_expense_trend || monthlyExpenseTrend
    };

    const response = await aiService.analyzeRiskRadar(payload);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.post('/loan-scam-check', auth, async (req, res) => {
  try {
    const response = await aiService.analyzeLoanScam(req.body);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.post('/simulation', auth, async (req, res) => {
  try {
    const payload = {
      ...req.body,
      current_income: req.body.current_income || req.user.monthly_income || 50000
    };
    const response = await aiService.runSimulation(payload);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.post('/what-if', auth, async (req, res) => {
  try {
    const payload = {
      ...req.body,
      income: req.body.income || req.user.monthly_income || 50000
    };
    const response = await aiService.runWhatIfScenario(payload);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.post('/emergency-detector', auth, async (req, res) => {
  try {
    const payload = {
      ...req.body,
      income: req.body.income || req.user.monthly_income || 50000
    };
    const response = await aiService.detectEmergency(payload);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.post('/festival-intelligence', auth, async (req, res) => {
  try {
    const payload = {
      ...req.body,
      user_id: String(req.user._id),
      income: req.body.income || req.user.monthly_income || 50000
    };
    const response = await aiService.analyzeFestivalIntelligence(payload);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.post('/whatsapp-expense', auth, async (req, res) => {
  try {
    const payload = {
      ...req.body,
      user_id: String(req.user._id)
    };
    const response = await aiService.parseWhatsappExpense(payload);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.get('/habit-score', auth, async (req, res) => {
  try {
    const response = await aiService.getHabitScore(String(req.user._id));
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.get('/macro-risk-alert', auth, async (req, res) => {
  try {
    const response = await aiService.getMacroRiskAlert({
      user_id: String(req.user._id),
      force_refresh: req.query.force_refresh === 'true'
    });
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

router.post('/macro-risk-simulation', auth, async (req, res) => {
  try {
    const payload = {
      ...req.body,
      user_id: String(req.user._id),
      user_profile: {
        ...(req.body.user_profile || {}),
        income: req.body?.user_profile?.income || req.user.monthly_income || 50000,
        loan_emi: req.body?.user_profile?.loan_emi || req.user.existing_emis || 0,
      }
    };

    const response = await aiService.runMacroRiskSimulation(payload);
    res.send(response);
  } catch (error) {
    res.status(400).send({ error: error.message });
  }
});

module.exports = router;
