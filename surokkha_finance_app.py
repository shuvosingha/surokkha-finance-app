import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# -------------------- Configuration --------------------
st.set_page_config(page_title="Surokkha Vet Clinics", layout="wide")
LOGO_PATH = r"logo.png"
DATA_FILE = "transactions.csv"
CATEGORY_FILE = "categories.csv"

# -------------------- Initialize Session State --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# -------------------- User Roles --------------------
USERS = {
    "admin": {"password": "surokkha123", "role": "Admin"},
    "staff1": {"password": "staffpass", "role": "Staff"},
    "viewer1": {"password": "viewonly", "role": "Viewer"}
}

# -------------------- Login --------------------
if not st.session_state.logged_in:
    st.title("🔐 Login to Surokkha Finance App")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# -------------------- Header --------------------
col1, col2 = st.columns([1, 5])
with col1:
    st.image(LOGO_PATH, width=100)
with col2:
    st.title("💼 Surokkha Vet Clinics - Income & Expense Manager")
    st.markdown(f"👤 Logged in as: **{st.session_state.username}** ({st.session_state.role})")

# -------------------- Load/Save Data --------------------
def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame(columns=[
            "Date", "Category", "Type", "Amount", "Payment Method",
            "Client Name", "Phone Number", "Duty Doctor", "Details"
        ])

def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)

def load_categories():
    try:
        cats = pd.read_csv(CATEGORY_FILE)
        if "Category" not in cats.columns or "Type" not in cats.columns:
            return pd.DataFrame({"Category": [], "Type": []})
        return cats
    except Exception:
        return pd.DataFrame({"Category": [], "Type": []})

def save_categories(df: pd.DataFrame):
    df.to_csv(CATEGORY_FILE, index=False)

df = load_data()
categories = load_categories()

# -------------------- Sidebar --------------------
st.sidebar.header("🔍 Filter Transactions")

date_default = [datetime.today() - timedelta(days=30), datetime.today()]
date_range = st.sidebar.date_input("Date Range", date_default)

# Handle single-date selection gracefully
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range
    end_date = date_range

type_filter = st.sidebar.multiselect("Type", ["Income", "Expense"], default=["Income", "Expense"])

# Logout control
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

# Apply filters
filtered_df = df.copy()
if not filtered_df.empty:
    filtered_df = filtered_df[
        (filtered_df["Date"] >= pd.to_datetime(start_date)) &
        (filtered_df["Date"] <= pd.to_datetime(end_date)) &
        (filtered_df["Type"].isin(type_filter))
    ]

