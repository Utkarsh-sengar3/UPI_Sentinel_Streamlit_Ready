
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TX_FILE = DATA / "UPI_Sentinel_Dashboard_Transactions.csv"
CB_FILE = DATA / "UPI_Sentinel_Cleaned_Complaints.json"

app = Dash(__name__)
app.title = "UPI Sentinel"

# -----------------------------
# Load data
# -----------------------------
tx = pd.read_csv(TX_FILE, low_memory=False)

for col in ["timestamp_clean", "transaction_date"]:
    if col in tx.columns:
        tx[col] = pd.to_datetime(tx[col], errors="coerce")

numeric_cols = [
    "amount_clean", "amount_abs", "chargeback_count", "chargeback_amount",
    "user_chargeback_count", "user_disputed_amount",
    "merchant_chargeback_count", "merchant_disputed_amount",
    "risk_signal_score", "reporting_delay_hours",
    "data_quality_issue_count"
]
for col in numeric_cols:
    if col in tx.columns:
        tx[col] = pd.to_numeric(tx[col], errors="coerce").fillna(0)

tx["transaction_month"] = tx["transaction_month"].astype(str)
tx["merchant_category_analysis"] = tx["merchant_category_analysis"].fillna("Unknown / Unmapped")
tx["status_clean"] = tx["status_clean"].fillna("Unknown")
tx["risk_signal_level"] = tx["risk_signal_level"].fillna("Low")
tx["kyc_status_clean"] = tx["kyc_status_clean"].fillna("Unknown")

try:
    with open(CB_FILE, "r", encoding="utf-8") as f:
        cb_raw = json.load(f)
    cb = pd.DataFrame(cb_raw)
except Exception:
    cb = pd.DataFrame()

if not cb.empty:
    cb["disputed_amount"] = pd.to_numeric(
        cb["disputed_amount"], errors="coerce"
    ).abs()
    cb["transaction_timestamp"] = pd.to_datetime(
        cb["transaction_timestamp"], errors="coerce"
    )
    cb["reported_timestamp"] = pd.to_datetime(
        cb["reported_timestamp"], errors="coerce"
    )
    cb["reason_code"] = cb["reason_code"].fillna("Other / Unmapped")
    cb["severity"] = cb["severity"].fillna("Other")
else:
    cb = pd.DataFrame(columns=["reason_code", "severity", "disputed_amount"])

# -----------------------------
# Styling helpers
# -----------------------------
BG = "#07111c"
PANEL = "#0d1b29"
PANEL2 = "#102335"
TEXT = "#eaf3ff"
MUTED = "#8fa7bd"
BLUE = "#2388ff"
GREEN = "#25d68a"
RED = "#ff5364"
ORANGE = "#f6a623"
PURPLE = "#9a72ff"
CYAN = "#22c7d9"

def card(title, value, sub="", accent=BLUE):
    return html.Div(
        [
            html.Div(title, style={"color": MUTED, "fontSize": "13px"}),
            html.Div(value, style={"color": TEXT, "fontSize": "25px", "fontWeight": "700", "marginTop": "5px"}),
            html.Div(sub, style={"color": accent, "fontSize": "11px", "marginTop": "6px"}),
        ],
        style={
            "background": PANEL,
            "border": f"1px solid {accent}55",
            "borderRadius": "12px",
            "padding": "15px",
            "boxShadow": "0 8px 24px rgba(0,0,0,.18)",
        },
    )

def panel(title, children):
    return html.Div(
        [
            html.Div(title, style={"fontWeight": "700", "fontSize": "16px", "marginBottom": "10px"}),
            children,
        ],
        style={
            "background": PANEL,
            "border": "1px solid #18344a",
            "borderRadius": "12px",
            "padding": "14px",
            "height": "100%",
        },
    )

def fig_base(fig):
    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font={"color": TEXT, "family": "Inter, Arial"},
        margin={"l": 45, "r": 20, "t": 25, "b": 40},
        legend={"font": {"color": MUTED}},
    )
    return fig

