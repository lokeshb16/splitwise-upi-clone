import streamlit as st
import requests
import json

# Page config and Title
st.set_page_config(page_title="Splitwise UPI Clone", layout="wide")
st.title("🇮🇳 Splitwise Clone with Instant UPI Settlement")

# Backend API URL
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")

# 🛠️ SIDEBAR: Control Panel (Reset Button)
with st.sidebar:
    st.header("⚙️ Admin Controls")
    st.write("Click the button below to clear all testing data from the database.")
    
    # Red color danger button
    if st.button("🔥 Reset Database", type="secondary", use_container_width=True):
        try:
            response = requests.post(f"{BACKEND_URL}/reset-database/", timeout=5)
            if response.status_code == 200:
                st.success("💥 Database successfully reset! All IDs start from 1 again.")
                st.balloons() # Quick success animation
            else:
                st.error("Something went wrong on the backend.")
        except Exception as e:
            st.error(f"Backend not connected: {e}")

# Creating tabs for different features
tabs = st.tabs(["👥 Manage Users & Groups", "💸 Add Expense", "🧾 Settlement & UPI Pay"])

# ------------------------------------------------------------------
# TAB 1: MANAGE USERS & GROUPS
# ------------------------------------------------------------------
with tabs[0]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Create New User")
        u_name = st.text_input("Full Name", value="lokesh bavistale")
        u_phone = st.text_input("Phone Number", value="9111111111")
        u_upi = st.text_input("UPI ID (VPA)", value="lokesh@oksbi")
        
        if st.button("Register User"):
            if u_name and u_phone and u_upi:
                params = {
                    "name": u_name,
                    "phone": u_phone,
                    "upi_id": u_upi
                }
                try:
                    response = requests.post(f"{BACKEND_URL}/users/", params=params, timeout=5)
                    if response.status_code == 200:
                        st.success(f"User Created! ID: {response.json()['id']}")
                    else:
                        st.error(f"Backend Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Connection Error: {e}")
            else:
                st.warning("Please fill all user fields.")

    with col2:
        st.subheader("👥 Create Expense Group")
        g_name = st.text_input("Group Name", placeholder="e.g., Flatmates, Goa Trip")
        g_members = st.text_input("Member IDs (Comma Separated)", placeholder="e.g., [1, 2, 3]")
        
        if st.button("Create Group"):
            if g_name and g_members:
                try:
                    json_valid = json.loads(g_members)
                    response = requests.post(f"{BACKEND_URL}/groups/?name={g_name}&member_ids={g_members}")
                    if response.status_code == 200:
                        st.success(f"Group '{g_name}' Created Successfully! ID: {response.json()['id']}")
                except Exception as e:
                    st.error("Please enter Member IDs in correct format like [1, 2, 3]")
            else:
                st.warning("Please fill all group fields.")

# ------------------------------------------------------------------
# TAB 2: ADD EXPENSE
# ------------------------------------------------------------------
with tabs[1]:
    st.subheader("💰 Log a New Expense (Splits Equally)")
    
    exp_group_id = st.number_input("Group ID", min_value=1, step=1)
    exp_payer_id = st.number_input("Payer (User ID)", min_value=1, step=1)
    exp_amount = st.number_input("Total Amount (₹)", min_value=1.0, value=100.0)
    exp_desc = st.text_input("Description / Note", placeholder="e.g., Dinner, Room Rent")
    
    if st.button("Submit & Split Expense"):
        if exp_group_id and exp_payer_id and exp_amount:
            url = f"{BACKEND_URL}/expenses/?group_id={exp_group_id}&paid_by_id={exp_payer_id}&amount={exp_amount}&description={exp_desc}"
            response = requests.post(url)
            if response.status_code == 200:
                st.success("Expense added and split equally among all members!")
            else:
                st.error("Failed to add expense. Check if Group ID exists.")
        else:
            st.warning("Please fill all required fields.")

# ------------------------------------------------------------------
# TAB 3: SETTLEMENT & UPI PAY
# ------------------------------------------------------------------
with tabs[2]:
    st.subheader("🧾 Simplified Debt Matrix & Instant Pay")
    
    settle_group_id = st.number_input("Enter Group ID to Settle", min_value=1, step=1)
    
    if st.button("Calculate Settlements"):
        response = requests.get(f"{BACKEND_URL}/groups/{settle_group_id}/settle/")
        
        if response.status_code == 200:
            settlements = response.json()
            
            if not settlements:
                st.info("🎉 All caught up! No pending balances in this group.")
            else:
                st.write("### Pending Balances:")
                for tx in settlements:
                    col_tx, col_btn = st.columns([3, 1])
                    col_tx.markdown(f"👉 **{tx['from']}** owes **{tx['to']}** 💵 **₹{tx['amount']:.2f}**")
                    upi_link = tx['upi_url']
                    col_btn.link_button("⚡ Pay via UPI", upi_link, type="primary")
        else:
            st.error("Group not found or something went wrong.")