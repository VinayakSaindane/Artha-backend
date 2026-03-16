const express = require('express');
const router = express.Router();
const Festival = require('../models/Festival');
const Expense = require('../models/Expense');
const aiService = require('../services/aiService');
const auth = require('../middleware/auth');

// Create a new festival plan
router.post('/plan', auth, async (req, res) => {
    try {
        const { name, date } = req.body;
        console.log(`Planning festival: ${name} on ${date} for user: ${req.user._id}`);

        // Fetch last 6 months of expenses for analysis
        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

        const pastExpenses = await Expense.find({
            user_id: req.user._id,
            date: { $gte: sixMonthsAgo }
        }).select('amount category date description').lean();

        // Summarize data to avoid prompt overflow
        const spendingSummary = pastExpenses.reduce((acc, exp) => {
            acc[exp.category] = (acc[exp.category] || 0) + exp.amount;
            return acc;
        }, {});

        console.log(`Sending summarized spending to AI:`, spendingSummary);

        const analysis = await aiService.analyzeFestivalShield({
            user_id: String(req.user._id),
            name,
            date,
            pastExpenses: spendingSummary,
            income: req.user.monthly_income || 50000
        });

        console.log("AI Analysis received:", JSON.stringify(analysis).substring(0, 100) + "...");

        const festival = new Festival({
            user_id: req.user._id,
            name,
            date,
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
        const festivals = await Festival.find({ user_id: req.user._id, status: { $ne: 'COMPLETED' } });
        res.send(festivals);
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
