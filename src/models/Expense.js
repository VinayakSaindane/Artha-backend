const mongoose = require('mongoose');

const expenseSchema = new mongoose.Schema({
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
        required: true,
        enum: ['Food', 'Transport', 'EMI', 'Health', 'Fun', 'Essentials', 'Housing', 'Other']
    },
    description: String,
    date: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Expense', expenseSchema);
