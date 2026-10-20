import streamlit as st
import pandas as pd
import re
import phonenumbers
import plotly.express as px
from fpdf import FPDF

# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="Universal Data Pipeline & Dynamic Dashboard",
    page_icon="🤖",
    layout="wide"
)
# ---------------------------------------------------------
# Custom CSS to make download buttons prominent
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Clean background and modern font styling */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Soft, professional, and less harsh header styling */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Modern card design for metric boxes */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e1e8ed;
    }
    
    /* Prominent and stylish download buttons */
    .stDownloadButton > button {
        background-color: #2ecc71 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        padding: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stDownloadButton > button:hover {
        background-color: #27ae60 !important;
        color: white !important;
    }
    
    /* Clean container styling for dataframes */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)
# ---------------------------------------------------------
# Smart Detection & Cleaning Logic
# ---------------------------------------------------------
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).strip()
    return re.sub(r'\s+', ' ', text)

def clean_email(email):
    if pd.isna(email):
        return ""
    email = str(email).strip().lower()
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return email
    return email

def format_phone(phone, country_code="US"):
    if pd.isna(phone):
        return ""
    phone_str = str(phone).strip()
    try:
        parsed_phone = phonenumbers.parse(phone_str, country_code)
        if phonenumbers.is_valid_number(parsed_phone):
            return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    return phone_str

def is_email_column(series):
    sample = series.dropna().astype(str).head(10)
    if len(sample) == 0:
        return False
    return sample.str.contains(r'[^@]+@[^@]+\.[^@]+', regex=True).mean() > 0.4

def process_dataframe(df, default_country="US", custom_dedup_col=None):
    initial_rows = len(df)
    
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].apply(clean_text)

    for col in df.columns:
        col_lower = str(col).lower()
        if 'email' in col_lower or 'mail' in col_lower or is_email_column(df[col]):
            df[col] = df[col].apply(clean_email)
        elif any(k in col_lower for k in ['phone', 'mobile', 'tel', 'cell', 'contact']):
            df[col] = df[col].apply(lambda x: format_phone(x, country_code=default_country))

    if custom_dedup_col and custom_dedup_col != "Auto Detect":
        df_clean = df.drop_duplicates(subset=[custom_dedup_col], keep='first')
        dedup_by = custom_dedup_col
    else:
        dedup_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['email', 'phone', 'id'])]
        if dedup_cols:
            df_clean = df.drop_duplicates(subset=[dedup_cols[0]], keep='first')
            dedup_by = dedup_cols[0]
        else:
            df_clean = df.drop_duplicates()
            dedup_by = "All Columns Exact Match"

    removed_duplicates = initial_rows - len(df_clean)
    return df_clean, initial_rows, removed_duplicates, dedup_by

# ---------------------------------------------------------
# PDF Report Generator (Fixed Full Data & No Text Truncation)
# ---------------------------------------------------------
class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", 'B', 15)
        self.set_text_color(31, 58, 147)
        self.cell(0, 8, "Data Pipeline Analytics & Full Data Report", ln=True, align='C')
        self.set_font("Helvetica", 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, "Complete Dataset Audit & Cleaned Records Export", ln=True, align='C')
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()}", align='C')

def generate_pdf_report(initial_rows, cleaned_df, removed_dupes):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    
    cleaned_rows = len(cleaned_df)
    efficiency_rate = f"{((cleaned_rows/initial_rows)*100):.1f}%" if initial_rows > 0 else "0%"
    
    # Section 1: Executive Metrics Summary
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "1. Executive Pipeline Summary", ln=True)
    
    metrics_data = [
        ("Total Raw Input Records:", str(initial_rows)),
        ("Cleaned Unique Output Records:", str(cleaned_rows)),
        ("Duplicates Identified & Removed:", str(removed_dupes)),
        ("Data Quality Score:", efficiency_rate)
    ]
    
    pdf.set_font("Helvetica", size=9)
    pdf.set_fill_color(245, 247, 250)
    for label, val in metrics_data:
        pdf.cell(100, 6, f"  {label}", border=1, fill=True)
        pdf.cell(90, 6, f" {val}", border=1, ln=True, fill=True)
        
    pdf.ln(4)

    # Section 2: Key Data Insights
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 6, "2. Key Data Insights & Field Distribution", ln=True)
    pdf.set_font("Helvetica", size=9)
    
    for col in cleaned_df.columns:
        unique_vals = cleaned_df[col].nunique()
        top_val = cleaned_df[col].mode()[0] if not cleaned_df[col].empty else "N/A"
        insight_text = f"- Field '{col}': {unique_vals} unique values. Top entry: '{top_val}'."
        pdf.multi_cell(0, 5, insight_text)
        
    pdf.ln(4)

    # Section 3: COMPLETE Cleaned Dataset Records (Full Data without Truncation)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 6, f"3. Complete Cleaned Dataset Records ({cleaned_rows} rows)", ln=True)
    
    cols = list(cleaned_df.columns)
    total_width = 190
    col_width = total_width / max(len(cols), 1)
    
    # Table Header
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_fill_color(220, 230, 242)
    for col in cols:
        pdf.cell(col_width, 6, str(col), border=1, fill=True, align='C')
    pdf.ln()

    # Table Rows (Loops through ALL rows, showing full text without [:15] restriction)
    pdf.set_font("Helvetica", size=7)
    for _, row in cleaned_df.iterrows():
        for col in cols:
            val_str = str(row[col]) if not pd.isna(row[col]) else ""
            pdf.cell(col_width, 5, val_str, border=1, align='L') # تم إزالة قيد القص لظهر الإيميل كاملاً
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# ---------------------------------------------------------
# UI Main Layout
# ---------------------------------------------------------
st.title("🤖 Universal Data Pipeline & Interactive Dashboard")
st.markdown("Upload any structured CSV or Excel file. The system automatically detects data types, cleans errors, deduplicates records, and generates full analytics.")

