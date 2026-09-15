# UPI Sentinel — Fraud Ring & Merchant Analytics

UPI Sentinel is a machine-learning and analytics platform for exploring UPI transaction behavior, suspicious risk signals, merchant exposure, disputes, KYC intelligence, data quality, and fraud-network relationships through an interactive Streamlit dashboard.

## Streamlit Deployment

This repository is configured for Streamlit Community Cloud.

### Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Deploy

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud.
3. Select **Create app**.
4. Choose this GitHub repository and the `main` branch.
5. Set the entrypoint to `streamlit_app.py`.
6. Click **Deploy**.

The application keeps its data files inside `data/`, so the CSV and JSON datasets must be committed to the repository for the deployed dashboard to load correctly.

## Dashboard Modules

- Executive Overview
- Fraud & Risk
- Merchant Intelligence
- Disputes & Chargebacks
- KYC Intelligence
- Fraud Ring / Network
- Data Quality
- AgentIQ

> Risk signals are investigative indicators and should not be interpreted as proof of fraud.

## Developers

**Pritish Kumar** — Lead Developer & Primary Contributor  
**Utkarsh Sengar** — ML & Development Contributor  
**Sarthak Pandey** — Development & Analysis Contributor  
**Navneet Pandey** — Project & Analysis Contributor
