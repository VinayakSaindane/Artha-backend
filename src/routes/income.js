const express = require('express');
const Income = require('../models/Income');
const auth = require('../middleware/auth');
const eligibilityCache = require('../../lib/eligibilityCache');
const router = express.Router();

// Get all income for user
router.get('/', auth, async (req, res) => {
    try {
        const income = await Income.find({ user_id: req.user._id }).sort({ date: -1 });
        res.send(income);
    } catch (error) {
        res.status(500).send(error);
    }
});

// Add income
router.post('/', auth, async (req, res) => {
    try {
        const income = new Income({
            ...req.body,
            user_id: req.user._id
        });
        await income.save();

        const category = String(req.body.category || '').toLowerCase();
        if (category === 'salary') {
            req.user.monthly_income = Number(req.body.amount) || req.user.monthly_income;
            req.user.annual_income = (req.user.monthly_income || 0) * 12;
            req.user.profileVersion = (req.user.profileVersion || 1) + 1;
            await req.user.save();
            eligibilityCache.invalidateUser(req.user._id.toString());
        }

        res.status(201).send(income);
    } catch (error) {
        res.status(400).send(error);
    }
});

// Delete income
router.delete('/:id', auth, async (req, res) => {
    try {
        const income = await Income.findOneAndDelete({ _id: req.params.id, user_id: req.user._id });
        if (!income) return res.status(404).send();
        res.send(income);
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
