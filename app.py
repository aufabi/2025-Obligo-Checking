import streamlit as st
import pandas as pd
import plotly.express as px

# Streamlit App Title
st.title("📊 Aplikasi Manajemen Kartu Obligo")
st.write("Unggah data kartu obligo untuk melihat analisis proyek dan kredit.")

# File Uploader
uploaded_file = st.file_uploader("Upload file kartu obligo (CSV/XLS/XLSX)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file Excel: {e}")
        st.stop()
    
    st.write("### Data Kartu Obligo", df.head())

    # Pastikan ada kolom yang sesuai
    required_columns = {"Nama Proyek", "Total Pencairan (Rp)", "Baki Debet (Rp)", "Nominal Kredit", "Jatuh Tempo Kontrak", "Jatuh Tempo Fasilitas"}
    if not required_columns.issubset(df.columns):
        st.error("File harus memiliki kolom yang sesuai dengan format kartu obligo.")
    else:
        # Hitung Saldo Kredit
        df["Saldo Kredit"] = df["Nominal Kredit"] - df["Total Pencairan (Rp)"]
        
        # Tampilkan Data
        st.write("### Ringkasan Kredit Proyek")
        st.dataframe(df[["Nama Proyek", "Nominal Kredit", "Total Pencairan (Rp)", "Baki Debet (Rp)", "Saldo Kredit"]])
        
        # Grafik Penggunaan Kredit
        fig_usage = px.bar(df, x="Nama Proyek", y="Total Pencairan (Rp)", title="Total Pencairan Kredit per Proyek", 
                           labels={"Total Pencairan (Rp)": "Total Pencairan (Rp)"}, text_auto=True)
        st.plotly_chart(fig_usage)
        
        # Grafik Saldo Kredit
        fig_balance = px.bar(df, x="Nama Proyek", y="Saldo Kredit", title="Saldo Kredit Tersisa per Proyek", 
                             labels={"Saldo Kredit": "Saldo Kredit (Rp)"}, text_auto=True)
        st.plotly_chart(fig_balance)
        
        # Notifikasi Proyek yang Mendekati Jatuh Tempo
        df["Jatuh Tempo Kontrak"] = pd.to_datetime(df["Jatuh Tempo Kontrak"], errors='coerce')
        df["Jatuh Tempo Fasilitas"] = pd.to_datetime(df["Jatuh Tempo Fasilitas"], errors='coerce')
        
        upcoming_due = df[(df["Jatuh Tempo Kontrak"].notna()) & (df["Jatuh Tempo Kontrak"] <= pd.Timestamp.today() + pd.DateOffset(days=30))]
        
        if not upcoming_due.empty:
            st.warning("⚠️ Proyek berikut mendekati jatuh tempo kontrak:")
            st.dataframe(upcoming_due[["Nama Proyek", "Jatuh Tempo Kontrak", "Baki Debet (Rp)"]])
        else:
            st.success("✅ Tidak ada proyek yang mendekati jatuh tempo dalam 30 hari ke depan!")
