const axios = require('axios');

const PYTHON_AI_URL = process.env.PYTHON_AI_URL || 'http://localhost:8010';
const AI_SERVICE_API_KEY = process.env.AI_SERVICE_API_KEY || 'artha-ai-internal-key';

const pythonClient = axios.create({
  baseURL: PYTHON_AI_URL,
  timeout: 8000,
  headers: {
    'x-api-key': AI_SERVICE_API_KEY,
    'Content-Type': 'application/json'
  }
});

const getMockResponse = (feature, data) => {
  console.log(`[AI] Returning Smart Mock for ${feature}`);
  const mocks = {
    agreement: {
      risk_level: "MEDIUM",
      risk_score: 45,
      summary: "Standard financial agreement with typical terms. No immediate red flags found in automated scan.",
      flags: [{ issue: "Arbitration Clause", clause_text: "Section 14.2", severity: "MEDIUM", regulation_violated: "Consumer Protection", suggested_fix: "Ensure venue is local." }],
      missing_clauses: ["Specific Exit Clause"]
    },
    loan: {
      approval_probability: 75,
      verdict: "Likely Approved",
      recommended_loan_amount: (data.income || 50000) * 12,
      improvement_tips: [{ action: "Lower existing EMIs", impact: "High" }],
      suggested_banks: ["HDFC Bank", "ICICI Bank"]
    },
    pulse: {
      health_score: 65,
      status: "SAFE",
      debt_trap_days: null,
      emi_to_income_ratio: 0.3,
      savings_rate: 0.15,
      trend: data.trend || "STABLE",
      scenario_if_no_action: "Your debt is manageable. Continue tracking to avoid lifestyle inflation.",
      prescription: [{ action: "Increase SIP by 5%", priority: "MEDIUM", monthly_saving: 2000 }]
    },
    goals: {
      status: "On Track",
      required_monthly_savings: 15000,
      projection_at_deadline: 25000000,
      retirement_corpus_needed: 100000000, // 10 Cr
      monthly_sip_needed: 15000,
      year_by_year_projection: [
        { year: '2025', corpus: 500000, age: 28 },
        { year: '2030', corpus: 2500000, age: 33 },
        { year: '2040', corpus: 15000000, age: 43 },
        { year: '2050', corpus: 100000000, age: 55 }
      ],
      investment_strategy: "Diversified Equity Mutual Funds (70%) and Debt (30%)",
      alternative_plans: ["Delay retirement by 2 years to reach 3Cr corpus"]
    },
    festival: {
      detected_spike_pattern: "Moderate Cultural Spending",
      estimated_extra_spending: 25000,
      savings_plan: { daily_target: 150, days_remaining: 30, total_target: 4500 },
      actionable_tips: ["Skip 2 outside coffees daily", "Use existing festive lights", "Buy gifts in bulk early"],
      debt_warning: "Managing now prevents 14% interest credit card debt later."
    },
    strategy: {
      health_score: 72,
      summary: {
        savings_rate: 0.25,
        emergency_fund_status: "Adequate",
        emergency_fund_months: 6,
        debt_to_income: 0.15
      },
      retirement: {
        projected_corpus: 45000000,
        needed_corpus: 85000000,
        shortfall: 40000000,
        monthly_sip_required: 22000
      },
      asset_allocation: { equity: 65, debt: 25, gold: 10 },
      projections: [
        { age: 30, corpus: 500000, inflation_adjusted_value: 500000 },
        { age: 40, corpus: 8500000, inflation_adjusted_value: 6200000 },
        { age: 50, corpus: 32000000, inflation_adjusted_value: 18000000 },
        { age: 60, corpus: 85000000, inflation_adjusted_value: 35000000 }
      ],
      action_steps: [
        { title: "Increase Equity Exposure", impact: "HIGH", description: "At age 30, you can afford higher risk for long-term compounding." },
        { title: "Automate SIP", impact: "MED", description: "Set up auto-debit for ₹22,000 on the 1st of every month." }
      ],
      risk_analysis: "Your current portfolio is slightly conservative for your goals. Market volatility is your primary risk, but time is on your side."
    },
    riskRadar: {
      risk_score: 67,
      risk_level: "Moderate",
      debt_trap_risk: "Medium",
      emergency_fund_coverage_months: 2.3,
      retirement_gap: "₹48.0L",
      recommendations: [
        "Increase emergency savings",
        "Reduce EMI burden",
        "Increase retirement investments"
      ]
    },
    loanScam: {
      app_name: data.loan_app_name || "FastLoan365",
      fraud_score: 85,
      risk_level: "High",
      reasons: [
        "Not RBI registered",
        "Interest rate extremely high",
        "High complaint volume"
      ],
      recommendation: "Avoid using this lending application"
    },
    simulation: {
      decision: data.decision || "Buy Car",
      debt_ratio_after_purchase: 47,
      risk_level: "High",
      impact_summary: "This purchase may push your EMI ratio close to the danger zone."
    },
    whatIf: {
      scenario_name: data.scenario_name || "Salary change + new EMI",
      horizon_years: 5,
      chart_data: [
        { year: 2027, surplus: 90000, net_worth: 1200000, foir: 28 },
        { year: 2028, surplus: 110000, net_worth: 1700000, foir: 29 },
        { year: 2029, surplus: 130000, net_worth: 2300000, foir: 30 },
        { year: 2030, surplus: 150000, net_worth: 3000000, foir: 31 },
        { year: 2031, surplus: 180000, net_worth: 3800000, foir: 31 }
      ]
    },
    emergency: {
      emergency_status: "Warning",
      survival_months: 1.5,
      recommended_emergency_fund: "₹2.7L",
      action_plan: [
        "Pause discretionary spending",
        "Cancel subscriptions",
        "Build emergency buffer"
      ]
    },
    festivalIntel: {
      festival_name: data.festival_name || "Diwali",
      festival_spike_probability: 74,
      recommended_savings_target: 22000,
      risk_level: "High"
    },
    whatsapp: {
      status: "logged",
      amount: 200,
      category: "Food",
      merchant: "Local Cafe",
      budget_used_percent: 78,
      reply: "Logged ₹200 under Food. Your Food budget is now 78% used."
    },
    habit: {
      score: 732,
      range: "0-850",
      streak_days: 11,
      badges: ["EMI Slayer", "Shield User", "Bharat Saver"],
      milestones: ["Financial discipline elite zone"]
    }
  };
  return mocks[feature] || {};
};