# -----------------------------
# Sidebar
# -----------------------------
menu_items = [
    ("overview", "⌂  Overview"),
    ("risk", "⚠  Fraud & Risk"),
    ("merchant", "▣  Merchant Analytics"),
    ("chargeback", "▰  Disputes & Chargebacks"),
    ("kyc", "◉  KYC Intelligence"),
    ("network", "✣  Fraud Network"),
    ("quality", "◫  Data Quality"),
    ("agent", "✦  AgentIQ (AI)"),
]

sidebar = html.Div(
    [
        html.Div("UPI SENTINEL", style={"fontSize": "24px", "fontWeight": "800", "color": BLUE}),
        html.Div("Fraud Ring & Merchant Analytics", style={"color": MUTED, "fontSize": "11px", "marginBottom": "25px"}),
        *[
            html.Button(
                label,
                id=f"nav-{key}",
                n_clicks=0,
                style={
                    "width": "100%",
                    "textAlign": "left",
                    "background": "transparent",
                    "color": TEXT,
                    "border": "0",
                    "padding": "12px 10px",
                    "borderRadius": "8px",
                    "marginBottom": "4px",
                    "cursor": "pointer",
                    "fontSize": "13px",
                },
            )
            for key, label in menu_items
        ],
        html.Div(
            [
                html.Div('"Safer Payments"', style={"color": MUTED, "fontStyle": "italic"}),
                html.Div('"Stronger Trust"', style={"color": MUTED, "fontStyle": "italic"}),
                html.Div("UPI SENTINEL • v1.0", style={"color": "#577187", "fontSize": "10px", "marginTop": "35px"}),
            ],
            style={"position": "absolute", "bottom": "25px", "left": "20px"},
        ),
    ],
    style={
        "width": "205px",
        "minHeight": "100vh",
        "background": "#091522",
        "padding": "25px 14px",
        "boxSizing": "border-box",
        "position": "fixed",
        "left": 0,
        "top": 0,
    },
)

# -----------------------------
# Header
# -----------------------------
header = html.Div(
    [
        html.Div(
            [
                html.Div("UPI SENTINEL", style={"fontSize": "29px", "fontWeight": "800", "color": BLUE}),
                html.Div("Fraud Ring & Merchant Analytics", style={"color": MUTED, "fontSize": "13px"}),
            ]
        ),
        html.Div(
            [
                html.Span("● Live Data", style={"color": GREEN, "marginRight": "25px", "fontSize": "13px"}),
                html.Span("AgentIQ", style={"color": MUTED, "fontSize": "13px"}),
            ]
        ),
    ],
    style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "18px 25px",
        "borderBottom": "1px solid #173044",
        "background": "#091522",
    },
)