st.sidebar.header("⚙️ Configuration Controls")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])
country_code = st.sidebar.selectbox("Phone Country Standard", ["US", "EG", "SA", "AE", "GB", "CA"], index=0)

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        raw_df = pd.read_csv(uploaded_file)
    else:
        raw_df = pd.read_excel(uploaded_file)

    dedup_option = st.sidebar.selectbox("Select Key Column for Deduplication", ["Auto Detect"] + list(raw_df.columns))

    st.subheader("📋 Raw Input Preview (All Data with Scrollbar)")
    st.dataframe(raw_df, height=250, use_container_width=True)

    clean_df, initial_count, removed_count, dedup_key = process_dataframe(
        raw_df, default_country=country_code, custom_dedup_col=dedup_option
    )

    st.markdown("---")
    st.subheader("📊 Key Quality Metrics")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Original Records", initial_count)
    m2.metric("Cleaned Records", len(clean_df))
    m3.metric("Duplicates Removed", removed_count)
    m4.metric("Deduplicated Key", str(dedup_key))

    st.subheader("✨ Cleaned & Consolidated Output Data")
    st.dataframe(clean_df, height=250, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Dynamic Analytical Dashboard")
    
    c1, c2 = st.columns(2)

    with c1:
        pie_df = pd.DataFrame({
            'Status': ['Clean Unique', 'Duplicates Removed'],
            'Count': [len(clean_df), removed_count]
        })
        fig_pie = px.pie(pie_df, values='Count', names='Status', title="Data Quality Breakdown", color_discrete_sequence=['#2ecc71', '#e74c3c'])
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        numeric_cols = clean_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = [c for c in clean_df.select_dtypes(include=['object', 'string']).columns if not any(k in c.lower() for k in ['email', 'phone', 'mail'])]

        if categorical_cols:
            selected_col = st.selectbox("Categorical Field Breakdown", categorical_cols)
            top_counts = clean_df[selected_col].value_counts().head(10).reset_index()
            top_counts.columns = [selected_col, 'Count']
            fig_bar = px.bar(top_counts, x=selected_col, y='Count', title=f"Top Values in '{selected_col}'", color='Count', color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)
        elif numeric_cols:
            selected_num = st.selectbox("Select Numeric Distribution", numeric_cols)
            fig_hist = px.histogram(clean_df, x=selected_num, title=f"Distribution of '{selected_num}'", color_discrete_sequence=['#3498db'])
            st.plotly_chart(fig_hist, use_container_width=True)

    # ---------------------------------------------------------
    # Export Section with Progress Indicator
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("💾 Export Clean Output & Executive PDF")

    e1, e2 = st.columns(2)

    with e1:
        # Download Clean CSV Data
        csv_bytes = clean_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download Clean CSV Data",
            data=csv_bytes,
            file_name="clean_consolidated_output.csv",
            mime="text/csv"
        )

    with e2:
        # Show generating status before rendering the download button
        with st.spinner("⏳ Generating Executive PDF Report... Please wait"):
            pdf_bytes = generate_pdf_report(initial_count, clean_df, removed_count)
            
        st.download_button(
            label="📄 Download Full Analytics & All Records PDF Report",
            data=pdf_bytes,
            file_name="Executive_Data_Analytics_Report.pdf",
            mime="application/pdf"
        )