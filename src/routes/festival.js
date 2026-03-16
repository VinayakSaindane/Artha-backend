const express = require('express');
const router = express.Router();
const Festival = require('../models/Festival');
const Expense = require('../models/Expense');
const aiService = require('../services/aiService');
const auth = require('../middleware/auth');

// Create a new festival plan
router.post('/plan', auth, async (req, res) => {
    try {
        const { name, date, target_amount } = req.body;
        console.log(`Planning festival: ${name} on ${date} for user: ${req.user._id}`);

        // Fetch last 6 months of expenses for analysis
        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

        const pastExpenses = await Expense.find({
            user_id: req.user._id,
            date: { $gte: sixMonthsAgo }
        }).select('amount category date description').lean();

        // Summarize category-level spend to keep AI payload compact.
        const spendingSummary = pastExpenses.reduce((acc, exp) => {
            acc[exp.category] = (acc[exp.category] || 0) + exp.amount;
            return acc;
        }, {});

        const monthlyBuckets = pastExpenses.reduce((acc, exp) => {
            const d = new Date(exp.date);
            const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            acc[key] = (acc[key] || 0) + exp.amount;
            return acc;
        }, {});

        const monthlyTotals = Object.values(monthlyBuckets);
        const averageMonthlySpend = monthlyTotals.length
            ? monthlyTotals.reduce((sum, value) => sum + value, 0) / monthlyTotals.length
            : 0;

        const recentMonthKey = Object.keys(monthlyBuckets).sort().pop();
        const latestMonthSpend = recentMonthKey ? monthlyBuckets[recentMonthKey] : 0;

        const festiveCategories = ['Food', 'Fun', 'Other', 'Essentials'];
        const festiveCategorySpend = Object.entries(spendingSummary)
            .filter(([category]) => festiveCategories.includes(category))
            .reduce((sum, [, value]) => sum + value, 0);

        const parsedTargetAmount = Number(target_amount || 0);
        const normalizedTargetAmount = Number.isFinite(parsedTargetAmount) ? Math.max(0, parsedTargetAmount) : 0;

        console.log(`Sending summarized spending to AI:`, spendingSummary);

        const analysis = await aiService.analyzeFestivalShield({
            user_id: String(req.user._id),
            name,
            date,
            pastExpenses: spendingSummary,
            target_amount: normalizedTargetAmount,
            income: req.user.monthly_income || 50000,
            expenseInsights: {
                average_monthly_spend: averageMonthlySpend,
                latest_month_spend: latestMonthSpend,
                festive_category_spend: festiveCategorySpend,
                expense_months_covered: monthlyTotals.length,
                category_breakdown: spendingSummary
            }
        });

        console.log("AI Analysis received:", JSON.stringify(analysis).substring(0, 100) + "...");

        const festival = new Festival({
            user_id: req.user._id,
            name,
            date,
            target_amount: normalizedTargetAmount,
            analysis
        });

        await festival.save();
        res.status(201).send({ festival, analysis });
    } catch (error) {
        console.error("Festival Plan Error:", error);
        res.status(400).send({ error: error.message, details: error.stack });
    }
});

// Get current festival plans
router.get('/', auth, async (req, res) => {
    try {
        const festivals = await Festival.find({ user_id: req.user._id, status: { $ne: 'COMPLETED' } })
            .sort({ created_at: 1, _id: 1 });
        res.send(festivals);
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
