import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (도표 및 비교 데이터 추가) ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    font_path = "NanumGothic.ttf"
    font_ready = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("Nanum", "", font_path)
            pdf.set_font("Nanum", "", 12)
            font_name = "Nanum"
            font_ready = True
        except: font_name = "Arial"
    else: font_name = "Arial"

    # 헤더
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 20)
    pdf.set_text_color(0, 82, 156)
    title = "V-GEN VPP 수익 분석 보고서" if font_ready else "V-GEN VPP Analysis Report"
    pdf.cell(190, 20, title, ln=True, align='C')
    pdf.ln(5)
    
    # 기본 정보
    pdf.set_font(font_name, "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, " 1. 발전소 정보", ln=True, fill=True)
    pdf.ln(2)
    pdf.cell(95, 10, f"위치: {data['region']}")
    pdf.cell(95, 10, f"용량: {data['cap']} MW", ln=True)
    pdf.ln(5)

    # 수익 비교 도표 (참여 전 vs 참여 후)
    pdf.set_font(font_name, "", 12)
    pdf.cell(190, 10, " 2. VPP 참여 전/후 수익 비교 (연간 예상)", ln=True, fill=True)
    pdf.ln(3)
    
    # 표 헤더
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(80, 10, "구분", border=1, align='C', fill=True)
    pdf.cell(55, 10, "참여 전", border=1, align='C', fill=True)
    pdf.cell(55, 10, "참여 후 (VPP)", border=1, align='C', fill=True)
    pdf.ln()
    
    # 표 내용
    pdf.cell(80, 10, "기본 전력판매 수익", border=1)
    pdf.cell(55, 10, f"{data['base_rev']:,.0f}", border=1, align='R')
    pdf.cell(55, 10, f"{data['base_rev']:,.0f}", border=1, align='R')
    pdf.ln()
    
    pdf.set_text_color(0, 82, 156)
    pdf.cell(80, 10, "VPP 추가 순수익 (정산금)", border=1)
    pdf.cell(55, 10, "0", border=1, align='R')
    pdf.cell(55, 10, f"+ {data['extra_profit']:,.0f}", border=1, align='R')
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, "", 12)
    pdf.cell(80, 12, "총 예상 매출 (합계)", border=1, fill=True)
    pdf.cell(55, 12, f"{data['base_rev']:,.0f}", border=1, align='R', fill=True)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(55, 12, f"{data['base_rev'] + data['extra_profit']:,.0f}", border=1, align='R', fill=True)
    pdf.ln(15)

    # 상세 설명
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, "", 11)
    pdf.multi_cell(190, 8, 
        "본 보고서는 브이젠의 입찰 최적화 알고리즘을 적용한 수치입니다.\n"
        "제주 입찰 시장의 핵심인 MEP, CP, MAP 등 5대 정산금을 극대화하여\n"
        "기존 고정가격 대비 추가 수익을 안정적으로 확보할 수 있습니다."
    )

    return bytes(pdf.output())

# --- 2. 데이터 및 입력 (기존 모든 항목 유지) ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

with st.sidebar:
    st.header("📍 1. 발전소 제원")
    selected_region = st.selectbox("위치 선택", list(region_presets.keys()))
    preset = region_presets[selected_region]
    
    cap_mw = st.number_input("용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("고정가격 단가 (원)", value=180)

    st.header("📊 2. 5대 정산금 직접수정")
    in_mep = st.number_input("MEP (전력량)", value=preset['mep'])
    in_cp = st.number_input("CP (용량)", value=preset['cp'])
    in_map = st.number_input("MAP (기대이익)", value=preset['map'])
    in_mwp = st.number_input("MWP (변동비)", value=preset['mwp'])
    in_imbp = st.number_input("IMBP (페널티)", value=preset['imbp'])

    st.header("💰 3. 수수료 설정")
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)
owner_extra_profit_yr = annual_gen * owner_net_extra_unit
base_rev_yr = annual_gen * fixed_p

# --- 4. 메인 화면 시각화 (기존 항목 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("5대 정산금 합계", f"{gross_extra_unit:.2f}원")
with m2: st.metric("사업자 순증분", f"{owner_net_extra_unit:.2f}원")
with m3: st.metric("연 순이익 증분", f"{owner_extra_profit_yr/10000:,.0f}만원")
with m4: st.metric("최종 예상 단가", f"{fixed_p + owner_net_extra_unit:.1f}원")

st.divider()

col1, col2 = st.columns([1.5, 1])
with col1:
    st.subheader("📈 수익 구성 워터폴")
    fig = go.Figure(go.Waterfall(
        x = ["기본단가", "CP", "MEP", "MAP", "기타/페널티", "최종단가"],
        y = [fixed_p, in_cp, in_mep, in_map, in_mwp-in_imbp, 0],
        measure = ["relative", "relative", "relative", "relative", "relative", "total"]
    ))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 정산 상세 테이블")
    df = pd.DataFrame({
        "구분": ["참여 전 매출", "VPP 추가 수익", "최종 합계"],
        "금액(만원/년)": [f"{base_rev_yr/10000:,.0f}", f"{owner_extra_profit_yr/10000:,.0f}", f"{(base_rev_yr + owner_extra_profit_yr)/10000:,.0f}"]
    })
    st.table(df)

# --- 5. PDF 다운로드 및 리포트 데이터 ---
st.divider()
st.subheader("📥 전문 수익 분석 리포트 발급")

report_params = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "region": selected_region,
    "cap": cap_mw,
    "base_rev": base_rev_yr,
    "extra_profit": owner_extra_profit_yr
}

if st.button("전문 PDF 리포트 생성"):
    try:
        pdf_bytes = create_pdf(report_params)
        st.download_button(
            label="🚀 한글 PDF 리포트 다운로드 (비교 도표 포함)",
            data=pdf_bytes,
            file_name=f"VGEN_VPP_Report_{datetime.now().strftime('%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"PDF 생성 오류: {e}")
