from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx
from bson import ObjectId

from app.config import get_settings
from app.database import get_db


class MacroRiskEngineService:
    def __init__(self) -> None:
        self._cache_lock = asyncio.Lock()
        self._cached_alert: dict[str, Any] | None = None
        self._cached_at: datetime | None = None
        self._cache_ttl = timedelta(hours=6)

        self._event_keywords: dict[str, list[str]] = {
            "Geopolitical Conflict": ["war", "conflict", "missile", "border", "sanctions", "military"],
            "Recession Signal": ["recession", "layoffs", "unemployment", "slowdown", "gdp contraction"],
            "Inflation Spike": ["inflation", "cpi", "food prices", "fuel prices", "price surge"],
            "Market Crash": ["market crash", "selloff", "bear market", "volatility", "panic"],
            "Pandemic Alert": ["pandemic", "outbreak", "virus", "health emergency", "lockdown"],
            "Interest Rate Hike": ["rate hike", "repo rate", "federal reserve", "tightening", "hawkish"],
        }

    async def get_macro_risk_alert(self, payload: dict[str, Any] | None = None, force_refresh: bool = False) -> dict[str, Any]:
        payload = payload or {}
        user_profile = payload.get("user_profile") or {}
        user_id = payload.get("user_id")

        should_refresh = force_refresh or self._cached_alert is None or self._cached_at is None
        if not should_refresh and self._cached_at is not None:
            should_refresh = datetime.utcnow() - self._cached_at > self._cache_ttl

        if should_refresh:
            async with self._cache_lock:
                now_stale = self._cached_alert is None or self._cached_at is None
                expired = self._cached_at is None or (datetime.utcnow() - self._cached_at > self._cache_ttl)
                if force_refresh or now_stale or expired:
                    self._cached_alert = await self._build_alert_payload()
                    self._cached_at = datetime.utcnow()

        base_alert = dict(self._cached_alert or await self._build_alert_payload())
        personal = await self._personal_financial_impact(base_alert, user_id=user_id, overrides=user_profile)
        recommendations = self._action_recommendation_engine(base_alert, personal)

        return {
            **base_alert,
            "personal_financial_impact": personal,
            "recommended_actions": recommendations,
            "cache": {
                "cached": self._cached_at is not None,
                "cached_at": self._cached_at.isoformat() if self._cached_at else None,
                "next_refresh_eta_seconds": int(max(0, (self._cache_ttl - (datetime.utcnow() - (self._cached_at or datetime.utcnow()))).total_seconds())),
            },
        }

    async def run_macro_risk_simulation(self, payload: dict[str, Any]) -> dict[str, Any]:
        scenario = str(payload.get("scenario") or "war escalation")
        horizon_months = min(24, max(1, int(payload.get("horizon_months") or 12)))
        user_id = payload.get("user_id")
        user_profile = payload.get("user_profile") or {}

        alert = await self.get_macro_risk_alert({"user_id": user_id, "user_profile": user_profile})
        user = await self._load_user_financials(user_id=user_id, overrides=user_profile)

        return self._what_if_scenario_simulator(
            scenario=scenario,
            horizon_months=horizon_months,
            alert=alert,
            user=user,
        )

    async def scheduled_refresh(self) -> None:
        async with self._cache_lock:
            self._cached_alert = await self._build_alert_payload()
            self._cached_at = datetime.utcnow()

    async def _build_alert_payload(self) -> dict[str, Any]:
        signals = await self._event_intelligence_engine()
        event = self._detect_top_event(signals)
        macro_impact = self._macro_economic_impact_model(signals=signals, top_event=event)

        return {
            "event_detected": event,
            "signal_summary": {
                "headlines_scanned": len(signals.get("headlines", [])),
                "market_volatility": signals.get("market_volatility"),
                "inflation_trend": signals.get("inflation_trend"),
                "economic_sentiment": signals.get("economic_sentiment"),
            },
            "macro_risk_index": {
                "score": macro_impact["macro_risk_score"],
                "risk_band": self._risk_band(macro_impact["macro_risk_score"]),
                "formula": {
                    "market_volatility": macro_impact["components"]["market_volatility"],
                    "inflation_trend": macro_impact["components"]["inflation_trend"],
                    "geopolitical_risk": macro_impact["components"]["geopolitical_risk"],
                    "economic_sentiment": macro_impact["components"]["economic_sentiment"],
                },
            },
            "macro_impact": macro_impact["risk_map"],
            "macro_risk_chart": self._macro_risk_chart(macro_impact),
        }

    async def _event_intelligence_engine(self) -> dict[str, Any]:
        settings = get_settings()
        headlines: list[str] = []
        market_volatility = 42.0
        inflation_trend = 55.0
        economic_sentiment = 48.0

        async with httpx.AsyncClient(timeout=8.0) as client:
            news_key = settings.news_api_key
            if news_key:
                try:
                    news_query = "war OR recession OR inflation OR market crash OR pandemic OR rate hike"
                    response = await client.get(
                        "https://newsapi.org/v2/everything",
                        params={
                            "q": news_query,
                            "language": "en",
                            "sortBy": "publishedAt",
                            "pageSize": 50,
                            "apiKey": news_key,
                        },
                    )
                    articles = response.json().get("articles", [])
                    headlines.extend([str(item.get("title") or "") for item in articles if item.get("title")])
                except Exception:
                    pass

            alpha_key = settings.alpha_vantage_api_key
            if alpha_key:
                try:
                    response = await client.get(
                        "https://www.alphavantage.co/query",
                        params={
                            "function": "GLOBAL_QUOTE",
                            "symbol": "SPY",
                            "apikey": alpha_key,
                        },
                    )
                    quote = response.json().get("Global Quote", {})
                    pct_text = str(quote.get("10. change percent") or "0").replace("%", "").strip()
                    pct = abs(float(pct_text or 0.0))
                    market_volatility = min(100.0, max(5.0, pct * 12.0))
                except Exception:
                    pass

            try:
                inflation_resp = await client.get(
                    "https://api.worldbank.org/v2/country/IN/indicator/FP.CPI.TOTL.ZG",
                    params={"format": "json", "per_page": 2},
                )
                gdp_resp = await client.get(
                    "https://api.worldbank.org/v2/country/IN/indicator/NY.GDP.MKTP.KD.ZG",
                    params={"format": "json", "per_page": 2},
                )

                inflation_rows = inflation_resp.json()[1] if isinstance(inflation_resp.json(), list) and len(inflation_resp.json()) > 1 else []
                gdp_rows = gdp_resp.json()[1] if isinstance(gdp_resp.json(), list) and len(gdp_resp.json()) > 1 else []

                inflation_value = float((inflation_rows[0] or {}).get("value") or 6.0) if inflation_rows else 6.0
                gdp_value = float((gdp_rows[0] or {}).get("value") or 5.5) if gdp_rows else 5.5

                inflation_trend = min(100.0, max(10.0, inflation_value * 8.0))
                economic_sentiment = min(100.0, max(10.0, (10.0 - gdp_value) * 10.0 + 25.0))
            except Exception:
                pass

        if not headlines:
            headlines = [
                "Global markets mixed amid recession concerns and persistent inflation pressure",
                "Oil prices jump on geopolitical conflict escalation fears",
                "Central banks signal possible rate hike cycle extension",
                "Healthcare agencies monitor new pandemic cluster in multiple regions",
            ]

        return {
            "headlines": headlines,
            "market_volatility": round(market_volatility, 2),
            "inflation_trend": round(inflation_trend, 2),
            "economic_sentiment": round(economic_sentiment, 2),
        }

    def _detect_top_event(self, signals: dict[str, Any]) -> dict[str, Any]:
        headlines = [str(x).lower() for x in signals.get("headlines", [])]
        best_event = "Geopolitical Conflict"
        best_score = 0.0

        for event, keywords in self._event_keywords.items():
            hit_count = 0
            weighted_hits = 0.0
            for text in headlines:
                matches = sum(1 for keyword in keywords if keyword in text)
                if matches > 0:
                    hit_count += 1
                    weighted_hits += min(3, matches) / 3.0

            confidence = 0.0
            if headlines:
                confidence = min(1.0, (weighted_hits / len(headlines)) * 1.8)

            if confidence > best_score:
                best_score = confidence
                best_event = event

        severity = "Low"
        if best_score >= 0.65:
            severity = "High"
        elif best_score >= 0.35:
            severity = "Moderate"

        return {
            "event": best_event,
            "confidence": round(best_score, 2),
            "severity": severity,
            "expected_impact_window_days": 10 if severity == "High" else 20 if severity == "Moderate" else 30,
        }

    def _macro_economic_impact_model(self, signals: dict[str, Any], top_event: dict[str, Any]) -> dict[str, Any]:
        event_name = str(top_event.get("event") or "").lower()
        event_severity = str(top_event.get("severity") or "Low")

        geopolitical_risk = 30.0
        if "geopolitical" in event_name or "war" in event_name:
            geopolitical_risk = 78.0 if event_severity == "High" else 58.0
        elif "pandemic" in event_name:
            geopolitical_risk = 46.0
        elif "recession" in event_name:
            geopolitical_risk = 40.0

        market_volatility = float(signals.get("market_volatility") or 40.0)
        inflation_trend = float(signals.get("inflation_trend") or 50.0)
        economic_sentiment = float(signals.get("economic_sentiment") or 45.0)

        macro_risk_score = (
            0.4 * market_volatility
            + 0.3 * inflation_trend
            + 0.2 * geopolitical_risk
            + 0.1 * economic_sentiment
        )
        macro_risk_score = max(0.0, min(100.0, macro_risk_score))

        risk_map = {
            "stock_market_risk": self._bucket_label((market_volatility + geopolitical_risk) / 2.0),
            "inflation_risk": self._bucket_label(inflation_trend),
            "employment_risk": self._bucket_label((economic_sentiment + inflation_trend) / 2.0),
            "loan_rate_trend": "Increasing" if inflation_trend > 50 else "Stable",
            "currency_risk": self._bucket_label((geopolitical_risk + market_volatility) / 2.2),
        }

        return {
            "macro_risk_score": round(macro_risk_score, 2),
            "components": {
                "market_volatility": round(market_volatility, 2),
                "inflation_trend": round(inflation_trend, 2),
                "geopolitical_risk": round(geopolitical_risk, 2),
                "economic_sentiment": round(economic_sentiment, 2),
            },
            "risk_map": risk_map,
        }

    async def _personal_financial_impact(
        self,
        alert: dict[str, Any],
        user_id: str | None,
        overrides: dict[str, Any] | None,
    ) -> dict[str, Any]:
        profile = await self._load_user_financials(user_id=user_id, overrides=overrides)

        macro_score = float(alert.get("macro_risk_index", {}).get("score") or 45.0)
        high_risk_multiplier = 1.15 if macro_score >= 60 else 1.0

        portfolio = max(0.0, float(profile.get("investments") or 0.0))
        base_expenses = max(1.0, float(profile.get("expenses") or 0.0))
        income = max(1.0, float(profile.get("income") or 0.0))
        emi = max(0.0, float(profile.get("loan_emi") or 0.0))
        savings = max(0.0, float(profile.get("savings") or 0.0))

        portfolio_drop_pct = min(30.0, max(3.0, (macro_score * 0.18) * high_risk_multiplier))
        inflation_pct = min(10.0, max(2.0, macro_score * 0.065))
        monthly_expense_increase = base_expenses * (inflation_pct / 100.0)

        stressed_expenses = base_expenses + monthly_expense_increase
        debt_ratio = min(100.0, ((emi + stressed_expenses) / income) * 100.0)
        savings_runway = round(savings / max(stressed_expenses, 1.0), 1)

        return {
            "portfolio_impact": f"-{portfolio_drop_pct:.1f}%",
            "portfolio_value_impact": round(-(portfolio * portfolio_drop_pct / 100.0), 2),
            "monthly_expense_increase": f"₹{round(monthly_expense_increase):,.0f}",
            "inflation_shock": round(inflation_pct, 2),
            "new_debt_ratio": f"{debt_ratio:.1f}%",
            "savings_runway_months": savings_runway,
            "financial_risk_level": self._bucket_label(debt_ratio),
            "inputs": {
                "income": round(income, 2),
                "expenses": round(base_expenses, 2),
                "savings": round(savings, 2),
                "investments": round(portfolio, 2),
                "loan_emi": round(emi, 2),
            },
        }

    def _action_recommendation_engine(self, alert: dict[str, Any], personal: dict[str, Any]) -> list[str]:
        actions: list[str] = []
        macro_score = float(alert.get("macro_risk_index", {}).get("score") or 45.0)
        runway = float(personal.get("savings_runway_months") or 0.0)

        if runway < 6:
            actions.append("Increase emergency savings to at least 6 months of expenses")

        if macro_score >= 60:
            actions.append("Reduce volatile equity exposure and rebalance toward diversified defensive assets")
            actions.append("Avoid taking new loans until macro volatility cools")
            actions.append("Hold higher liquidity for the next 90 days")
        elif macro_score >= 30:
            actions.append("Reduce discretionary spending by 10-15% and redirect to emergency corpus")
            actions.append("Keep staggered SIP strategy instead of lump-sum risk during uncertain weeks")
        else:
            actions.append("Continue disciplined investing, but keep a macro watchlist active")

        actions.append("Track fuel, food, and EMI-sensitive categories weekly for early stress signals")

        deduped: list[str] = []
        for item in actions:
            if item not in deduped:
                deduped.append(item)

        return deduped[:5]

    def _what_if_scenario_simulator(
        self,
        scenario: str,
        horizon_months: int,
        alert: dict[str, Any],
        user: dict[str, Any],
    ) -> dict[str, Any]:
        scenario_key = scenario.lower().strip()

        income = max(1.0, float(user.get("income") or 0.0))
        expenses = max(0.0, float(user.get("expenses") or 0.0))
        emi = max(0.0, float(user.get("loan_emi") or 0.0))
        savings = max(0.0, float(user.get("savings") or 0.0))
        investments = max(0.0, float(user.get("investments") or 0.0))

        macro_score = float(alert.get("macro_risk_index", {}).get("score") or 45.0)
        baseline_net_worth = max(0.0, savings + investments)

        monthly_income_drop = 0.0
        monthly_inflation = 0.006
        emi_growth = 0.002
        market_drawdown = 0.0

        if "war" in scenario_key:
            monthly_inflation = 0.010
            market_drawdown = 0.12
        elif "recession" in scenario_key:
            monthly_income_drop = 0.03
            monthly_inflation = 0.007
            market_drawdown = 0.18
        elif "job loss" in scenario_key:
            monthly_income_drop = 1.0
            monthly_inflation = 0.005
        elif "interest" in scenario_key or "rate" in scenario_key:
            emi_growth = 0.008
            monthly_inflation = 0.007
        elif "market crash" in scenario_key:
            market_drawdown = 0.22
            monthly_inflation = 0.006
        else:
            monthly_inflation = 0.006 + (macro_score / 10000.0)

        chart_data: list[dict[str, Any]] = []
        current_savings = savings
        current_investments = investments * (1.0 - market_drawdown)
        current_emi = emi

        for month in range(1, horizon_months + 1):
            if monthly_income_drop >= 1.0 and month <= 4:
                month_income = 0.0
            else:
                month_income = income * ((1.0 - monthly_income_drop) ** month)

            month_expense = expenses * ((1.0 + monthly_inflation) ** month)
            current_emi = current_emi * (1.0 + emi_growth)

            surplus = month_income - current_emi - month_expense
            current_savings += surplus
            current_investments *= (1.0 + max(-0.08, (0.008 - monthly_inflation / 2.0)))

            total_assets = max(0.0, current_savings + current_investments)
            annualized_income = max(1.0, month_income * 12.0)
            debt_ratio = min(100.0, ((current_emi * 12.0) / annualized_income) * 100.0)

            chart_data.append(
                {
                    "month": month,
                    "income": round(month_income, 2),
                    "emi": round(current_emi, 2),
                    "expenses": round(month_expense, 2),
                    "surplus": round(surplus, 2),
                    "savings": round(current_savings, 2),
                    "net_worth": round(total_assets, 2),
                    "debt_ratio": round(debt_ratio, 2),
                    "risk_level": self._bucket_label(max(debt_ratio, macro_score * 0.9)),
                }
            )

        first_month = chart_data[0]
        final_month = chart_data[-1]
        initial_expense_shock = max(0.0, first_month["expenses"] - expenses)
        net_worth_change_pct = 0.0
        if baseline_net_worth > 0:
            net_worth_change_pct = ((final_month["net_worth"] - baseline_net_worth) / baseline_net_worth) * 100.0

        scenario_context = self._scenario_context(
            scenario=scenario,
            macro_score=macro_score,
            monthly_income_drop=monthly_income_drop,
            monthly_inflation=monthly_inflation,
            emi_growth=emi_growth,
            market_drawdown=market_drawdown,
            horizon_months=horizon_months,
        )

        return {
            "scenario": scenario,
            "horizon_months": horizon_months,
            "projection_formula": "Surplus(t) = Income(t) - EMI(t) - Expenses(t)",
            "chart_data": chart_data,
            "macro_risk_chart": self._scenario_macro_risk_chart(
                alert=alert,
                scenario=scenario,
                scenario_context=scenario_context,
            ),
            "scenario_context": scenario_context,
            "personal_financial_impact": {
                "portfolio_impact": f"{net_worth_change_pct:+.1f}%",
                "monthly_expense_increase": f"₹{round(initial_expense_shock):,.0f}",
                "new_debt_ratio": f"{final_month['debt_ratio']:.1f}%",
                "financial_risk_level": final_month["risk_level"],
                "ending_savings": round(final_month["savings"], 2),
                "ending_net_worth": round(final_month["net_worth"], 2),
            },
            "recommended_actions": self._scenario_recommendations(
                scenario=scenario,
                final_month=final_month,
                horizon_months=horizon_months,
            ),
            "summary": {
                "ending_savings": round(final_month["savings"], 2),
                "ending_net_worth": round(final_month["net_worth"], 2),
                "peak_debt_ratio": round(max(point["debt_ratio"] for point in chart_data), 2),
                "risk_level": final_month["risk_level"],
                "headline": scenario_context["headline"],
            },
        }

    def _scenario_context(
        self,
        scenario: str,
        macro_score: float,
        monthly_income_drop: float,
        monthly_inflation: float,
        emi_growth: float,
        market_drawdown: float,
        horizon_months: int,
    ) -> dict[str, Any]:
        scenario_key = scenario.lower().strip()
        title = scenario.replace("-", " ").title()

        headline = "Macro stress test shows manageable pressure on cash flow."
        description = "Track savings, expenses, and EMI sensitivity each month while the scenario unfolds."

        if "war" in scenario_key:
            headline = "War escalation would raise inflation pressure and hit portfolio stability quickly."
            description = "Expect import-led inflation, higher household costs, and weaker market confidence over the next few months."
        elif "recession" in scenario_key:
            headline = "A long recession would compress income growth and drag net worth steadily lower."
            description = "Cash flow resilience becomes the main defense as income softens and markets stay under pressure."
        elif "job loss" in scenario_key:
            headline = "Temporary job loss creates an immediate liquidity shock and rapidly increases financial stress."
            description = "Savings runway matters more than returns when income disappears for several months."
        elif "interest" in scenario_key or "rate" in scenario_key:
            headline = "Rate hikes would raise EMI burden and reduce monthly surplus over time."
            description = "Debt servicing pressure compounds gradually, especially for floating-rate loans."
        elif "market crash" in scenario_key:
            headline = "A market crash would cut portfolio value first, then pressure overall net worth."
            description = "The main risk is capital drawdown, with household cash flow staying comparatively more stable."

        return {
            "title": title,
            "headline": headline,
            "description": description,
            "impact_window_months": horizon_months,
            "drivers": {
                "income_change_pct": round(-(monthly_income_drop * 100.0), 2),
                "monthly_inflation_pct": round(monthly_inflation * 100.0, 2),
                "emi_growth_pct": round(emi_growth * 100.0, 2),
                "market_drawdown_pct": round(market_drawdown * 100.0, 2),
                "macro_risk_score": round(macro_score, 2),
            },
        }

    def _scenario_recommendations(
        self,
        scenario: str,
        final_month: dict[str, Any],
        horizon_months: int,
    ) -> list[str]:
        scenario_key = scenario.lower().strip()
        actions: list[str] = []

        if "war" in scenario_key:
            actions.extend([
                "Increase emergency cash and keep at least 2 months of core expenses highly liquid",
                "Trim exposure to highly volatile equities until headline risk cools",
                "Lock essential monthly spending categories and review fuel and food inflation weekly",
            ])
        elif "recession" in scenario_key:
            actions.extend([
                "Preserve cash flow by pausing optional big-ticket spending for this stress window",
                "Build a wider income buffer and keep resume or freelance options active",
                "Prioritize debt payments that improve monthly surplus fastest",
            ])
        elif "job loss" in scenario_key:
            actions.extend([
                "Shift immediately to survival-budget mode and stop discretionary auto-debits",
                "Protect at least 4 to 6 months of essential cash runway before any investing top-ups",
                "Contact lenders early if EMI stress may emerge within the next 60 days",
            ])
        elif "interest" in scenario_key or "rate" in scenario_key:
            actions.extend([
                "Prepay high-rate debt where possible to offset rising EMI pressure",
                "Avoid new floating-rate borrowing during the rate-hike period",
                "Refinance or rebalance liabilities if your lender offers lower fixed-rate options",
            ])
        elif "market crash" in scenario_key:
            actions.extend([
                "Avoid panic-selling long-term assets during the first drawdown phase",
                "Keep fresh investments staggered instead of lump-sum deployment",
                "Separate emergency cash from market-linked holdings so liquidity stays intact",
            ])
        else:
            actions.extend([
                "Review surplus and fixed obligations every month of the scenario window",
                "Move any avoidable discretionary spend into emergency reserves",
            ])

        if float(final_month.get("debt_ratio") or 0.0) >= 40.0:
            actions.append("Reduce EMI pressure before debt ratio crosses deeper stress territory")

        if float(final_month.get("savings") or 0.0) <= 0.0:
            actions.append(f"Current plan exhausts savings within {horizon_months} months; add liquidity or cut fixed costs now")

        deduped: list[str] = []
        for item in actions:
            if item not in deduped:
                deduped.append(item)

        return deduped[:5]

    def _scenario_macro_risk_chart(
        self,
        alert: dict[str, Any],
        scenario: str,
        scenario_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        base_formula = alert.get("macro_risk_index", {}).get("formula", {})
        drivers = scenario_context.get("drivers", {})
        scenario_key = scenario.lower().strip()

        market_volatility = float(base_formula.get("market_volatility") or 40.0)
        inflation_trend = float(base_formula.get("inflation_trend") or 45.0)
        geopolitical_risk = float(base_formula.get("geopolitical_risk") or 35.0)
        economic_sentiment = float(base_formula.get("economic_sentiment") or 40.0)

        market_drawdown = float(drivers.get("market_drawdown_pct") or 0.0)
        monthly_inflation = float(drivers.get("monthly_inflation_pct") or 0.0)
        income_change = abs(float(drivers.get("income_change_pct") or 0.0))

        market_volatility += market_drawdown * 0.65
        inflation_trend += monthly_inflation * 7.0
        economic_sentiment += income_change * 1.1

        if "war" in scenario_key:
            geopolitical_risk += 14.0
            market_volatility += 8.0
        elif "recession" in scenario_key:
            economic_sentiment += 12.0
            market_volatility += 7.0
        elif "job loss" in scenario_key:
            economic_sentiment += 15.0
        elif "interest" in scenario_key or "rate" in scenario_key:
            inflation_trend += 6.0
        elif "market crash" in scenario_key:
            market_volatility += 14.0

        def clamp(value: float) -> float:
            return round(max(0.0, min(100.0, value)), 2)

        return [
            {"name": "Market Volatility", "score": clamp(market_volatility)},
            {"name": "Inflation Trend", "score": clamp(inflation_trend)},
            {"name": "Geopolitical Risk", "score": clamp(geopolitical_risk)},
            {"name": "Economic Sentiment", "score": clamp(economic_sentiment)},
        ]

    async def _load_user_financials(self, user_id: str | None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        overrides = overrides or {}
        default_income = max(1.0, float(overrides.get("income") or 50000.0))
        default_expenses = max(0.0, float(overrides.get("expenses") or default_income * 0.65))

        profile = {
            "income": default_income,
            "expenses": default_expenses,
            "savings": max(0.0, float(overrides.get("savings") or default_income * 4.0)),
            "investments": max(0.0, float(overrides.get("investments") or default_income * 6.0)),
            "loan_emi": max(0.0, float(overrides.get("loan_emi") or overrides.get("emi") or default_income * 0.2)),
            "expense_history": [],
        }

        if not user_id:
            return profile

        db = get_db()
        oid: ObjectId | None = None
        try:
            oid = ObjectId(user_id)
        except Exception:
            oid = None

        user_doc: dict[str, Any] | None = None
        if oid is not None:
            user_doc = await db["users"].find_one({"_id": oid})

        if user_doc:
            profile["income"] = max(float(user_doc.get("monthly_income") or profile["income"]), 1.0)
            profile["loan_emi"] = max(float(user_doc.get("existing_emis") or profile["loan_emi"]), 0.0)

        now = datetime.utcnow()
        six_months_ago = now - timedelta(days=180)

        total_income = 0.0
        income_count = 0
        expense_monthly: dict[str, float] = {}
        total_expenses = 0.0
        total_emi = 0.0

        user_filter = {"user_id": user_id, "date": {"$gte": six_months_ago}}

        income_cursor = db["incomes"].find(user_filter)
        async for item in income_cursor:
            total_income += float(item.get("amount") or 0.0)
            income_count += 1

        expense_cursor = db["expenses"].find(user_filter)
        async for item in expense_cursor:
            amount = float(item.get("amount") or 0.0)
            total_expenses += amount
            if str(item.get("category") or "").upper() == "EMI":
                total_emi += amount

            dt = item.get("date")
            month_key = (dt or now).strftime("%Y-%m")
            expense_monthly[month_key] = expense_monthly.get(month_key, 0.0) + amount

        months_count = max(1, len(expense_monthly))
        avg_expense = total_expenses / months_count if total_expenses > 0 else profile["expenses"]

        if income_count > 0:
            profile["income"] += total_income / max(1, months_count)

        profile["expenses"] = max(0.0, float(overrides.get("expenses") or avg_expense))
        profile["loan_emi"] = max(0.0, float(overrides.get("loan_emi") or profile["loan_emi"] or (total_emi / months_count if total_emi > 0 else 0.0)))
        profile["expense_history"] = [round(v, 2) for _, v in sorted(expense_monthly.items())][-6:]

        return profile

    def _macro_risk_chart(self, macro_impact: dict[str, Any]) -> list[dict[str, Any]]:
        c = macro_impact["components"]
        return [
            {"name": "Market Volatility", "score": round(c["market_volatility"], 2)},
            {"name": "Inflation Trend", "score": round(c["inflation_trend"], 2)},
            {"name": "Geopolitical Risk", "score": round(c["geopolitical_risk"], 2)},
            {"name": "Economic Sentiment", "score": round(c["economic_sentiment"], 2)},
        ]

    def _bucket_label(self, value: float) -> str:
        if value <= 30:
            return "Low"
        if value <= 60:
            return "Moderate"
        return "High"

    def _risk_band(self, score: float) -> str:
        if score <= 30:
            return "Low Risk"
        if score <= 60:
            return "Medium Risk"
        return "High Risk"


macro_risk_engine_service = MacroRiskEngineService()