# -----------------------------
# Pages
# -----------------------------
def overview_page():
    total = len(tx)
    total_amt = tx["amount_abs"].sum()
    avg = tx["amount_abs"].mean()
    failed = tx["failed_flag"].mean() * 100
    pending = tx["pending_flag"].mean() * 100
    cb_count = tx["chargeback_flag"].sum()
    cb_amt = tx["chargeback_amount"].sum()
    ratio = (cb_count / total * 100) if total else 0
    kyc_complete = tx["kyc_status_clean"].isin(["Verified", "Approved", "Complete"]).mean() * 100

    daily = (
        tx.dropna(subset=["transaction_date"])
        .groupby("transaction_date", as_index=False)
        .agg(transaction_count=("txn_id_clean", "count"), amount=("amount_abs", "sum"))
    )
    fig_daily = go.Figure()
    fig_daily.add_bar(x=daily["transaction_date"], y=daily["transaction_count"], name="Transaction Count")
    fig_daily.add_scatter(
        x=daily["transaction_date"], y=daily["amount"], name="Transaction Amount",
        yaxis="y2", mode="lines"
    )
    fig_daily.update_layout(
        yaxis={"title": "Transactions"},
        yaxis2={"title": "₹ Amount", "overlaying": "y", "side": "right"},
    )
    fig_base(fig_daily)

    status = tx["status_clean"].value_counts().reset_index()
    status.columns = ["status", "count"]
    fig_status = px.pie(status, names="status", values="count", hole=.62)
    fig_base(fig_status)

    cat = (
        tx.groupby("merchant_category_analysis", dropna=False)["amount_abs"]
        .sum().nlargest(7).sort_values()
        .reset_index()
    )
    fig_cat = px.bar(cat, x="amount_abs", y="merchant_category_analysis", orientation="h")
    fig_cat.update_layout(xaxis_title="Transaction Amount (₹)", yaxis_title="")
    fig_base(fig_cat)

    if not cb.empty:
        reason = cb["reason_code"].value_counts().reset_index()
        reason.columns = ["reason", "count"]
        reason = reason.head(7)
        fig_reason = px.pie(reason, names="reason", values="count", hole=.45)
        fig_base(fig_reason)
    else:
        fig_reason = fig_status

    top_merchants = (
        tx.groupby("merchant_id_clean", dropna=False)
        .agg(chargebacks=("chargeback_count", "sum"), amount=("chargeback_amount", "sum"))
        .sort_values(["chargebacks", "amount"], ascending=False)
        .head(10).reset_index()
    )
    top_merchants["amount"] = top_merchants["amount"].round(2)
    table = html.Table(
        [
            html.Thead(html.Tr([html.Th("#"), html.Th("Merchant"), html.Th("Chargebacks"), html.Th("Amount (₹)")])),

            html.Tbody([
                html.Tr([html.Td(i+1), html.Td(r["merchant_id_clean"]), html.Td(int(r["chargebacks"])), html.Td(f"{r['amount']:,.2f}")])
                for i, (_, r) in enumerate(top_merchants.iterrows())
            ])
        ],
        style={"width": "100%", "fontSize": "12px", "color": TEXT},
    )

    return [
        html.H1("Executive Overview", style={"marginBottom": "3px"}),
        html.Div("Key metrics and overall transaction health", style={"color": MUTED, "marginBottom": "15px"}),
        html.Div(
            [
                card("Total Transactions", f"{total:,}", "Core UPI volume", BLUE),
                card("Total Transaction Amount", f"₹{total_amt/1e6:.2f}M", "Processed value", GREEN),
                card("Average Transaction Value", f"₹{avg:,.0f}", "Mean ticket size", PURPLE),
                card("Failed Transaction Rate", f"{failed:.1f}%", "Operational risk", RED),
                card("Pending Transaction Rate", f"{pending:.1f}%", "Pending queue", ORANGE),
                card("Chargeback Count", f"{int(cb_count):,}", "Dispute-linked transactions", CYAN),
                card("Chargeback Amount", f"₹{cb_amt/1e6:.2f}M", "Disputed value", RED),
                card("Chargeback-to-Txn Ratio", f"{ratio:.2f}%", "Core risk metric", ORANGE),
                card("KYC Completion", f"{kyc_complete:.1f}%", "Verified / approved users", GREEN),
            ],
            style={"display": "grid", "gridTemplateColumns": "repeat(5, 1fr)", "gap": "10px", "marginBottom": "12px"},
        ),
        html.Div(
            [
                panel("Daily Transaction Volume & Value", dcc.Graph(figure=fig_daily, config={"displayModeBar": False})),
                panel("Transaction Status Distribution", dcc.Graph(figure=fig_status, config={"displayModeBar": False})),
            ],
            style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "12px", "marginBottom": "12px"},
        ),
        html.Div(
            [
                panel("Top Merchant Categories by Transaction Amount", dcc.Graph(figure=fig_cat, config={"displayModeBar": False})),
                panel("Chargeback Reason Distribution", dcc.Graph(figure=fig_reason, config={"displayModeBar": False})),
                panel("Top Merchants by Chargeback Count", table),
            ],
            style={"display": "grid", "gridTemplateColumns": "1.25fr 1fr 1.15fr", "gap": "12px"},
        ),
    ]

