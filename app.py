import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (한글 지원 및 에러 방지) ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 폰트 파일 경로 확인 (app.py와 같은 위치)
    font_path = "NanumGothic.ttf"
    
    font_ready = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("Nanum", "", font_path)
            pdf.set_font("Nanum", "", 12)
            font_name = "Nanum"
            font_ready = True
        except:
            font_name = "Arial"
    else:
        font_name = "Arial"

    # PDF 내용 작성
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 20)
    pdf.set_text_color(0, 82, 156)
    title = "V-GEN VPP 수익 분석 보고서" if font_ready else "V-GEN Profit Analysis Report"
    pdf.cell(190, 20, title, ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font(font_name, "", 12)
    pdf.set_text_color(0, 0, 0)
    
    if font_ready:
        pdf.cell(190, 10, f"분석 일자: {data['date']}", ln=True)
        pdf.cell(190, 10, f"발전소 위치: {data['region']}", ln=True)
        pdf.cell(190, 10, f"설비 용량: {data['cap']} MW", ln=True)
        pdf.cell(190, 10, f"연간 추가 수익: {data['extra_profit']:,.0f} 원", ln=True)
    else:
        pdf.cell(190, 10, f"Date: {data['date']}", ln=True)
        pdf.cell(190, 10, f"Region: {data['region_eng']}", ln=True)
        pdf.cell(190, 10, f"Capacity: {data['cap']} MW", ln=True)
        pdf.cell(190, 10, f"Extra Profit: {data['extra_profit']:,.0f} KRW", ln=True)

    return bytes(pdf.output())

# --- 2. 데이터 프리셋 (반드시 입력창 이전에 정의) ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

# --- 3. 사이드바 입력창 (selected_region 변수가 여기서 생성됨) ---
with st.sidebar:
    st.header("📍 발전소 제원 설정")
    # [핵심] 변수 정의가 가장 먼저 와야 함
    selected_region = st.selectbox("위치 선택", list(region_presets.keys()))
    preset = region_presets[selected_region]
    
    cap_mw = st.number_input("용량 (MW)", value=1.0)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("고정가격 (원)", value=180)
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 4. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = preset['mep'] + preset['cp'] + preset['map'] + preset['mwp'] - preset['imbp']
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)
owner_extra_profit_yr = annual_gen * owner_net_extra_unit

# --- 5. 메인 UI 출력 ---
st.title("📑 V-GEN VPP 수익 분석기")
st.metric("연간 추가 순수익 예상", f"{owner_extra_profit_yr/10000:,.0f} 만원")

# --- 6. PDF 다운로드 섹션 (selected_region 정의 이후에 배치) ---
st.divider()
st.subheader("📥 맞춤형 분석 리포트 생성")

# PDF 전용 데이터 정리
report_params = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "region": selected_region,
    "region_eng": "Jeju" if "제주" in selected_region else "Mainland",
    "cap": cap_mw,
    "extra_profit": owner_extra_profit_yr
}

if st.button("PDF 리포트 생성"):
    try:
        pdf_data = create_pdf(report_params)
        st.download_button(
            label="📩 한글 리포트(PDF) 다운로드",
            data=pdf_data,
            file_name=f"VGEN_Report_{datetime.now().strftime('%m%d')}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF 생성 오류: {e}")
