# Option Dashboard

A production-oriented Streamlit dashboard for Zerodha option sellers monitoring manually placed **0 DTE Short Straddles**.

## Features

- Zerodha Kite Connect login status and live position reading.
- Automatic short straddle detection from open short CE and PE positions.
- Live combined premium, MTM, profit percentage, ROI, premium decay, and holding timer.
- Profit target cards for 30%, 50%, 60%, and 70% premium decay.
- Stop-loss cards for 10%, 15%, 20%, and 25% premium expansion.
- One-shot success alerts for targets and continuous alarm for stop loss until dismissed.
- Alert WAV files are generated locally at runtime to avoid committing binary assets.
- Append-only CSV journal for completed/manual exits.
- Clean module boundaries for future Telegram, WhatsApp, auto-exit, and multi-strategy support.

## Folder Structure

```text
option_dashboard/
├── app.py
├── kite_api.py
├── monitor.py
├── calculations.py
├── journal.py
├── config.py
├── requirements.txt
├── trades.csv
├── assets/
│   ├── README.md
│   ├── success.wav  # runtime-generated, git-ignored
│   └── alarm.wav    # runtime-generated, git-ignored
└── README.md
```

## Installation

```bash
cd option_dashboard
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API Setup

Create `option_dashboard/.env`:

```env
API_KEY=your_kite_api_key
API_SECRET=your_kite_api_secret
ACCESS_TOKEN=your_daily_access_token
REFRESH_INTERVAL=2
```

Kite access tokens are session-scoped. Generate and update `ACCESS_TOKEN` before market monitoring each day.

## Running

```bash
streamlit run app.py
```

The trader should place the straddle manually in Zerodha. The dashboard reads open positions and detects a CE/PE short pair with the same underlying, expiry, and strike.

## Screenshots

Add screenshots here after deploying or running locally:

- Main dashboard placeholder
- Target cards placeholder
- Stop-loss alert placeholder

## Future Enhancements

- SQLite persistence for trades and intraday premium history.
- Telegram and WhatsApp alerts.
- Optional guarded auto-exit order placement.
- Multiple simultaneous strategies.
- Iron Condor, Strangle, and Calendar Spread monitors.
- Broker abstraction beyond Zerodha.