def risk_page():
    risky = tx[tx["risk_signal_score"] > 0].copy()
    levels = tx["risk_signal_level"].value_counts().reset_index()
    levels.columns = ["risk", "count"]
    fig_level = px.bar(levels, x="risk", y="count")
    fig_base(fig_level)

    risk_cat = (
        tx.groupby("merchant_category_analysis")
        .agg(
            transactions=("txn_id_clean", "count"),
            risk_score=("risk_signal_score", "mean"),
            chargebacks=("chargeback_count", "sum")
        ).reset_index()
        .sort_values("risk_score", ascending=False).head(10)
    )
    fig_cat = px.bar(risk_cat, x="risk_score", y="merchant_category_analysis", orientation="h")
    fig_base(fig_cat)

    high = (
        tx.groupby(["merchant_id_clean", "merchant_category_analysis"])
        .agg(
            transactions=("txn_id_clean", "count"),
            chargebacks=("chargeback_count", "sum"),
            disputed_amount=("chargeback_amount", "sum"),
            avg_risk=("risk_signal_score", "mean")
        ).reset_index()
    )
    high["chargeback_ratio"] = high["chargebacks"] / high["transactions"].replace(0, np.nan) * 100
    high = high.sort_values(["avg_risk", "chargeback_ratio"], ascending=False).head(15)

    return [
        html.H1("Fraud & Risk", style={"marginBottom": "3px"}),
        html.Div("Suspicious transaction signals — not proof of fraud", style={"color": MUTED, "marginBottom": "15px"}),
        html.Div(
            [
                card("High Risk Transactions", f"{(tx['risk_signal_level']=='High').sum():,}", "Requires investigation", RED),
                card("Rapid Transactions", f"{tx['rapid_transaction_flag'].sum():,}", "Velocity signal", ORANGE),
                card("Merchant Spikes", f"{tx['merchant_spike_flag'].sum():,}", "Volume anomaly signal", PURPLE),
                card("High Value Transactions", f"{tx['high_value_flag'].sum():,}", "Amount signal", CYAN),
            ],
            style={"display": "grid", "gridTemplateColumns": "repeat(4,1fr)", "gap": "10px", "marginBottom": "12px"},
        ),
        html.Div(
            [
                panel("Risk Level Distribution", dcc.Graph(figure=fig_level, config={"displayModeBar": False})),
                panel("Highest-Risk Categories", dcc.Graph(figure=fig_cat, config={"displayModeBar": False})),
            ],
            style={"display": "grid", "gridTemplateColumns": "1fr 1.4fr", "gap": "12px", "marginBottom": "12px"},
        ),
        panel(
            "Priority Merchant Signals",
            html.Table(
                [html.Thead(html.Tr([html.Th(c) for c in ["Merchant", "Category", "Transactions", "Chargebacks", "Disputed ₹", "Avg Risk"]]))] +
                [html.Tbody([
                    html.Tr([
                        html.Td(r["merchant_id_clean"]),
                        html.Td(r["merchant_category_analysis"]),
                        html.Td(int(r["transactions"])),
                        html.Td(int(r["chargebacks"])),
                        html.Td(f"{r['disputed_amount']:,.0f}"),
                        html.Td(f"{r['avg_risk']:.1f}")
                    ]) for _, r in high.iterrows()
                ])],
                style={"width": "100%", "fontSize": "12px", "color": TEXT}
            )
        )
    ]

def merchant_page():
    m = (
        tx.groupby(["merchant_id_clean", "merchant_category_analysis"], dropna=False)
        .agg(
            transactions=("txn_id_clean", "count"),
            amount=("amount_abs", "sum"),
            chargebacks=("chargeback_count", "sum"),
            disputed=("chargeback_amount", "sum"),
            risk=("risk_signal_score", "mean")
        ).reset_index()
    )
    m["chargeback_ratio"] = m["chargebacks"] / m["transactions"].replace(0, np.nan) * 100
    top = m.nlargest(10, "amount").sort_values("amount")
    fig_amount = px.bar(top, x="amount", y="merchant_id_clean", orientation="h")
    fig_base(fig_amount)

    cat = (
        m.groupby("merchant_category_analysis")
        .agg(transactions=("transactions","sum"), chargebacks=("chargebacks","sum"), disputed=("disputed","sum"))
        .reset_index()
    )
    cat["ratio"] = cat["chargebacks"] / cat["transactions"].replace(0, np.nan) * 100
    fig_ratio = px.bar(cat.nlargest(10, "ratio"), x="ratio", y="merchant_category_analysis", orientation="h")
    fig_ratio.update_layout(xaxis_title="Chargeback / Transaction (%)", yaxis_title="")
    fig_base(fig_ratio)

    return [
        html.H1("Merchant Intelligence"),
        html.Div("Merchant performance, dispute exposure and risk signals", style={"color": MUTED, "marginBottom": "15px"}),
        html.Div(
            [
                panel("Top Merchants by Transaction Amount", dcc.Graph(figure=fig_amount, config={"displayModeBar": False})),
                panel("Highest Chargeback-to-Transaction Categories", dcc.Graph(figure=fig_ratio, config={"displayModeBar": False})),
            ],
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
        ),
    ]