# -------------------- Transaction Entry --------------------
if st.session_state.role in ["Admin", "Staff"]:
    st.subheader("➕ Add New Transaction")
    with st.form("transaction_form"):
        col1, col2, col3 = st.columns(3)

        # Category options
        category_options = categories["Category"].unique().tolist() if not categories.empty else []

        with col1:
            date = st.date_input("Date", datetime.today())
            if category_options:
                category = st.selectbox("Category", category_options)
            else:
                st.info("No categories yet. Add in Category Manager below.")
                category = st.text_input("Category")
            trans_type = st.selectbox("Type", ["Income", "Expense"])

        with col2:
            amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
            payment_method = st.selectbox("Payment Method", ["Cash", "Card", "bKash", "Nagad", "Bank", "Other"])
            client_name = st.text_input("Client Name")

        with col3:
            phone = st.text_input("Phone Number")
            client_address = st.text_input("Client Address")
            doctor = st.text_input("Duty Doctor")
            details = st.text_area("Details")

        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            if not category:
                st.error("Please enter/select a Category.")
            else:
                new_row = pd.DataFrame([{
                    "Date": pd.to_datetime(date),
                    "Category": category,
                    "Type": trans_type,
                    "Amount": float(amount),
                    "Payment Method": payment_method,
                    "Client Name": client_name,
                    "Phone Number": phone,
                    "Client Address": client_address,
                    "Duty Doctor": doctor,
                    "Details": details
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("✅ Transaction added!")

# -------------------- Transactions Table --------------------
st.subheader("📋 Transaction Records")
st.dataframe(
    (filtered_df.sort_values("Date", ascending=False) if not filtered_df.empty else filtered_df),
    use_container_width=True
)


# -------------------- Export --------------------
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=(filtered_df.to_csv(index=False) if not filtered_df.empty else df.head(0).to_csv(index=False)).encode("utf-8"),
    file_name="surokkha_transactions.csv",
    mime="text/csv"
)

# -------------------- Category Manager --------------------
if st.session_state.role == "Admin":
    st.subheader("🗂️ Category Manager")
    with st.expander("Manage Categories"):
        colA, colB = st.columns([2,1])
        with colA:
            new_cat = st.text_input("New Category")
        with colB:
            new_type = st.selectbox("Type for New Category", ["Income", "Expense"])
        add_clicked = st.button("Add Category")
        if add_clicked:
            if not new_cat:
                st.error("Please enter a category name.")
            else:
                categories = pd.concat(
                    [categories, pd.DataFrame([{"Category": new_cat, "Type": new_type}])],
                    ignore_index=True
                )
                save_categories(categories)
                st.success(f"✅ Category '{new_cat}' added!")
        st.dataframe(categories, use_container_width=True)

# -------------------- Analytics --------------------
if st.session_state.role in ["Admin", "Staff"]:
    st.subheader("📊 Data Analytics")

    def show_summary(df_in: pd.DataFrame, label: str):
        income = df_in[df_in["Type"] == "Income"]["Amount"].sum() if not df_in.empty else 0.0
        expense = df_in[df_in["Type"] == "Expense"]["Amount"].sum() if not df_in.empty else 0.0
        count = len(df_in)
        st.markdown(f"**{label}**")
        cols = st.columns(3)
        cols[0].metric("Total Income", f"৳ {income:,.2f}")
        cols[1].metric("Total Expense", f"৳ {expense:,.2f}")
        cols[2].metric("Transactions", count)

    periods = {
        "Last 7 Days": datetime.today() - timedelta(days=7),
        "Last 30 Days": datetime.today() - timedelta(days=30),
        "Last 3 Months": datetime.today() - timedelta(days=90),
        "Last 6 Months": datetime.today() - timedelta(days=180),
        "Last Year": datetime.today() - timedelta(days=365)
    }

    for label, start in periods.items():
        period_df = df[df["Date"] >= start] if not df.empty else df
        show_summary(period_df, label)

# -------------------- Graphs --------------------
st.subheader("📈 Income & Expense Graphs")
graph_df = df.copy()
graph_df["Date"] = pd.to_datetime(graph_df["Date"], errors="coerce")

if not graph_df.empty:
    graph_df["Month"] = graph_df["Date"].dt.to_period("M").astype(str)

    col1, col2 = st.columns(2)
    with col1:
        inc = graph_df[graph_df["Type"] == "Income"]
        fig_income = px.bar(
            inc, x="Month", y="Amount", color="Category",
            title="Monthly Income", barmode="stack"
        ) if not inc.empty else None
        if fig_income:
            st.plotly_chart(fig_income, use_container_width=True)
        else:
            st.info("No income data to display yet.")

    with col2:
        exp = graph_df[graph_df["Type"] == "Expense"]
        fig_expense = px.bar(
            exp, x="Month", y="Amount", color="Category",
            title="Monthly Expense", barmode="stack"
        ) if not exp.empty else None
        if fig_expense:
            st.plotly_chart(fig_expense, use_container_width=True)
        else:
            st.info("No expense data to display yet.")
else:
    st.info("No data yet. Add transactions to see analytics and charts.")

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import io
import qrcode

def generate_receipt_pdf(row):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Draw letter pad background
    try:
        letterpad = ImageReader("letterpad.png")  # Ensure this file is in your GitHub repo
        c.drawImage(letterpad, 0, 0, width=width, height=height)
    except:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, "Surokkha Vet Clinics")

    # Receipt Title
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#0B6E4F"))
    c.drawCentredString(width / 2, height - 180, "Income & Expense Receipt")

    # Billed To Section
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(50, height - 210, "Billed To:")
    c.setFont("Helvetica", 10)
    c.drawString(120, height - 210, f"{row['Client Name']} | {row['Phone Number']}")
    c.drawString(120, height - 225, f"Address: {row.get('Client Address', '')}")
    c.drawString(120, height - 240, f"Duty Doctor: {row['Duty Doctor']}")

    # Itemized Table
    y = height - 270
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Service")
    c.drawString(250, y, "Unit Price")
    c.drawString(350, y, "Quantity")
    c.drawString(450, y, "Total")
    y -= 15
    c.line(50, y, 550, y)
    y -= 20

    # Single item
    service = row["Category"]
    unit_price = float(row["Amount"])
    quantity = 1
    total = unit_price * quantity

    c.setFont("Helvetica", 10)
    c.drawString(50, y, service)
    c.drawString(250, y, f"৳ {unit_price:.2f}")
    c.drawString(350, y, str(quantity))
    c.drawString(450, y, f"৳ {total:.2f}")
    y -= 30

    # Totals
    tax = round(total * 0.05, 2)
    grand_total = total + tax

    c.setFont("Helvetica-Bold", 10)
    c.drawString(350, y, "Subtotal:")
    c.drawString(450, y, f"৳ {total:.2f}")
    y -= 15
    c.drawString(350, y, "Tax (5%):")
    c.drawString(450, y, f"৳ {tax:.2f}")
    y -= 15
    c.drawString(350, y, "Total:")
    c.drawString(450, y, f"৳ {grand_total:.2f}")
    y -= 30

    # QR Code
    qr = qrcode.make("https://www.surokkhavetclinics.com")
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_img = ImageReader(qr_buffer)
    c.drawImage(qr_img, width - 120, 50, width=60, height=60)

    # Footer Note
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.black)
    c.drawString(50, 40, "Thank you for choosing Surokkha Vet Clinics.")
    c.drawString(50, 25, "This receipt was generated digitally and does not require a signature.")

    # Duty Doctor Signature Block
    c.setFont("Helvetica", 10)
    c.drawString(width - 200, 80, f"Duty Doctor: {row['Duty Doctor']}")
    c.line(width - 200, 75, width - 50, 75)
    c.drawString(width - 200, 60, "Signature")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

st.subheader("🧾 Generate Receipt")

for i, row in filtered_df.iterrows():
    with st.expander(f"Receipt for {row['Client Name']} on {row['Date'].date()}"):
        if st.button(f"Generate PDF", key=f"receipt_{i}"):
            pdf_buffer = generate_receipt_pdf(row)
            st.download_button(
                label="📥 Download Receipt",
                data=pdf_buffer,
                file_name=f"receipt_{row['Client Name'].replace(' ', '_')}_{row['Date'].date()}.pdf",
                mime="application/pdf"
            )








