const mongoose = require('mongoose');

const festivalSchema = new mongoose.Schema({
    user_id: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    name: {
        type: String,
        required: true
    },
    date: {
        type: Date,
        required: true
    },
    target_amount: {
        type: Number,
        default: 0
    },
    status: {
        type: String,
        enum: ['PLANNING', 'SAVING', 'COMPLETED'],
        default: 'PLANNING'
    },
    analysis: {
        type: Object
    },
    created_at: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Festival', festivalSchema);