def chargeback_page():
    count = len(cb)
    amount = cb["disputed_amount"].sum() if not cb.empty else 0
    delay = (
        (cb["reported_timestamp"] - cb["transaction_timestamp"]).dt.total_seconds()/3600
    ).dropna().mean() if not cb.empty else 0

    if not cb.empty:
        reason = cb["reason_code"].value_counts().reset_index()
        reason.columns = ["reason", "count"]
        fig_reason = px.bar(reason.head(10), x="count", y="reason", orientation="h")
        fig_base(fig_reason)

        sev = cb["severity"].value_counts().reset_index()
        sev.columns = ["severity", "count"]
        fig_sev = px.pie(sev, names="severity", values="count", hole=.5)
        fig_base(fig_sev)
    else:
        fig_reason = go.Figure()
        fig_sev = go.Figure()

    return [
        html.H1("Disputes & Chargebacks"),
        html.Div("Complaint patterns, disputed value, severity and reporting delay", style={"color": MUTED, "marginBottom": "15px"}),
        html.Div(
            [
                card("Complaint Records", f"{count:,}", "Chargeback / dispute events", CYAN),
                card("Disputed Amount", f"₹{amount/1e6:.2f}M", "Absolute disputed value", RED),
                card("Avg Reporting Delay", f"{delay:.1f} hrs", "Transaction → complaint", ORANGE),
                card("After 7 Days", f"{int((cb['reported_timestamp']-cb['transaction_timestamp']).dt.days.gt(7).sum()) if not cb.empty else 0:,}", "Delayed disputes", PURPLE),
            ],
            style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"10px","marginBottom":"12px"}
        ),
        html.Div(
            [
                panel("Chargeback Reasons", dcc.Graph(figure=fig_reason, config={"displayModeBar": False})),
                panel("Severity Distribution", dcc.Graph(figure=fig_sev, config={"displayModeBar": False})),
            ],
            style={"display":"grid","gridTemplateColumns":"1.4fr 1fr","gap":"12px"},
        ),
    ]

def kyc_page():
    kyc = tx.groupby("kyc_status_clean").agg(
        transactions=("txn_id_clean","count"),
        amount=("amount_abs","sum")
    ).reset_index()
    fig = px.bar(kyc, x="kyc_status_clean", y="transactions")
    fig_base(fig)

    risk = tx.groupby("risk_segment_clean", dropna=False)["amount_abs"].sum().reset_index()
    fig2 = px.pie(risk, names="risk_segment_clean", values="amount_abs", hole=.5)
    fig_base(fig2)

    return [
        html.H1("KYC Intelligence"),
        html.Div("KYC status, risk segments and transaction exposure", style={"color": MUTED, "marginBottom": "15px"}),
        html.Div(
            [
                panel("Transactions by KYC Status", dcc.Graph(figure=fig, config={"displayModeBar": False})),
                panel("Transaction Value by Risk Segment", dcc.Graph(figure=fig2, config={"displayModeBar": False})),
            ],
            style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"12px"},
        )
    ]

