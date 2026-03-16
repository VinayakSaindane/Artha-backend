const mongoose = require('mongoose');

const goalSchema = new mongoose.Schema({
    user_id: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    name: {
        type: String,
        required: true
    },
    target_amount: {
        type: Number,
        required: true
    },
    current_amount: {
        type: Number,
        default: 0
    },
    deadline: Date,
    category: {
        type: String,
        enum: ['Retirement', 'Education', 'Emergency', 'Housing', 'Other']
    },
    created_at: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Goal', goalSchema);
