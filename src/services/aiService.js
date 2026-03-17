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

const toNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const calculateFutureValueWithSip = (currentSavings, monthlySip, years, annualReturn = 0.1) => {
  const monthlyRate = annualReturn / 12;
  const months = Math.max(1, Math.round(years * 12));
  const savingsGrowth = currentSavings * Math.pow(1 + annualReturn, years);

  if (monthlyRate <= 0) {
    return savingsGrowth + monthlySip * months;
  }

  const sipGrowth = monthlySip * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate);
  return savingsGrowth + sipGrowth;
};

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
    },
    macroAlert: {
      event_detected: {
        event: "Geopolitical Conflict",
        confidence: 0.71,
        severity: "High",
        expected_impact_window_days: 10
      },
      macro_risk_index: {
        score: 66,
        risk_band: "High Risk",
        formula: {
          market_volatility: 72,
          inflation_trend: 61,
          geopolitical_risk: 75,
          economic_sentiment: 48
        }
      },
      macro_impact: {
        stock_market_risk: "High",
        inflation_risk: "Moderate",
        employment_risk: "Moderate",
        loan_rate_trend: "Increasing"
      },
      personal_financial_impact: {
        portfolio_impact: "-12.0%",
        monthly_expense_increase: "₹3500",
        new_debt_ratio: "44%",
        financial_risk_level: "Medium"
      },
      recommended_actions: [
        "Increase emergency savings to 6 months",
        "Reduce volatile equity exposure",
        "Hold higher liquidity",
        "Avoid taking new loans during high uncertainty"
      ],
      macro_risk_chart: [
        { name: "Market Volatility", score: 72 },
        { name: "Inflation Trend", score: 61 },
        { name: "Geopolitical Risk", score: 75 },
        { name: "Economic Sentiment", score: 48 }
      ]
    },
    macroSimulation: {
      scenario: "war escalation",
      horizon_months: 12,
      projection_formula: "Surplus(t) = Income(t) - EMI(t) - Expenses(t)",
      chart_data: [
        { month: 1, savings: 202000, net_worth: 510000, debt_ratio: 36, risk_level: "Moderate" },
        { month: 3, savings: 196000, net_worth: 500500, debt_ratio: 38, risk_level: "Moderate" },
        { month: 6, savings: 181500, net_worth: 479000, debt_ratio: 41, risk_level: "High" },
        { month: 9, savings: 168000, net_worth: 455000, debt_ratio: 43, risk_level: "High" },
        { month: 12, savings: 154500, net_worth: 434000, debt_ratio: 45, risk_level: "High" }
      ],
      scenario_context: {
        title: "War Escalation",
        headline: "War escalation would raise inflation pressure and hit portfolio stability quickly.",
        description: "Expect import-led inflation, higher household costs, and weaker market confidence over the next few months.",
        impact_window_months: 12,
        drivers: {
          income_change_pct: 0,
          monthly_inflation_pct: 1,
          emi_growth_pct: 0.2,
          market_drawdown_pct: 12,
          macro_risk_score: 66,
        },
      },
      personal_financial_impact: {
        portfolio_impact: "-15.0%",
        monthly_expense_increase: "₹3,500",
        new_debt_ratio: "45.0%",
        financial_risk_level: "High",
        ending_savings: 154500,
        ending_net_worth: 434000,
      },
      recommended_actions: [
        "Increase emergency cash and keep at least 2 months of core expenses highly liquid",
        "Trim exposure to highly volatile equities until headline risk cools",
        "Lock essential monthly spending categories and review fuel and food inflation weekly",
        "Reduce EMI pressure before debt ratio crosses deeper stress territory",
      ],
      summary: {
        ending_savings: 154500,
        ending_net_worth: 434000,
        peak_debt_ratio: 45,
        risk_level: "High",
        headline: "War escalation would raise inflation pressure and hit portfolio stability quickly.",
      }
    }
  };
  if (feature === 'macroSimulation') {
    const scenario = String(data?.scenario || mocks.macroSimulation.scenario).toLowerCase();
    const baseChart = [
      { name: "Market Volatility", score: 72 },
      { name: "Inflation Trend", score: 61 },
      { name: "Geopolitical Risk", score: 75 },
      { name: "Economic Sentiment", score: 48 }
    ];

    const adjusted = baseChart.map((row) => ({ ...row }));
    if (scenario.includes('recession')) {
      adjusted[0].score = 78;
      adjusted[3].score = 64;
    } else if (scenario.includes('job loss')) {
      adjusted[3].score = 72;
      adjusted[1].score = 57;
    } else if (scenario.includes('interest') || scenario.includes('rate')) {
      adjusted[1].score = 74;
      adjusted[0].score = 69;
    } else if (scenario.includes('market crash')) {
      adjusted[0].score = 86;
      adjusted[3].score = 59;
    }

    return {
      ...mocks.macroSimulation,
      scenario: data?.scenario || mocks.macroSimulation.scenario,
      macro_risk_chart: adjusted,
    };
  }

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

