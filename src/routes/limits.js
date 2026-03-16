const express = require('express');
const router = express.Router();
const User = require('../models/User');
const auth = require('../middleware/auth');

// Update category limits
router.post('/', auth, async (req, res) => {
    try {
        const { limits } = req.body; // { "Food": 5000, "Transport": 2000 }

        const user = await User.findById(req.user._id);
        if (!user.category_limits) {
            user.category_limits = new Map();
        }

        for (const [category, amount] of Object.entries(limits)) {
            user.category_limits.set(category, amount);
        }

        await user.save();
        res.send(user.category_limits);
    } catch (error) {
        res.status(400).send({ error: error.message });
    }
});

// Get category limits
router.get('/', auth, async (req, res) => {
    try {
        res.send(req.user.category_limits || {});
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