def network_page():
    # Lightweight user→merchant network built from the highest-risk rows.
    edges = (
        tx.nlargest(150, "risk_signal_score")[["user_id_clean","merchant_id_clean","risk_signal_score"]]
        .dropna()
    )
    if edges.empty:
        return [html.H1("Fraud Network"), html.Div("No network edges available.", style={"color": MUTED})]

    users = list(edges["user_id_clean"].unique())
    merchants = list(edges["merchant_id_clean"].unique())
    pos = {}
    for i, u in enumerate(users):
        pos[("u",u)] = (0, i - len(users)/2)
    for i, m in enumerate(merchants):
        pos[("m",m)] = (1, i - len(merchants)/2)

    fig = go.Figure()
    for _, r in edges.iterrows():
        x0,y0 = pos[("u",r["user_id_clean"])]
        x1,y1 = pos[("m",r["merchant_id_clean"])]
        fig.add_trace(go.Scatter(x=[x0,x1], y=[y0,y1], mode="lines", line={"color":"#31556d","width":1}, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[pos[("u",u)][0] for u in users], y=[pos[("u",u)][1] for u in users],
        mode="markers+text", text=users, textposition="middle left",
        marker={"size":8,"color":CYAN}, name="Users"
    ))
    fig.add_trace(go.Scatter(
        x=[pos[("m",m)][0] for m in merchants], y=[pos[("m",m)][1] for m in merchants],
        mode="markers+text", text=merchants, textposition="middle right",
        marker={"size":11,"color":RED}, name="Merchants"
    ))
    fig.update_xaxes(showticklabels=False, range=[-.3,1.3], zeroline=False)
    fig.update_yaxes(showticklabels=False, zeroline=False)
    fig_base(fig)

    return [
        html.H1("Fraud Ring / Network"),
        html.Div("Graph-first view of high-risk user ↔ merchant relationships", style={"color": MUTED, "marginBottom": "15px"}),
        panel("Suspicious Relationship Network", dcc.Graph(figure=fig, style={"height":"650px"}, config={"displayModeBar": False})),
    ]

def quality_page():
    quality = tx["data_quality_status"].value_counts().reset_index()
    quality.columns = ["status","count"]
    fig = px.bar(quality, x="status", y="count")
    fig_base(fig)

    dq_cols = [c for c in ["amount_missing_flag","utr_missing_flag","amount_negative_flag","kyc_fk_valid_flag","merchant_fk_valid_flag"] if c in tx.columns]
    dq = pd.DataFrame({"issue": dq_cols, "count": [int(tx[c].eq(True).sum()) if tx[c].dtype == bool else int(tx[c].fillna(False).astype(bool).sum()) for c in dq_cols]})
    fig2 = px.bar(dq, x="count", y="issue", orientation="h")
    fig_base(fig2)

    return [
        html.H1("Data Quality"),
        html.Div("Cleaning health, missing values and join quality", style={"color": MUTED, "marginBottom": "15px"}),
        html.Div(
            [
                card("Rows Analyzed", f"{len(tx):,}", "Dashboard-ready transaction rows", BLUE),
                card("Needs Review", f"{(tx['data_quality_status']=='Needs Review').sum():,}", "Rows requiring attention", ORANGE),
                card("Clean Rows", f"{(tx['data_quality_status']=='Clean').sum():,}", "No tracked quality issue", GREEN),
                card("Invalid / Missing UTR", f"{tx['utr_missing_flag'].sum():,}", "Traceability issue", RED),
            ],
            style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"10px","marginBottom":"12px"}
        ),
        html.Div(
            [
                panel("Data Quality Status", dcc.Graph(figure=fig, config={"displayModeBar": False})),
                panel("Key Quality Signals", dcc.Graph(figure=fig2, config={"displayModeBar": False})),
            ],
            style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"12px"},
        ),
    ]

def agent_page():
    examples = [
        "Which merchant category has the highest chargeback-to-transaction ratio?",
        "Show the top 10 merchants by disputed amount.",
        "Which users have repeated disputes?",
        "Which categories have the highest failed transaction rate?",
        "Find high-risk merchants with transaction spikes.",
    ]
    return [
        html.H1("AgentIQ"),
        html.Div("Natural-language analytics layer for business questions", style={"color": MUTED, "marginBottom": "15px"}),
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Ask AgentIQ", style={"fontWeight":"700","fontSize":"18px","marginBottom":"10px"}),
                        dcc.Input(
                            id="agent-input",
                            placeholder="e.g. Which merchant category has the highest chargeback-to-transaction ratio?",
                            style={"width":"100%","padding":"13px","background":"#081522","color":TEXT,"border":"1px solid #24455d","borderRadius":"8px"}
                        ),
                        html.Button("Analyze", id="agent-btn", n_clicks=0, style={"marginTop":"10px","padding":"10px 18px","background":BLUE,"color":"white","border":"0","borderRadius":"7px"}),
                        html.Div(id="agent-output", style={"marginTop":"18px","color":TEXT,"lineHeight":"1.6"}),
                    ],
                    style={"background":PANEL,"padding":"20px","borderRadius":"12px","border":"1px solid #18344a"}
                ),
                panel("Suggested Questions", html.Ul([html.Li(x, style={"marginBottom":"9px"}) for x in examples])),
            ],
            style={"display":"grid","gridTemplateColumns":"2fr 1fr","gap":"12px"}
        )
    ]

