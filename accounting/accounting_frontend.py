import streamlit as st
import pandas as pd
#import mysql.connector
import time

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Accounting System", layout="wide")

# -------------------------------
# DB CONNECTION (REUSE YOUR CONFIG IF EXISTS)
# -------------------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="yourpassword",
        database="invoice_db"
    )

# -------------------------------
# FETCH DATA
# -------------------------------
def fetch_invoices():
    conn = get_connection()
    query = "SELECT * FROM invoices ORDER BY created_at DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# -------------------------------
# LEDGER GENERATION
# -------------------------------
def generate_ledger(df):
    ledger_entries = []
    for _, row in df.iterrows():
        entry = {
            "Date": row["invoice_date"],
            "Debit": "Purchase Account",
            "Credit": row["vendor_name"],
            "Amount": row["amount"]
        }
        ledger_entries.append(entry)
    return pd.DataFrame(ledger_entries)

# -------------------------------
# UI HEADER
# -------------------------------
st.title("📊 AI Accounting Dashboard")
st.markdown("Auto-synced invoice data → Accounting system")

# -------------------------------
# REFRESH BUTTON
# -------------------------------
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🔄 Refresh"):
        st.rerun()

# -------------------------------
# LOAD DATA
# -------------------------------
df = fetch_invoices()

# -------------------------------
# METRICS
# -------------------------------
total_invoices = len(df)
total_amount = df["amount"].sum() if not df.empty else 0
total_gst = df["gst"].sum() if not df.empty else 0

col1, col2, col3 = st.columns(3)

col1.metric("Total Invoices", total_invoices)
col2.metric("Total Amount (₹)", f"{total_amount:,.2f}")
col3.metric("Total GST (₹)", f"{total_gst:,.2f}")

st.divider()

# -------------------------------
# INVOICE TABLE
# -------------------------------
st.subheader("📄 Invoice Records")

if df.empty:
    st.warning("No invoices found.")
else:
    st.dataframe(df, use_container_width=True)

st.divider()

# -------------------------------
# LEDGER VIEW
# -------------------------------
st.subheader("📘 Ledger Entries (Auto Generated)")

ledger_df = generate_ledger(df)

if ledger_df.empty:
    st.info("No ledger entries available.")
else:
    st.dataframe(ledger_df, use_container_width=True)

    # Pretty display for demo impact
    st.markdown("### 🧾 Journal Entries")
    for _, row in ledger_df.iterrows():
        st.markdown(f"""
        **Date:** {row['Date']}  
        **Dr:** {row['Debit']} ₹{row['Amount']}  
        **Cr:** {row['Credit']} ₹{row['Amount']}  
        ---
        """)

# -------------------------------
# AUTO REFRESH (LIVE DEMO EFFECT)
# -------------------------------
st.markdown("⏳ Auto-refreshing every 10 seconds...")
time.sleep(10)
st.rerun()