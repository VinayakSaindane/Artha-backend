const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const auth = require('../middleware/auth');
const eligibilityCache = require('../../lib/eligibilityCache');
const router = express.Router();

// Register
router.post('/register', async (req, res) => {
    try {
        const { email, password, name, monthly_income, age } = req.body;
        const user = new User({ email, password, name, monthly_income, age });
        await user.save();

        const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '1d' });
        res.status(201).send({ user, access_token: token, token_type: 'bearer' });
    } catch (error) {
        res.status(400).send({ detail: error.message });
    }
});

// Login
router.post('/login', async (req, res) => {
    try {
        // Note: client might send email/password in body
        const { email, password } = req.body;
        const user = await User.findOne({ email });

        if (!user || !(await user.comparePassword(password))) {
            return res.status(401).send({ detail: 'Invalid credentials' });
        }

        const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '1d' });
        res.send({ user, access_token: token, token_type: 'bearer' });
    } catch (error) {
        res.status(400).send({ detail: error.message });
    }
});

// Get Current User
router.get('/me', auth, async (req, res) => {
    res.send(req.user);
});

// Update Profile
router.put('/profile', auth, async (req, res) => {
    try {
        const {
            name,
            email,
            monthly_income,
            annual_income,
            age,
            gender,
            occupation,
            caste,
            marital_status,
            number_of_children,
            state,
            city,
            has_house,
            has_bank_account,
            cibil_score,
            existing_emis,
            preferred_language,
            has_girl_child_below_10,
            is_vulnerable_citizen,
        } = req.body;

        const hadIncome = req.user.annual_income || req.user.monthly_income * 12;

        if (typeof name === 'string') req.user.name = name;
        if (typeof email === 'string') req.user.email = email;
        if (monthly_income !== undefined) req.user.monthly_income = Number(monthly_income) || 0;
        if (annual_income !== undefined) req.user.annual_income = Number(annual_income) || 0;
        if (age !== undefined) req.user.age = Number(age) || 0;
        if (gender !== undefined) req.user.gender = gender;
        if (occupation !== undefined) req.user.occupation = occupation;
        if (caste !== undefined) req.user.caste = caste;
        if (marital_status !== undefined) req.user.marital_status = marital_status;
        if (number_of_children !== undefined) req.user.number_of_children = Number(number_of_children) || 0;
        if (state !== undefined) req.user.state = state;
        if (city !== undefined) req.user.city = city;
        if (has_house !== undefined) req.user.has_house = Boolean(has_house);
        if (has_bank_account !== undefined) req.user.has_bank_account = Boolean(has_bank_account);
        if (cibil_score !== undefined) req.user.cibil_score = Number(cibil_score) || 0;
        if (existing_emis !== undefined) req.user.existing_emis = Number(existing_emis) || 0;
        if (preferred_language !== undefined) req.user.preferred_language = preferred_language;
        if (has_girl_child_below_10 !== undefined) req.user.has_girl_child_below_10 = Boolean(has_girl_child_below_10);
        if (is_vulnerable_citizen !== undefined) req.user.is_vulnerable_citizen = Boolean(is_vulnerable_citizen);

        if (!req.user.annual_income && req.user.monthly_income) {
            req.user.annual_income = req.user.monthly_income * 12;
        }

        req.user.profileVersion = (req.user.profileVersion || 1) + 1;

        await req.user.save();
        eligibilityCache.invalidateUser(req.user._id.toString());

        const hasIncomeChanged = hadIncome !== (req.user.annual_income || req.user.monthly_income * 12);
        const message = hasIncomeChanged
            ? 'Profile updated. Income change detected, scheme eligibility refreshed.'
            : 'Profile updated successfully.';

        res.send({ ...req.user.toObject(), message });
    } catch (error) {
        res.status(400).send({ detail: error.message });
    }
});

router.get('/profile', auth, async (req, res) => {
    const annualIncome = req.user.annual_income || (req.user.monthly_income || 0) * 12;
    res.send({
        id: req.user._id,
        name: req.user.name,
        email: req.user.email,
        age: req.user.age,
        monthlyIncome: req.user.monthly_income || 0,
        annualIncome,
        gender: req.user.gender || '',
        occupation: req.user.occupation || '',
        caste: req.user.caste || '',
        maritalStatus: req.user.marital_status || '',
        childrenCount: req.user.number_of_children || 0,
        state: req.user.state || '',
        city: req.user.city || '',
        hasHouse: Boolean(req.user.has_house),
        hasBankAccount: Boolean(req.user.has_bank_account),
        cibilScore: req.user.cibil_score || 0,
        existingEmis: req.user.existing_emis || 0,
        preferredLanguage: req.user.preferred_language || '',
        hasGirlChildBelow10: Boolean(req.user.has_girl_child_below_10),
        isVulnerableCitizen: Boolean(req.user.is_vulnerable_citizen),
    });
});

router.get('/profile/demo/:persona', async (req, res) => {
    const personas = {
        rahul: {
            name: 'Rahul Sharma - Demo',
            age: 32,
            annualIncome: 540000,
            gender: 'male',
            occupation: 'salaried',
            caste: 'general',
            state: 'maharashtra',
            hasHouse: false,
            maritalStatus: 'married',
            childrenCount: 1,
            hasBankAccount: true,
            hasGirlChildBelow10: true,
            preferredLanguage: 'mr'
        },
        priya: {
            name: 'Priya Deshpande - Demo',
            age: 28,
            annualIncome: 200000,
            gender: 'female',
            occupation: 'self-employed',
            caste: 'obc',
            state: 'maharashtra',
            hasHouse: false,
            maritalStatus: 'single',
            childrenCount: 0,
            hasBankAccount: true,
            preferredLanguage: 'mr'
        },
        ramesh: {
            name: 'Ramesh Patil - Demo',
            age: 45,
            annualIncome: 300000,
            gender: 'male',
            occupation: 'farmer',
            caste: 'obc',
            state: 'maharashtra',
            hasHouse: true,
            maritalStatus: 'married',
            childrenCount: 2,
            hasBankAccount: true,
            preferredLanguage: 'mr'
        }
    };

    const key = (req.params.persona || '').toLowerCase();
    if (!personas[key]) {
        return res.status(404).send({ error: 'Demo profile not found' });
    }

    return res.send(personas[key]);
});

module.exports = router;
