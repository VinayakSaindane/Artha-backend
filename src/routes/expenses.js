const express = require('express');
const Expense = require('../models/Expense');
const auth = require('../middleware/auth');
const router = express.Router();

// Get all expenses for user
router.get('/', auth, async (req, res) => {
    try {
        const expenses = await Expense.find({ user_id: req.user._id }).sort({ date: -1 });
        res.send(expenses);
    } catch (error) {
        res.status(500).send(error);
    }
});

// Create expense
router.post('/', auth, async (req, res) => {
    try {
        const expense = new Expense({
            ...req.body,
            user_id: req.user._id
        });
        await expense.save();
        res.status(201).send(expense);
    } catch (error) {
        res.status(400).send(error);
    }
});

// Delete expense
router.delete('/:id', auth, async (req, res) => {
    try {
        const expense = await Expense.findOneAndDelete({ _id: req.params.id, user_id: req.user._id });
        if (!expense) return res.status(404).send();
        res.send(expense);
    } catch (error) {
        res.status(500).send(error);
    }
});

// Get summary
router.get('/summary', auth, async (req, res) => {
    try {
        const summary = await Expense.aggregate([
            { $match: { user_id: req.user._id } },
            { $group: { _id: "$category", total_amount: { $sum: "$amount" } } },
            { $project: { category: "$_id", total_amount: 1, _id: 0 } }
        ]);
        res.send(summary);
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