pages = {
    "overview": overview_page,
    "risk": risk_page,
    "merchant": merchant_page,
    "chargeback": chargeback_page,
    "kyc": kyc_page,
    "network": network_page,
    "quality": quality_page,
    "agent": agent_page,
}

app.layout = html.Div(
    [
        sidebar,
        html.Div(
            [
                header,
                html.Div(id="page-content", style={"padding":"25px","maxWidth":"1600px","margin":"0 auto"}),
            ],
            style={"marginLeft":"205px","minHeight":"100vh","background":BG},
        ),
    ],
    style={"background":BG,"color":TEXT,"fontFamily":"Inter, Arial, sans-serif","minHeight":"100vh"},
)

@app.callback(
    Output("page-content", "children"),
    [Input(f"nav-{key}", "n_clicks") for key, _ in menu_items],
)
def route(*clicks):
    index = 0
    if any(clicks):
        index = max(range(len(clicks)), key=lambda i: clicks[i] or 0)
    return pages[menu_items[index][0]]()

@app.callback(
    Output("agent-output", "children"),
    Input("agent-btn", "n_clicks"),
    Input("agent-input", "value"),
    prevent_initial_call=True,
)
def agent_answer(n_clicks, question):
    q = (question or "").lower()

    if "chargeback-to-transaction" in q or "chargeback ratio" in q:
        g = tx.groupby("merchant_category_analysis").agg(
            transactions=("txn_id_clean","count"),
            chargebacks=("chargeback_count","sum")
        ).reset_index()
        g["ratio"] = g["chargebacks"] / g["transactions"].replace(0,np.nan) * 100
        r = g.sort_values("ratio", ascending=False).iloc[0]
        return html.Div([
            html.B("AgentIQ Result"),
            html.Br(),
            f"The highest chargeback-to-transaction ratio is for {r['merchant_category_analysis']}: ",
            html.B(f"{r['ratio']:.2f}%"),
            f" ({int(r['chargebacks'])} chargebacks across {int(r['transactions'])} transactions)."
        ])

    if "top 10 merchants" in q and "disputed" in q:
        g = tx.groupby("merchant_id_clean")["chargeback_amount"].sum().nlargest(10)
        return html.Div([
            html.B("Top 10 merchants by disputed amount"),
            html.Ol([html.Li(f"{idx}: ₹{val:,.2f}") for idx,val in g.items()])
        ])

    if "failed" in q and "categor" in q:
        g = tx.groupby("merchant_category_analysis")["failed_flag"].mean().mul(100).sort_values(ascending=False).head(5)
        return html.Div([
            html.B("Highest failed transaction rates"),
            html.Ol([html.Li(f"{idx}: {val:.2f}%") for idx,val in g.items()])
        ])

    if "repeated disputes" in q or "repeated" in q:
        g = tx.groupby("user_id_clean")["chargeback_count"].sum().nlargest(10)
        return html.Div([
            html.B("Users with repeated dispute-linked transactions"),
            html.Ol([html.Li(f"{idx}: {int(val)} chargeback-linked transactions") for idx,val in g.items()])
        ])

    if "risk" in q and "merchant" in q and "spike" in q:
        g = tx[tx["merchant_spike_flag"] == True].groupby("merchant_id_clean")["risk_signal_score"].mean().nlargest(10)
        return html.Div([
            html.B("High-risk merchants with transaction spikes"),
            html.Ol([html.Li(f"{idx}: average risk signal {val:.1f}") for idx,val in g.items()])
        ])

    return html.Div([
        html.B("AgentIQ"),
        html.Br(),
        "I can answer the suggested dashboard questions. Try the exact wording shown on the right."
    ])

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