const analyzeAgreement = async (text, userContext = {}) => {
  return await callPythonAI(
    '/ai/analyze-agreement',
    {
      text: (text || '').substring(0, 10000),
      user_context: userContext,
    },
    'agreement'
  );
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
  const age = toNumber(data.age, 28);
  const retirementAge = Math.max(age + 1, toNumber(data.retirement_age, 55));
  const yearsToRetirement = Math.max(1, retirementAge - age);
  const income = toNumber(data.income, 50000);
  const monthlyExpenses = Math.max(0, toNumber(data.monthly_expenses, income * 0.6));
  const existingEmis = Math.max(0, toNumber(data.existing_emis, 0));
  const goalCommitment = Math.max(0, toNumber(data.goal_commitment, 0));
  const currentSavings = Math.max(0, toNumber(data.current_savings, income * 6));
  const currentSip = Math.max(0, toNumber(data.monthly_sip, Math.max(0, income - monthlyExpenses - existingEmis - goalCommitment)));
  const inflationRate = 0.06;
  const expectedReturn = 0.1;
  const annualExpenseNeed = Math.max(monthlyExpenses * 12, income * 12 * 0.45);
  const retirementCorpusNeeded = Math.round(annualExpenseNeed * 25 * Math.pow(1 + inflationRate, yearsToRetirement));

  const months = yearsToRetirement * 12;
  const monthlyRate = expectedReturn / 12;
  const futureCurrentSavings = currentSavings * Math.pow(1 + expectedReturn, yearsToRetirement);
  let monthlySipNeeded = 0;

  if (retirementCorpusNeeded > futureCurrentSavings) {
    const shortfall = retirementCorpusNeeded - futureCurrentSavings;
    monthlySipNeeded = Math.round((shortfall * monthlyRate) / (Math.pow(1 + monthlyRate, months) - 1));
  }

  const projectionAtDeadline = Math.round(calculateFutureValueWithSip(currentSavings, currentSip, yearsToRetirement, expectedReturn));
  const requiredMonthlySavings = Math.max(monthlySipNeeded, goalCommitment);

  const status = currentSip >= requiredMonthlySavings
    ? 'On Track'
    : currentSip >= requiredMonthlySavings * 0.75
      ? 'Needs Small Increase'
      : 'At Risk';

  const yearByYearProjection = [];
  for (let year = 0; year <= yearsToRetirement; year += 1) {
    yearByYearProjection.push({
      year: String(new Date().getFullYear() + year),
      age: age + year,
      corpus: Math.round(calculateFutureValueWithSip(currentSavings, currentSip, year, expectedReturn))
    });
  }

  const recommendationGap = Math.max(0, requiredMonthlySavings - currentSip);

  return {
    status,
    required_monthly_savings: requiredMonthlySavings,
    projection_at_deadline: projectionAtDeadline,
    retirement_corpus_needed: retirementCorpusNeeded,
    monthly_sip_needed: monthlySipNeeded,
    year_by_year_projection: yearByYearProjection,
    investment_strategy: expectedReturn >= 0.1
      ? 'Core equity index funds with debt rebalancing every year.'
      : 'Balanced mutual funds with steady debt allocation.',
    alternative_plans: recommendationGap > 0
      ? [
        `Increase monthly SIP by ₹${recommendationGap.toLocaleString('en-IN')} to stay on-track.`,
        'Reduce monthly discretionary expenses by 10% and redirect to goal SIP.'
      ]
      : [
        'Continue current SIP and review every quarter.',
        'Top-up SIP by 5% annually to beat inflation comfortably.'
      ]
  };
};

