import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Streamlit App Title
st.title("📊 Aplikasi Manajemen Kartu Obligo")
st.write("Unggah data kartu obligo untuk melihat analisis proyek dan kredit.")

# File Uploader
uploaded_file = st.file_uploader("Upload file kartu obligo (CSV/XLS/XLSX)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    try:
        file_bytes = io.BytesIO(uploaded_file.getvalue())
        
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(file_bytes)
        elif uploaded_file.name.endswith(".xls"):
            xls = pd.ExcelFile(file_bytes, engine="xlrd")  # Gunakan xlrd untuk .xls
        else:
            xls = pd.ExcelFile(file_bytes, engine="openpyxl")  # Gunakan openpyxl untuk .xlsx
        
        sheet_name = st.selectbox("Pilih sheet untuk dianalisis", xls.sheet_names)
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Hapus baris kosong
        df.dropna(how="all", inplace=True)
        
        # Cari baris header yang benar
        for i in range(5):  # Cek di 5 baris pertama
            if "No. Loan" in df.iloc[i].values:
                df.columns = df.iloc[i]
                df = df[i+1:].reset_index(drop=True)
                break
        
        # Ubah tipe data agar dapat diserialisasi ke JSON
        df = df.convert_dtypes()
        df = df.applymap(lambda x: int(x) if isinstance(x, pd.Int64Dtype) else x)
        df = df.astype({col: "int" for col in df.select_dtypes(include=["int64"]).columns})
        
        st.write("### Data Kartu Obligo", df.head())

        # Kolom yang diharapkan
        expected_columns = [
            "No.", "No. Loan", "Nama Proyek", "Nomor Kontrak/PO/SPK", "Bowheer", 
            "Nilai Kontrak / Proyek", "Jatuh Tempo Kontrak", "Total Pencairan (Rp)", 
            "Jatuh Tempo Fasilitas", "Baki Debet (Rp)", "Keterangan", "Progress", 
            "Tanggal Kredit", "Nominal Kredit"
        ]
        
        # Filter hanya kolom yang sesuai
        df = df[[col for col in expected_columns if col in df.columns]]
        
        # Pastikan ada kolom yang sesuai
        required_columns = {"Nama Proyek", "Total Pencairan (Rp)", "Baki Debet (Rp)", "Nominal Kredit", "Jatuh Tempo Kontrak", "Jatuh Tempo Fasilitas"}
        if not required_columns.issubset(df.columns):
            st.error("File harus memiliki kolom yang sesuai dengan format kartu obligo. Cek apakah nama kolom di file sudah benar.")
        else:
            # Hitung Saldo Kredit
            df["Saldo Kredit"] = df["Nominal Kredit"] - df["Total Pencairan (Rp)"]
            
            # Konversi tanggal ke string sebelum menampilkan
            df = df.astype(str)
            
            # Tampilkan Data
            st.write("### Ringkasan Kredit Proyek")
            st.dataframe(df)
            
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
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
