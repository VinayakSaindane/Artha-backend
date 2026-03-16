# Backend AI/ML & Formula Logic Reference

This document summarizes the main formulas, scoring engines, and AI/ML logic powering the backend features.

---

## 1. Habit Score Engine

**File:** ai-service/ai_services/habit_score_engine.py

- **Purpose:** Computes a financial habit score (0–850) for a user based on 90 days of income, expenses, and EMI data.
- **Key Formulas:**
    - **Savings Rate:**  
      $$
      \text{savings\_rate} = \max\left(0, \frac{\text{income\_total} - \text{expense\_total}}{\max(\text{income\_total}, 1)}\right)
      $$
    - **Budget Compliance:**  
      $$
      \text{budget\_compliance} = \max\left(0, 1 - \frac{\text{overspend\_days}}{90}\right)
      $$
    - **Debt Reduction:**  
      $$
      \text{debt\_reduction} = \max\left(0, 1 - \frac{\text{emi\_total}}{\max(\text{income\_total}, 1)}\right)
      $$
    - **No Overspend Streak:**  
      $$
      \text{no\_overspend\_streak} = \max(0, 14 - \text{overspend\_days})
      $$
    - **Final Score:**  
      $$
      \text{raw} = 0.35 \times \text{savings\_rate} + 0.25 \times \text{budget\_compliance} + 0.20 \times \min\left(1, \frac{\text{no\_overspend\_streak}}{14}\right) + 0.20 \times \text{debt\_reduction}
      $$
      $$
      \text{score} = \min(850, \max(0, \text{round}(\text{raw} \times 850)))
      $$
- **Badges & Milestones:** Awarded for high savings, compliance, or debt reduction.

---

## 2. Scam Detector

**File:** ai-service/ai_services/scam_detector.py

- **Purpose:** Flags risky lending apps using a weighted risk formula.
- **Key Formulas:**
    - **Regulatory Risk:**  
      $$
      \text{regulatory\_risk} = \begin{cases}
      0 & \text{if app is RBI registered} \\
      100 & \text{otherwise}
      \end{cases}
      $$
    - **Interest Rate Risk:**  
      $$
      \text{interest\_rate\_risk} = \min(100, \max(0, \frac{\text{interest\_rate} - 24}{36} \times 100))
      $$
    - **Complaint Rate:**  
      $$
      \text{complaint\_rate} = \min(100, \text{complaint\_count} \times 7.5)
      $$
    - **Permission Risk:**  
      $$
      \text{permission\_risk} = \min(100, \text{permission\_hits} \times 30)
      $$
    - **Fraud Score:**  
      $$
      \text{fraud\_score} = 0.35 \times \text{regulatory\_risk} + 0.30 \times \text{interest\_rate\_risk} + 0.20 \times \text{complaint\_rate} + 0.15 \times \text{permission\_risk}
      $$
      (Clipped to 0–100)
- **Risk Level:**  
  - High: $\geq 70$  
  - Moderate: $40$–$69$  
  - Low: $< 40$

---

## 3. Festival Intelligence

**File:** ai-service/ai_services/festival_intelligence.py

- **Purpose:** Predicts festival spending spikes and risk.
- **Key Formulas:**
    - **Projected Spike:**  
      $$
      \text{projected\_spike} = \text{average\_event\_spend} \times \text{seasonal\_multiplier}
      $$
    - **Spike Probability:**  
      $$
      \text{festival\_spike\_probability} = \min(95, \max(10, \text{round}(\frac{\text{projected\_spike}}{\text{monthly\_expenses}} \times 100)))
      $$
    - **Risk Level:**  
      - High: $\geq 70$  
      - Moderate: $40$–$69$  
      - Low: $< 40$

---

## 4. Financial Simulator

**File:** ai-service/ai_services/financial_simulator.py

- **Purpose:** Simulates the impact of new loans/purchases on user finances.
- **Key Formulas:**
    - **Debt Ratio After Purchase:**  
      $$
      \text{debt\_ratio\_after\_purchase} = \text{round}\left(\frac{\text{total\_emi}}{\text{current\_income}} \times 100, 2\right)
      $$
    - **Savings Reduction Percent:**  
      $$
      \text{savings\_reduction\_percent} = \text{round}\left(\frac{\text{savings} - \text{savings\_after}}{\max(\text{savings}, 1)} \times 100, 2\right)
      $$
    - **Risk Level:**  
      - High: $\geq 45\%$  
      - Moderate: $30$–$44.99\%$  
      - Low: $< 30\%$

---

## 5. Eligibility Engine

**File:** lib/eligibilityEngine.js

- **Purpose:** Checks user eligibility for government schemes using rules and formulas.
- **Key Logic:**
    - **Criteria Types:** age, income, gender, occupation, caste, state, house status, children, etc.
    - **Each criterion** is checked using a formula (e.g., age range, income min/max, gender match).
    - **Match Score:**  
      $$
      \text{matchScore} = \text{round}\left(\frac{\text{metCount}}{\text{totalCriteria}} \times 100\right)
      $$
    - **Eligibility Status:**  
      - eligible: all hard criteria met  
      - partial: $\text{matchScore} \geq 60$  
      - not_eligible: otherwise

---

## 6. Other Features

- **PDF/WhatsApp Parsing:** Uses rule-based extraction (see ai-service/utils/).
- **Risk Radar, Debt Pulse, Wealth Advisor:** Use similar scoring or rule-based logic, sometimes with ML models (see ai-service/services/).

---

**Tip:** For each feature, you can show these formulas and explain the logic to judges. The code is modular and transparent, so every score or risk is explainable.