const analyzeFestivalShield = async (data) => {
  const payload = {
    user_id: data.user_id,
    festival_name: data.name,
    name: data.name,
    festival_date: data.date,
    date: data.date,
    income: data.income,
    target_amount: data.target_amount,
    expense_insights: data.expenseInsights,
    past_expenses: data.pastExpenses,
  };

  const aiResponse = await callPythonAI('/ai/festival-spending', payload, 'festival');

  const averageMonthlySpend = toNumber(data?.expenseInsights?.average_monthly_spend, 0);
  const festiveCategorySpend = toNumber(data?.expenseInsights?.festive_category_spend, 0);
  const providedTarget = Math.max(0, toNumber(data.target_amount, 0));
  const inferredTarget = Math.round((averageMonthlySpend * 0.35) + (festiveCategorySpend * 0.12));
  const totalTarget = Math.max(1000, providedTarget || inferredTarget || 5000);
  const income = Math.max(1, toNumber(data.income, 50000));

  const today = new Date();
  const festivalDate = new Date(data.date);
  const msRemaining = festivalDate.getTime() - today.getTime();
  const daysRemaining = Math.max(1, Math.ceil(msRemaining / (1000 * 60 * 60 * 24)));

  const dailyTarget = Math.max(1, Math.round(totalTarget / daysRemaining));
  const weeklyTarget = Math.round(dailyTarget * 7);
  const spendToIncomeRatio = averageMonthlySpend / income;
  const intensity = spendToIncomeRatio > 0.75 ? 'High' : spendToIncomeRatio > 0.5 ? 'Moderate' : 'Stable';

  const categoryBreakdown = data?.expenseInsights?.category_breakdown || {};
  const topCategories = Object.entries(categoryBreakdown)
    .sort((a, b) => toNumber(b[1], 0) - toNumber(a[1], 0))
    .slice(0, 3)
    .map(([category]) => category);

  const generatedTasks = [
    {
      title: `Auto-save ₹${dailyTarget} every day until ${festivalDate.toLocaleDateString('en-IN')}`,
      cadence: 'daily',
      amount: dailyTarget
    },
    {
      title: `Set weekly checkpoint of ₹${weeklyTarget} and move surplus to festival wallet`,
      cadence: 'weekly',
      amount: weeklyTarget
    },
    {
      title: `Cap spend in ${topCategories[0] || 'Food'} by 12% and redirect difference to festival savings`,
      cadence: 'weekly',
      amount: Math.round(totalTarget * 0.2)
    }
  ];

  const dynamicResponse = {
    detected_spike_pattern: `${intensity} spending pressure from your tracked expenses`,
    estimated_extra_spending: totalTarget,
    savings_plan: {
      daily_target: dailyTarget,
      days_remaining: daysRemaining,
      total_target: totalTarget
    },
    actionable_tips: [
      `Pause one low-priority spend from ${topCategories[0] || 'Food'} and save the amount daily.`,
      `Keep festival purchases under ₹${Math.round(totalTarget * 0.65).toLocaleString('en-IN')} to avoid debt rollover.`,
      `Track expenses every evening; your daily safe spend before festival is ₹${Math.max(0, Math.round((income - averageMonthlySpend) / 30)).toLocaleString('en-IN')}.`
    ],
    generated_tasks: generatedTasks,
    debt_warning: `At current trend, festive spending can add pressure. Saving ₹${dailyTarget.toLocaleString('en-IN')}/day helps avoid post-festival debt.`
  };

  return {
    ...aiResponse,
    ...dynamicResponse,
    // Keep AI narrative only as supplementary metadata, never as the source of truth
    // for spend, savings targets, or detected pattern shown to the user.
    ai_generated_pattern: aiResponse.detected_spike_pattern || null,
    ai_generated_tips: Array.isArray(aiResponse.actionable_tips) ? aiResponse.actionable_tips : [],
    ai_generated_warning: aiResponse.debt_warning || null,
    estimated_extra_spending: dynamicResponse.estimated_extra_spending,
    savings_plan: dynamicResponse.savings_plan,
    actionable_tips: dynamicResponse.actionable_tips,
    generated_tasks: dynamicResponse.generated_tasks,
    debt_warning: dynamicResponse.debt_warning,
    detected_spike_pattern: dynamicResponse.detected_spike_pattern
  };
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

const getMacroRiskAlert = async (data = {}) => {
  try {
    const response = await pythonClient.get('/ai/macro-risk-alert', {
      params: {
        user_id: data.user_id,
        force_refresh: Boolean(data.force_refresh)
      }
    });
    return response.data;
  } catch (error) {
    const reason = error?.response?.data || error.message;
    console.warn('[AI] Python service fallback (macro alert):', reason);
    return getMockResponse('macroAlert', data || {});
  }
};

const runMacroRiskSimulation = async (data = {}) => {
  return await callPythonAI('/ai/macro-risk-simulation', data, 'macroSimulation');
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
  getHabitScore,
  getMacroRiskAlert,
  runMacroRiskSimulation
};
