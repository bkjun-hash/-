import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기", layout="wide")

# --- PDF 생성 함수 ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    # 한글 폰트 설정 (기본 폰트는 한글 깨짐이 발생할 수 있어 영문/숫자 위주 구성 혹은 폰트 추가 필요)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "V-GEN VPP Profit Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(100, 10, f"Region: {data['region']}")
    pdf.cell(90, 10, f"Capacity: {data['cap']} MW", ln=True)
    pdf.cell(190, 10, f"Analysis Date: {data['date']}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "1. Estimated Unit Price (KRW/kWh)", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(100, 10, f"- Base Price: {data['fixed_p']} KRW")
    pdf.cell(90, 10, f"- VPP Extra: +{data['extra_p']:.2f} KRW", ln=True)
    pdf.cell(190, 10, f"- Final Price: {data['fixed_p'] + data['extra_p']:.2f} KRW", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "2. Annual Profit Forecast", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"- Annual Generation: {data['gen']:,.0f} kWh", ln=True)
    pdf.cell(190, 10, f"- Total Annual Extra Profit: {data['profit']:,.0f} KRW", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(190, 5, "Notice: This report is based on KPX settlement rules and V-GEN's algorithm. Actual returns may vary depending on market conditions.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- 기존 시뮬레이터 로직 (동일) ---
# (지역 설정, 사이드바 입력창 등 기존 코드 유지)
region_presets = {
    "Jeju (High Curtailment)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "Honam (Medium Curtailment)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "Others (Low Curtailment)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

with st.sidebar:
    st.header("📍 1. Region & Spec")
    selected_region = st.selectbox("Select Location", list(region_presets.keys()))
    preset = region_presets[selected_region]
    cap_mw = st.number_input("Capacity (MW)", value=1.0)
    fixed_p = st.number_input("Base Price (KRW)", value=180)
    vgen_fee_rate = st.slider("V-GEN Fee (%)", 0, 30, 20) / 100

# 계산
annual_gen = cap_mw * 1000 * 3.6 * 365
gross_extra = preset['mep'] + preset['cp'] + preset['map'] + preset['mwp'] - preset['imbp']
owner_net_extra = gross_extra * (1 - vgen_fee_rate)
annual_profit = annual_gen * owner_net_extra

# --- 메인 화면 결과 ---
st.title("📑 V-GEN VPP Profit Analysis")
st.success(f"Estimated Annual Extra Profit: {annual_profit/10000:,.0f} Million KRW")

st.markdown("---")

# --- [추가] PDF 다운로드 버튼 섹션 ---
st.subheader("📥 Download Analysis Report")
st.write("아래 버튼을 누르면 위 분석 결과가 담긴 PDF 리포트가 생성됩니다.")

# PDF 데이터 준비
report_data = {
    "region": selected_region,
    "cap": cap_mw,
    "fixed_p": fixed_p,
    "extra_p": owner_net_extra,
    "gen": annual_gen,
    "profit": annual_profit,
    "date": pd.Timestamp.now().strftime("%Y-%m-%d")
}

pdf_bytes = create_pdf(report_data)

st.download_button(
    label="📩 Download PDF Report",
    data=pdf_bytes,
    file_name=f"VGEN_Analysis_{selected_region}.pdf",
    mime="application/pdf"
)

st.markdown("---")
# (이후 워터폴 차트 등 기존 가시화 로직 유지)
