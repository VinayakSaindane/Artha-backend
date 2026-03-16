const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
    email: {
        type: String,
        required: true,
        unique: true,
        trim: true,
        lowercase: true
    },
    password: {
        type: String,
        required: true
    },
    name: {
        type: String,
        required: true
    },
    monthly_income: {
        type: Number,
        default: 0
    },
    annual_income: {
        type: Number,
        default: 0
    },
    age: {
        type: Number,
        default: 25
    },
    gender: {
        type: String,
        enum: ['male', 'female', 'other', ''],
        default: ''
    },
    occupation: {
        type: String,
        enum: ['salaried', 'self-employed', 'farmer', 'student', 'unemployed', 'retired', ''],
        default: ''
    },
    caste: {
        type: String,
        enum: ['general', 'obc', 'sc', 'st', 'ews', ''],
        default: ''
    },
    marital_status: {
        type: String,
        enum: ['single', 'married', 'divorced', 'widowed', ''],
        default: ''
    },
    number_of_children: {
        type: Number,
        default: 0
    },
    state: {
        type: String,
        default: ''
    },
    city: {
        type: String,
        default: ''
    },
    has_house: {
        type: Boolean,
        default: false
    },
    has_bank_account: {
        type: Boolean,
        default: false
    },
    cibil_score: {
        type: Number,
        default: 0
    },
    existing_emis: {
        type: Number,
        default: 0
    },
    preferred_language: {
        type: String,
        enum: ['en', 'mr', 'hi', ''],
        default: ''
    },
    has_girl_child_below_10: {
        type: Boolean,
        default: false
    },
    is_vulnerable_citizen: {
        type: Boolean,
        default: false
    },
    profileVersion: {
        type: Number,
        default: 1
    },
    lastEligibleSchemeIds: {
        type: [String],
        default: []
    },
    appliedSchemeIds: {
        type: [String],
        default: []
    },
    created_at: {
        type: Date,
        default: Date.now
    },
    category_limits: {
        type: Map,
        of: Number,
        default: {}
    }
});

// Hash password before saving
userSchema.pre('save', async function (next) {
    if (!this.isModified('password')) return next();
    this.password = await bcrypt.hash(this.password, 10);
    next();
});

// Compare password method
userSchema.methods.comparePassword = async function (candidatePassword) {
    return await bcrypt.compare(candidatePassword, this.password);
};

module.exports = mongoose.model('User', userSchema);
