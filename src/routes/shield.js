const express = require('express');
const multer = require('multer');
const pdf = require('pdf-parse');
const Agreement = require('../models/Agreement');
const aiService = require('../services/aiService');
const auth = require('../middleware/auth');
const router = express.Router();

const upload = multer({
    limits: { fileSize: 5000000 }, // 5MB limit
    fileFilter(req, file, cb) {
        if (!file.originalname.match(/\.(pdf|txt)$/)) {
            return cb(new Error('Please upload a PDF or TXT file'));
        }
        cb(undefined, true);
    }
});

const buildUserContext = (user) => ({
    name: user?.name || '',
    age: user?.age || 0,
    occupation: user?.occupation || '',
    monthly_income: user?.monthly_income || 0,
    annual_income: user?.annual_income || 0,
    existing_emis: user?.existing_emis || 0,
    cibil_score: user?.cibil_score || 0,
    state: user?.state || '',
    city: user?.city || '',
    marital_status: user?.marital_status || '',
    is_vulnerable_citizen: Boolean(user?.is_vulnerable_citizen),
    preferred_language: user?.preferred_language || '',
});

// Analyze Agreement
router.post('/analyze', auth, upload.single('file'), async (req, res) => {
    try {
        let text = req.body.text;

        if (req.file) {
            if (req.file.mimetype === 'application/pdf') {
                const dataJson = await pdf(req.file.buffer);
                text = dataJson.text;
            } else {
                text = req.file.buffer.toString();
            }
        }

        if (!text) {
            return res.status(400).send({ error: "No text or file provided" });
        }

        const analysis = await aiService.analyzeAgreement(text, buildUserContext(req.user));

        const agreement = new Agreement({
            user_id: req.user._id,
            filename: req.file ? req.file.originalname : 'Direct Text Input',
            analysis
        });

        await agreement.save();
        res.send(agreement);
    } catch (error) {
        res.status(400).send({ error: error.message });
    }
});

// Get History
router.get('/history', auth, async (req, res) => {
    try {
        const history = await Agreement.find({ user_id: req.user._id }).sort({ created_at: -1 });
        res.send(history);
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