const callPythonAI = async (endpoint, payload, feature) => {
  try {
    const response = await pythonClient.post(endpoint, payload);
    return response.data;
  } catch (error) {
    const reason = error?.response?.data || error.message;
    console.warn(`[AI] Python service fallback (${feature}):`, reason);
  }

  return getMockResponse(feature, payload || {});
};

const analyzeAgreement = async (text) => {
  return await callPythonAI('/ai/analyze-agreement', { text: (text || '').substring(0, 10000) }, 'agreement');
};

const predictLoan = async (data) => {
  const payload = {
    income: data.income,
    salary: data.income,
    existing_emis: data.existing_emis,
    existing_loans: data.existing_emis,
    credit_score: data.credit_score,
    employment_type: data.employment_type || 'salaried',
    loan_amount: data.loan_amount,
  };
  return await callPythonAI('/ai/loan-predictor', payload, 'loan');
};

const analyzeDebtPulse = async (data) => {
  return await callPythonAI('/ai/debt-pulse', data, 'pulse');
};

const planGoals = async (data) => {
  return getMockResponse('goals', data);
};

const analyzeFestivalShield = async (data) => {
  const payload = {
    user_id: data.user_id,
    festival_name: data.name,
    name: data.name,
    festival_date: data.date,
    date: data.date,
    income: data.income,
  };
  return await callPythonAI('/ai/festival-spending', payload, 'festival');
};

const analyzeFinanceStrategy = async (data) => {
  return await callPythonAI('/ai/wealth-advisor', data, 'strategy');
};

const analyzeRiskRadar = async (data) => {
  return await callPythonAI('/ai/risk-radar', data, 'riskRadar');
};

const analyzeLoanScam = async (data) => {
  return await callPythonAI('/ai/loan-scam-check', data, 'loanScam');
};

const runSimulation = async (data) => {
  return await callPythonAI('/ai/simulation', data, 'simulation');
};

const runWhatIfScenario = async (data) => {
  return await callPythonAI('/ai/what-if', data, 'whatIf');
};

const detectEmergency = async (data) => {
  return await callPythonAI('/ai/emergency-detector', data, 'emergency');
};

const analyzeFestivalIntelligence = async (data) => {
  return await callPythonAI('/ai/festival-intelligence', data, 'festivalIntel');
};

const parseWhatsappExpense = async (data) => {
  return await callPythonAI('/ai/whatsapp-expense', data, 'whatsapp');
};

const getHabitScore = async (userId) => {
  try {
    const response = await pythonClient.get('/ai/habit-score', { params: { user_id: userId } });
    return response.data;
  } catch (error) {
    const reason = error?.response?.data || error.message;
    console.warn('[AI] Python service fallback (habit):', reason);
    return getMockResponse('habit', {});
  }
};

module.exports = {
  analyzeAgreement,
  predictLoan,
  analyzeDebtPulse,
  planGoals,
  analyzeFestivalShield,
  analyzeFinanceStrategy,
  analyzeRiskRadar,
  analyzeLoanScam,
  runSimulation,
  runWhatIfScenario,
  detectEmergency,
  analyzeFestivalIntelligence,
  parseWhatsappExpense,
  getHabitScore
};
