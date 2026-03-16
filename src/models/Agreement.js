const mongoose = require('mongoose');

const agreementSchema = new mongoose.Schema({
    user_id: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    filename: String,
    analysis: {
        type: Object
    },
    created_at: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Agreement', agreementSchema);
