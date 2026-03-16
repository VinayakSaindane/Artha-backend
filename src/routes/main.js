const express = require('express');
const router = express.Router();
const aiService = require('../services/aiService');
const auth = require('../middleware/auth');

// --- SCORE ---
router.post('/score/predict', auth, async (req, res) => {
    try {
        const prediction = await aiService.predictLoan(req.body);
        res.send(prediction);
    } catch (error) {
        res.status(400).send({ error: error.message });
    }
});

const Expense = require('../models/Expense');

// --- PULSE ---
router.get('/pulse/analyze', auth, async (req, res) => {
    try {
        const expenses = await Expense.find({ user_id: req.user._id }).lean();

        // Calculate total EMIs
        const total_emis = expenses
            .filter(e => e.category === 'EMI')
            .reduce((sum, e) => sum + e.amount, 0);

        // Calculate Trend (Comparing this month vs last month)
        const now = new Date();
        const thisMonth = expenses.filter(e => e.date.getMonth() === now.getMonth() && e.date.getFullYear() === now.getFullYear());

        const lastMonth = expenses.filter(e => {
            const targetMonth = now.getMonth() === 0 ? 11 : now.getMonth() - 1;
            const targetYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
            return e.date.getMonth() === targetMonth && e.date.getFullYear() === targetYear;
        });

        const thisMonthTotal = thisMonth.reduce((sum, e) => sum + e.amount, 0);
        const lastMonthTotal = lastMonth.reduce((sum, e) => sum + e.amount, 0);

        let trend = "STABLE";
        if (thisMonthTotal > lastMonthTotal * 1.1) trend = "DETERIORATING";
        else if (thisMonthTotal < lastMonthTotal * 0.9) trend = "IMPROVING";

        const data = {
            income: req.user.monthly_income || 50000,
            total_emis: total_emis || 0,
            monthly_expenses: thisMonthTotal || 0,
            trend: trend
        };

        const analysis = await aiService.analyzeDebtPulse(data);
        res.send(analysis);
    } catch (error) {
        console.error("Pulse API Error:", error);
        res.status(400).send({ error: error.message });
    }
});

// --- GOALS ---
const Goal = require('../models/Goal');

router.get('/goals', auth, async (req, res) => {
    try {
        const goals = await Goal.find({ user_id: req.user._id }).sort({ created_at: -1 });
        res.send(goals);
    } catch (error) {
        res.status(500).send(error);
    }
});

router.post('/goals', auth, async (req, res) => {
    try {
        const goal = new Goal({
            ...req.body,
            user_id: req.user._id
        });
        await goal.save();
        res.status(201).send(goal);
    } catch (error) {
        res.status(400).send({ error: error.message });
    }
});

router.post('/goals/plan', auth, async (req, res) => {
    try {
        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

        const recentExpenses = await Expense.find({
            user_id: req.user._id,
            date: { $gte: sixMonthsAgo }
        }).lean();

        const monthlyBuckets = recentExpenses.reduce((acc, row) => {
            const d = new Date(row.date);
            const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            acc[key] = (acc[key] || 0) + (row.amount || 0);
            return acc;
        }, {});

        const monthlyTotals = Object.values(monthlyBuckets);
        const averageMonthlyExpenses = monthlyTotals.length
            ? monthlyTotals.reduce((sum, value) => sum + value, 0) / monthlyTotals.length
            : 0;

        const existingGoals = await Goal.find({ user_id: req.user._id }).lean();
        const today = new Date();
        const activeGoalCommitment = existingGoals.reduce((sum, goal) => {
            const pendingAmount = Math.max(0, (goal.target_amount || 0) - (goal.current_amount || 0));
            if (!pendingAmount) return sum;

            if (!goal.deadline) {
                return sum + (pendingAmount / 24);
            }

            const deadline = new Date(goal.deadline);
            const monthsLeft = Math.max(
                1,
                (deadline.getFullYear() - today.getFullYear()) * 12 + (deadline.getMonth() - today.getMonth())
            );
            return sum + (pendingAmount / monthsLeft);
        }, 0);

        const income = req.body.income || req.user.monthly_income || 50000;
        const fallbackSavings = Math.max(0, (income - averageMonthlyExpenses) * Math.max(1, monthlyTotals.length));

        const payload = {
            ...req.body,
            income,
            monthly_expenses: req.body.monthly_expenses || Math.round(averageMonthlyExpenses),
            existing_emis: req.body.existing_emis || req.user.existing_emis || 0,
            current_savings: req.body.current_savings || Math.round(fallbackSavings),
            goal_commitment: Math.round(activeGoalCommitment),
            source_metrics: {
                monthly_average_expenses: Math.round(averageMonthlyExpenses),
                months_covered: monthlyTotals.length,
                active_goals: existingGoals.length
            }
        };

        const plan = await aiService.planGoals(payload);
        res.send(plan);
    } catch (error) {
        res.status(500).send(error);
    }
});

// --- ADVISOR ---
router.post('/advisor/strategy', auth, async (req, res) => {
    try {
        const strategy = await aiService.analyzeFinanceStrategy(req.body);
        res.send(strategy);
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
