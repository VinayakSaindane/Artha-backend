const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

const authRoutes = require('./routes/auth');
const expenseRoutes = require('./routes/expenses');
const shieldRoutes = require('./routes/shield');
const mainRoutes = require('./routes/main');
const festivalRoutes = require('./routes/festival');
const limitsRoutes = require('./routes/limits');
const aiIntelligenceRoutes = require('./routes/ai-intelligence');
const { schemesRouter } = require('./routes/schemes');
const { getSchemesDb } = require('../lib/schemesStore');
const userRoutes = require('./routes/user');

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Database Connection
mongoose.connect(process.env.MONGODB_URI)
    .then(() => console.log('Connected to MongoDB Atlas'))
    .catch((err) => console.error('MongoDB Connection Error:', err));

// Validate schemes dataset on startup
try {
    const schemesDb = getSchemesDb();
    console.log(`Schemes DB loaded. Version ${schemesDb.version}, items: ${schemesDb.schemes.length}`);
} catch (error) {
    console.error('Failed to load schemes DB:', error.message);
    process.exit(1);
}

// Routes
const incomeRoutes = require('./routes/income');

app.use('/api/auth', authRoutes);
app.use('/api/expenses', expenseRoutes);
app.use('/api/income', incomeRoutes);
app.use('/api/shield', shieldRoutes);
app.use('/api/festival', festivalRoutes);
app.use('/api/limits', limitsRoutes);
app.use('/api/ai', aiIntelligenceRoutes);
app.use('/api/schemes', schemesRouter);
app.use('/api/user', userRoutes);
app.use('/api', mainRoutes); // Handles /score and /pulse and /goals

// Base Route
app.get('/', (req, res) => {
    res.send({ message: 'ARTHA AI Backend (Node.js/Express/MongoDB) is running!' });
});

// Error Handling
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send({ error: 'Internal Server Error', message: err.message });
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
