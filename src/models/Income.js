const mongoose = require('mongoose');

const incomeSchema = new mongoose.Schema({
    user_id: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    amount: {
        type: Number,
        required: true
    },
    category: {
        type: String,
        default: 'Bonus' // Bonus, Refund, Salary, Side Hustle, Gift, Interest, Other
    },
    description: String,
    date: {
        type: Date,
        default: Date.now
    }
}, { timestamps: true });

module.exports = mongoose.model('Income', incomeSchema);
