# 🤖 Universal Data Pipeline & Dynamic Dashboard

A professional, schema-agnostic data cleaning, standardization, and interactive analytics web application built with **Python** and **Streamlit**. This tool is designed to automatically ingest any messy CSV or Excel dataset, clean errors, standardize contact details, deduplicate records, generate dynamic visualizations, and export comprehensive executive reports in CSV and PDF formats.

---

## 🌟 Key Features

- **Universal Ingestion:** Supports any structured CSV or Excel (`.xlsx`) file regardless of column naming conventions.
- **Smart Data Detection & Cleaning:**
  - Automatically detects and sanitizes text strings and emails using regular expressions (RegEx).
  - Standardizes international phone numbers using Google's `phonenumbers` library with custom country code selection (US, EG, SA, AE, etc.).
- **Flexible Deduplication:** Offers automated key detection (Email, Phone, ID) or custom column-based deduplication.
- **Interactive Analytical Dashboard:** Dynamically adapts to dataset structures, rendering quality breakdown pie charts, categorical bar charts, or numerical distribution histograms via **Plotly**.
- **Executive PDF Reporting:** Generates a multi-page, professional PDF report containing pipeline performance metrics, field-level analytical insights, and a complete export of all cleaned records without text truncation.
- **Modern UI/UX:** Styled with clean CSS, custom metric cards, scrollable raw/cleaned dataframes, and loading spinners for seamless user experience.

---

## 🛠️ Tech Stack

- **Programming Language:** Python 3.8+
- **Web Framework:** Streamlit
- **Data Processing:** Pandas
- **Data Visualization:** Plotly Express
- **PDF Generation:** FPDF2
- **Phone Standardization:** Phonenumbers library

---
