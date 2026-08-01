# AI Powered 0DTE Short Straddle Monitor

A modular Streamlit trading workstation for Indian index option sellers. The app keeps the original Zerodha short-straddle monitoring workflow and adds a complete pre-trade risk gate, market-regime engine, strategy selector, Greeks, analytics, backtesting, broker abstraction, and professional dashboard panels.

## Key Capabilities

- **Priority #1 No Trade Filter**: RBI policy, budget day, global events, India VIX level/spike, gap, opening range, ADX, VWAP distance, circuit day, IV, liquidity, expiry overlap, and exchange-issue filters.
- **Pre-Trade Checklist**: 12 checks with pass count such as `10/12`.
- **Trade Quality Score**: 0-100 weighted score across VWAP, opening range, VIX, IV, OI, PCR, news, time, liquidity, and premium decay.
- **Market Regime Detection**: SIDEWAYS, TRENDING, VOLATILE, EXPANSION, MEAN REVERSION, or NO TRADE using VWAP, ATR, ADX, SuperTrend state, EMAs, breadth, and opening range.
- **Auto Strategy Engine**: ATM short straddle, OTM1 short strangle, iron condor, wide iron condor, or skip-trade recommendation.
- **Auto Strike Selection**: ATM/OTM strikes, expected premium, theta, POP, and recommended call/put strikes.
- **Greeks Panel**: Delta, gamma, theta, vega, IV, IV rank, IV percentile, bid/ask, OI, and volume.
- **Risk Engine**: Capital, margin, max risk, combined premium, 30/40/50/60 stop levels, target, expected return, risk/reward, and probability of profit.
- **Live Monitor**: Large P&L, current premium, remaining risk, IV, risk/trend gauges, and heat map.
- **AI Trade Assistant**: Natural-language assessment of regime, VWAP, IV stability, premium decay, score, strategy, and confidence.
- **Exit Engine**: Combined SL, target, VWAP break, ADX rise, IV spike, time exit, trend reversal, and premium expansion reasons.
- **Journal + Analytics**: CSV trade records, screenshot placeholder, trade score, strategy, market type, P&L, mistakes, learning notes, win rate, expectancy, Sharpe, drawdown, profit factor, timing stats, monthly/yearly reports.
- **Backtest Engine**: Deterministic research stub for 30/90/180/365 day windows with CAGR, win rate, drawdown, and profit factor.
- **Broker Architecture**: `Broker` interface plus `DummyBroker`, ready for Zerodha, Dhan, Fyers, and Angel adapters.

## Project Structure

```text
option_dashboard/
├── analytics.py
├── app.py
├── broker.py
├── calculations.py
├── config.py
├── dashboard.py
├── greeks.py
├── indicators.py
├── journal.py
├── kite_api.py
├── main.py
├── market.py
├── monitor.py
├── risk.py
├── signals.py
├── sound_assets.py
├── storage.py
├── strategy.py
├── utils.py
├── requirements.txt
└── assets/
```

## Running

```bash
cd option_dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

The system runs in demo/paper mode without credentials. To enable Zerodha status checks, create `option_dashboard/.env` with `API_KEY`, `API_SECRET`, and daily `ACCESS_TOKEN`.
