import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TX_FILE = DATA / "UPI_Sentinel_Dashboard_Transactions.csv"
CB_FILE = DATA / "UPI_Sentinel_Cleaned_Complaints.json"

st.set_page_config(page_title="UPI Sentinel", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

BG = "#07111c"
PANEL = "#0d1b29"
TEXT = "#eaf3ff"
MUTED = "#8fa7bd"
BLUE = "#2388ff"
GREEN = "#25d68a"
RED = "#ff5364"
ORANGE = "#f6a623"
PURPLE = "#9a72ff"
CYAN = "#22c7d9"

st.markdown(f"""
<style>
.stApp {{ background: {BG}; color: {TEXT}; }}
[data-testid="stSidebar"] {{ background: #091522; }}
[data-testid="stSidebar"] * {{ color: {TEXT}; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1600px; }}
.metric-card {{ background:{PANEL}; border:1px solid #18344a; border-radius:14px; padding:16px; min-height:105px; }}
.metric-title {{ color:{MUTED}; font-size:.82rem; }}
.metric-value {{ color:{TEXT}; font-size:1.55rem; font-weight:750; margin-top:4px; }}
.metric-sub {{ color:{MUTED}; font-size:.72rem; margin-top:5px; }}
.section-title {{ font-size:1.05rem; font-weight:700; margin: .4rem 0 .2rem; }}
.small-muted {{ color:{MUTED}; font-size:.85rem; }}
div[data-testid="stMetric"] {{ background:{PANEL}; border:1px solid #18344a; padding:12px; border-radius:12px; }}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data():
    tx = pd.read_csv(TX_FILE, low_memory=False)
    for col in ["timestamp_clean", "transaction_date"]:
        if col in tx.columns:
            tx[col] = pd.to_datetime(tx[col], errors="coerce")
    numeric_cols = [
        "amount_clean", "amount_abs", "chargeback_count", "chargeback_amount",
        "user_chargeback_count", "user_disputed_amount", "merchant_chargeback_count",
        "merchant_disputed_amount", "risk_signal_score", "reporting_delay_hours",
        "data_quality_issue_count",
    ]
    for col in numeric_cols:
        if col in tx.columns:
            tx[col] = pd.to_numeric(tx[col], errors="coerce").fillna(0)
    tx["transaction_month"] = tx["transaction_month"].astype(str)
    for col, default in {
        "merchant_category_analysis": "Unknown / Unmapped",
        "status_clean": "Unknown",
        "risk_signal_level": "Low",
        "kyc_status_clean": "Unknown",
    }.items():
        if col in tx.columns:
            tx[col] = tx[col].fillna(default)

    try:
        with open(CB_FILE, "r", encoding="utf-8") as f:
            cb_raw = json.load(f)
        cb = pd.DataFrame(cb_raw)
    except Exception:
        cb = pd.DataFrame()
    if not cb.empty:
        cb["disputed_amount"] = pd.to_numeric(cb["disputed_amount"], errors="coerce").abs()
        cb["transaction_timestamp"] = pd.to_datetime(cb["transaction_timestamp"], errors="coerce")
        cb["reported_timestamp"] = pd.to_datetime(cb["reported_timestamp"], errors="coerce")
        cb["reason_code"] = cb["reason_code"].fillna("Other / Unmapped")
        cb["severity"] = cb["severity"].fillna("Other")
    else:
        cb = pd.DataFrame(columns=["reason_code", "severity", "disputed_amount"])
    return tx, cb

tx, cb = load_data()


def base(fig, height=360):
    fig.update_layout(
        paper_bgcolor=PANEL, plot_bgcolor=PANEL,
        font={"color": TEXT, "family": "Inter, Arial"},
        margin={"l": 45, "r": 20, "t": 35, "b": 45},
        legend={"font": {"color": MUTED}}, height=height,
    )
    return fig


def metric_card(title, value, sub="", accent=BLUE):
    st.markdown(
        f'<div class="metric-card" style="border-color:{accent}55">'
        f'<div class="metric-title">{title}</div><div class="metric-value">{value}</div>'
        f'<div class="metric-sub" style="color:{accent}">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def table(df, height=360):
    st.dataframe(df, use_container_width=True, height=height, hide_index=True)


def overview():
    st.title("Executive Overview")
    st.caption("Key metrics and overall transaction health")
    total = len(tx); total_amt = tx["amount_abs"].sum(); avg = tx["amount_abs"].mean()
    failed = tx["failed_flag"].mean() * 100; pending = tx["pending_flag"].mean() * 100
    cb_count = tx["chargeback_flag"].sum(); cb_amt = tx["chargeback_amount"].sum()
    kyc_complete = tx["kyc_status_clean"].isin(["Verified", "Approved", "Complete"]).mean() * 100
    cols = st.columns(5)
    for c, args in zip(cols, [
        ("Total Transactions", f"{total:,}", "Core UPI volume", BLUE),
        ("Transaction Value", f"₹{total_amt/1e6:.2f}M", "Processed value", GREEN),
        ("Average Ticket", f"₹{avg:,.0f}", "Mean transaction size", PURPLE),
        ("Chargebacks", f"{int(cb_count):,}", f"₹{cb_amt/1e6:.2f}M disputed", RED),
        ("KYC Complete", f"{kyc_complete:.1f}%", "Verified / approved / complete", CYAN),
    ]):
        with c: metric_card(*args)

    daily = tx.dropna(subset=["transaction_date"]).groupby("transaction_date", as_index=False).agg(
        transaction_count=("txn_id_clean", "count"), amount=("amount_abs", "sum"))
    fig = go.Figure()
    fig.add_bar(x=daily["transaction_date"], y=daily["transaction_count"], name="Transactions")
    fig.add_scatter(x=daily["transaction_date"], y=daily["amount"], name="Amount", yaxis="y2", mode="lines")
    fig.update_layout(yaxis_title="Transactions", yaxis2={"title":"₹ Amount", "overlaying":"y", "side":"right"})
    st.plotly_chart(base(fig, 390), use_container_width=True, key="overview_daily")

    c1, c2, c3 = st.columns(3)
    with c1:
        status = tx["status_clean"].value_counts().reset_index(); status.columns=["status","count"]
        st.plotly_chart(base(px.pie(status, names="status", values="count", hole=.62), 330), use_container_width=True, key="status")
    with c2:
        cat = tx.groupby("merchant_category_analysis")["amount_abs"].sum().nlargest(7).sort_values().reset_index()
        st.plotly_chart(base(px.bar(cat, x="amount_abs", y="merchant_category_analysis", orientation="h"), 330), use_container_width=True, key="categories")
    with c3:
        if not cb.empty:
            reason = cb["reason_code"].value_counts().head(7).reset_index(); reason.columns=["reason","count"]
            st.plotly_chart(base(px.pie(reason, names="reason", values="count", hole=.45), 330), use_container_width=True, key="reasons")

    st.subheader("Top Merchants by Chargeback Exposure")
    top = tx.groupby("merchant_id_clean", dropna=False).agg(
        chargebacks=("chargeback_count","sum"), disputed_amount=("chargeback_amount","sum")
    ).sort_values(["chargebacks","disputed_amount"], ascending=False).head(10).reset_index()
    table(top)


def risk_page():
    st.title("Fraud & Risk")
    st.caption("Suspicious transaction signals — not proof of fraud")
    cols=st.columns(4)
    cards=[
        ("High Risk Transactions", f"{(tx['risk_signal_level']=='High').sum():,}", "Requires investigation", RED),
        ("Rapid Transactions", f"{tx['rapid_transaction_flag'].sum():,}", "Velocity signal", ORANGE),
        ("Merchant Spikes", f"{tx['merchant_spike_flag'].sum():,}", "Volume anomaly signal", PURPLE),
        ("High Value Transactions", f"{tx['high_value_flag'].sum():,}", "Amount signal", CYAN),
    ]
    for c,a in zip(cols,cards):
        with c: metric_card(*a)
    c1,c2=st.columns([1,1.4])
    with c1:
        levels=tx["risk_signal_level"].value_counts().reset_index(); levels.columns=["risk","count"]
        st.plotly_chart(base(px.bar(levels,x="risk",y="count"),360),use_container_width=True,key="risk_levels")
    with c2:
        risk_cat=tx.groupby("merchant_category_analysis").agg(transactions=("txn_id_clean","count"),risk_score=("risk_signal_score","mean"),chargebacks=("chargeback_count","sum")).reset_index().sort_values("risk_score",ascending=False).head(10)
        st.plotly_chart(base(px.bar(risk_cat,x="risk_score",y="merchant_category_analysis",orientation="h"),360),use_container_width=True,key="risk_cat")
    high=tx.groupby(["merchant_id_clean","merchant_category_analysis"]).agg(transactions=("txn_id_clean","count"),chargebacks=("chargeback_count","sum"),disputed_amount=("chargeback_amount","sum"),avg_risk=("risk_signal_score","mean")).reset_index()
    high["chargeback_ratio"]=high["chargebacks"]/high["transactions"].replace(0,np.nan)*100
    st.subheader("Priority Merchant Signals")
    table(high.sort_values(["avg_risk","chargeback_ratio"],ascending=False).head(15))


def merchant_page():
    st.title("Merchant Intelligence")
    st.caption("Merchant performance, dispute exposure and risk signals")
    m=tx.groupby(["merchant_id_clean","merchant_category_analysis"],dropna=False).agg(transactions=("txn_id_clean","count"),amount=("amount_abs","sum"),chargebacks=("chargeback_count","sum"),disputed=("chargeback_amount","sum"),risk=("risk_signal_score","mean")).reset_index()
    m["chargeback_ratio"]=m["chargebacks"]/m["transactions"].replace(0,np.nan)*100
    c1,c2=st.columns(2)
    with c1:
        top=m.nlargest(10,"amount").sort_values("amount")
        st.plotly_chart(base(px.bar(top,x="amount",y="merchant_id_clean",orientation="h"),400),use_container_width=True,key="merchant_amount")
    with c2:
        cat=m.groupby("merchant_category_analysis").agg(transactions=("transactions","sum"),chargebacks=("chargebacks","sum"),disputed=("disputed","sum")).reset_index()
        cat["ratio"]=cat["chargebacks"]/cat["transactions"].replace(0,np.nan)*100
        st.plotly_chart(base(px.bar(cat.nlargest(10,"ratio"),x="ratio",y="merchant_category_analysis",orientation="h"),400),use_container_width=True,key="merchant_ratio")
    table(m.sort_values("amount",ascending=False).head(25))


def chargeback_page():
    st.title("Disputes & Chargebacks")
    st.caption("Complaint patterns, disputed value, severity and reporting delay")
    count=len(cb); amount=cb["disputed_amount"].sum() if not cb.empty else 0
    delay=((cb["reported_timestamp"]-cb["transaction_timestamp"]).dt.total_seconds()/3600).dropna().mean() if not cb.empty else 0
    delayed=int((cb["reported_timestamp"]-cb["transaction_timestamp"]).dt.days.gt(7).sum()) if not cb.empty else 0
    cols=st.columns(4)
    for c,a in zip(cols,[
        ("Complaint Records",f"{count:,}","Chargeback / dispute events",CYAN),
        ("Disputed Amount",f"₹{amount/1e6:.2f}M","Absolute disputed value",RED),
        ("Avg Reporting Delay",f"{delay:.1f} hrs","Transaction → complaint",ORANGE),
        ("After 7 Days",f"{delayed:,}","Delayed disputes",PURPLE)]):
        with c: metric_card(*a)
    c1,c2=st.columns([1.4,1])
    if not cb.empty:
        reason=cb["reason_code"].value_counts().head(10).reset_index(); reason.columns=["reason","count"]
        sev=cb["severity"].value_counts().reset_index(); sev.columns=["severity","count"]
        with c1: st.plotly_chart(base(px.bar(reason,x="count",y="reason",orientation="h"),400),use_container_width=True,key="cb_reason")
        with c2: st.plotly_chart(base(px.pie(sev,names="severity",values="count",hole=.5),400),use_container_width=True,key="cb_sev")
    else: st.info("No complaint records available.")


def kyc_page():
    st.title("KYC Intelligence")
    st.caption("KYC status, risk segments and transaction exposure")
    kyc=tx.groupby("kyc_status_clean").agg(transactions=("txn_id_clean","count"),amount=("amount_abs","sum")).reset_index()
    risk=tx.groupby("risk_segment_clean",dropna=False)["amount_abs"].sum().reset_index()
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(base(px.bar(kyc,x="kyc_status_clean",y="transactions"),400),use_container_width=True,key="kyc_status")
    with c2: st.plotly_chart(base(px.pie(risk,names="risk_segment_clean",values="amount_abs",hole=.5),400),use_container_width=True,key="kyc_risk")
    table(kyc)


def network_page():
    st.title("Fraud Ring / Network")
    st.caption("Graph-first view of high-risk user ↔ merchant relationships")
    edges=tx.nlargest(150,"risk_signal_score")[["user_id_clean","merchant_id_clean","risk_signal_score"]].dropna()
    if edges.empty: st.info("No network edges available."); return
    users=list(edges["user_id_clean"].unique()); merchants=list(edges["merchant_id_clean"].unique()); pos={}
    for i,u in enumerate(users): pos[("u",u)]=(0,i-len(users)/2)
    for i,m in enumerate(merchants): pos[("m",m)]=(1,i-len(merchants)/2)
    fig=go.Figure()
    for _,r in edges.iterrows():
        x0,y0=pos[("u",r["user_id_clean"])]; x1,y1=pos[("m",r["merchant_id_clean"])]
        fig.add_trace(go.Scatter(x=[x0,x1],y=[y0,y1],mode="lines",line={"color":"#31556d","width":1},hoverinfo="skip",showlegend=False))
    fig.add_trace(go.Scatter(x=[pos[("u",u)][0] for u in users],y=[pos[("u",u)][1] for u in users],mode="markers+text",text=users,textposition="middle left",marker={"size":8,"color":CYAN},name="Users"))
    fig.add_trace(go.Scatter(x=[pos[("m",m)][0] for m in merchants],y=[pos[("m",m)][1] for m in merchants],mode="markers+text",text=merchants,textposition="middle right",marker={"size":11,"color":RED},name="Merchants"))
    fig.update_xaxes(showticklabels=False,range=[-.3,1.3],zeroline=False); fig.update_yaxes(showticklabels=False,zeroline=False)
    st.plotly_chart(base(fig,650),use_container_width=True,key="network")


def quality_page():
    st.title("Data Quality")
    st.caption("Cleaning health, missing values and join quality")
    cols=st.columns(4)
    for c,a in zip(cols,[
        ("Rows Analyzed",f"{len(tx):,}","Dashboard-ready transaction rows",BLUE),
        ("Needs Review",f"{(tx['data_quality_status']=='Needs Review').sum():,}","Rows requiring attention",ORANGE),
        ("Clean Rows",f"{(tx['data_quality_status']=='Clean').sum():,}","No tracked quality issue",GREEN),
        ("Invalid / Missing UTR",f"{tx['utr_missing_flag'].sum():,}","Traceability issue",RED)]):
        with c: metric_card(*a)
    quality=tx["data_quality_status"].value_counts().reset_index(); quality.columns=["status","count"]
    dq_cols=[c for c in ["amount_missing_flag","utr_missing_flag","amount_negative_flag","kyc_fk_valid_flag","merchant_fk_valid_flag"] if c in tx.columns]
    dq=pd.DataFrame({"issue":dq_cols,"count":[int(tx[c].fillna(False).astype(bool).sum()) for c in dq_cols]})
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(base(px.bar(quality,x="status",y="count"),380),use_container_width=True,key="quality_status")
    with c2: st.plotly_chart(base(px.bar(dq,x="count",y="issue",orientation="h"),380),use_container_width=True,key="quality_signals")


def agent_page():
    st.title("AgentIQ")
    st.caption("Rule-based natural-language analytics layer for common business questions")
    examples=[
        "Which merchant category has the highest chargeback-to-transaction ratio?",
        "Show the top 10 merchants by disputed amount.",
        "Which users have repeated disputes?",
        "Which categories have the highest failed transaction rate?",
        "Find high-risk merchants with transaction spikes.",
    ]
    question=st.text_input("Ask AgentIQ", placeholder="e.g. Which merchant category has the highest chargeback-to-transaction ratio?")
    if st.button("Analyze", type="primary") and question:
        q=question.lower()
        if "chargeback-to-transaction" in q or "chargeback ratio" in q:
            g=tx.groupby("merchant_category_analysis").agg(transactions=("txn_id_clean","count"),chargebacks=("chargeback_count","sum")).reset_index(); g["ratio"]=g["chargebacks"]/g["transactions"].replace(0,np.nan)*100; r=g.sort_values("ratio",ascending=False).iloc[0]
            st.success(f"Highest ratio: {r['merchant_category_analysis']} — {r['ratio']:.2f}% ({int(r['chargebacks'])} chargebacks / {int(r['transactions'])} transactions).")
        elif "top 10 merchants" in q and "disputed" in q:
            g=tx.groupby("merchant_id_clean")["chargeback_amount"].sum().nlargest(10); st.dataframe(g.rename("Disputed Amount (₹)").reset_index(),use_container_width=True,hide_index=True)
        elif "failed" in q and "categor" in q:
            g=tx.groupby("merchant_category_analysis")["failed_flag"].mean().mul(100).sort_values(ascending=False).head(5); st.dataframe(g.rename("Failed Rate (%)").reset_index(),use_container_width=True,hide_index=True)
        elif "repeated disputes" in q or "repeated" in q:
            g=tx.groupby("user_id_clean")["chargeback_count"].sum().nlargest(10); st.dataframe(g.rename("Chargeback-linked Transactions").reset_index(),use_container_width=True,hide_index=True)
        elif "risk" in q and "merchant" in q and "spike" in q:
            g=tx[tx["merchant_spike_flag"]==True].groupby("merchant_id_clean")["risk_signal_score"].mean().nlargest(10); st.dataframe(g.rename("Average Risk Signal").reset_index(),use_container_width=True,hide_index=True)
        else:
            st.info("Try one of the suggested questions below.")
    st.markdown("### Suggested Questions")
    for x in examples: st.markdown(f"- {x}")

PAGES={"⌂  Overview":overview,"⚠  Fraud & Risk":risk_page,"▣  Merchant Analytics":merchant_page,"▰  Disputes & Chargebacks":chargeback_page,"◉  KYC Intelligence":kyc_page,"✣  Fraud Network":network_page,"◫  Data Quality":quality_page,"✦  AgentIQ (AI)":agent_page}

with st.sidebar:
    st.markdown("# 🛡️ UPI SENTINEL")
    st.caption("Fraud Ring & Merchant Analytics")
    st.success("● Live Data")
    page=st.radio("Navigation",list(PAGES.keys()),label_visibility="collapsed")
    st.divider()
    st.caption('"Safer Payments"')
    st.caption('"Stronger Trust"')
    st.caption("UPI SENTINEL • v1.0")

PAGES[page]()
