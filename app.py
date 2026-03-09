import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (한글 지원 및 디자인 강화) ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 한글 폰트 등록 (파일이 없을 경우 대비 예외처리)
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font("Nanum", "", font_path)
        pdf.set_font("Nanum", "", 12)
        font_name = "Nanum"
    else:
        st.error("NanumGothic.ttf 폰트 파일이 없습니다. 영문으로 출력됩니다.")
        pdf.set_font("Arial", "", 12)
        font_name = "Arial"

    # 헤더 섹션
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 20)
    pdf.set_text_color(0, 82, 156) # 브이젠 브랜드 컬러 느낌
    pdf.cell(190, 20, "V-GEN 제주 입찰시장 수익 분석 보고서", ln=True, align='C')
    pdf.ln(5)
    
    # 1. 요약 정보
    pdf.set_font(font_name, "", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, " 1. 분석 개요", ln=True, fill=True)
    pdf.set_font(font_name, "", 11)
    pdf.ln(2)
    pdf.cell(95, 10, f"분석 일자: {data['date']}")
    pdf.cell(95, 10, f"발전소 위치: {data['region']}", ln=True)
    pdf.cell(95, 10, f"설비 용량: {data['cap']} MW")
    pdf.cell(95, 10, f"일평균 발전시간: {data['gen_time']} 시간", ln=True)
    pdf.ln(5)

    # 2. 수익 분석 (중요 부분 강조)
    pdf.set_font(font_name, "", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, " 2. 연간 기대수익 시뮬레이션", ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font(font_name, "", 12)
    pdf.cell(100, 10, "기존 고정가격 계약 예상 매출:")
    pdf.cell(90, 10, f"{data['base_rev']:,.0f} 원", ln=True, align='R')
    
    # 추가 수익 강조 (파란색 배경)
    pdf.set_fill_color(230, 242, 255)
    pdf.set_font(font_name, "", 12)
    pdf.cell(100, 12, "VPP 참여 시 추가 순수익 (사업자 몫):", fill=True)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(90, 12, f"+ {data['extra_profit']:,.0f} 원 ", ln=True, align='R', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, "", 13)
    pdf.cell(100, 15, "최종 합산 예상 매출:")
    pdf.cell(90, 15, f"{data['base_rev'] + data['extra_profit']:,.0f} 원", ln=True, align='R')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)

    # 3. 상세 설명 (강조 컨텐츠)
    pdf.set_font(font_name, "", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, " 3. V-GEN 입찰 시스템 핵심 강점", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font(font_name, "", 10)
    pdf.multi_cell(190, 7, 
        "- 남동발전 제주 풍력자원 운영 실적: 국내 최초 제주 입찰 시장 실제 운영 데이터를 보유하고 있습니다.\n"
        "- 5대 정산금 최적화: MEP(전력량), CP(용량), MAP(보상) 등 복잡한 정산 항목을 AI 알고리즘으로 극대화합니다.\n"
        "- 출력제어 리스크 해소: 제주 지역의 고질적인 출력제어 문제를 MAP(기대이익보상) 정산금 확보를 통해 수익으로 전환합니다.\n"
        "- 투명한 정산 리포트: 매월 전력거래소 정산 자료와 연동된 투명한 수익 배분 리포트를 제공합니다."
    )
    
    pdf.ln(10)
    pdf.set_font(font_name, "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(190, 5, "본 리포트는 참고용이며, 실제 정산금은 전력거래소의 최종 확정 결과 및 시장 상황에 따라 달라질 수 있습니다.", align='C')

    return bytes(pdf.output())

# --- 2. 기존 계산기 로직 (그대로 유지) ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

with st.sidebar:
    st.header("📍 발전소 제원 설정")
    selected_region = st.selectbox("위치 선택", list(region_presets.keys()))
    preset = region_presets[selected_region]
    cap_mw = st.number_input("용량 (MW)", value=1.0)
    gen_time = st.slider("발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("고정가격 (원)", value=180)
    vgen_fee_rate = st.slider("수수료 (%)", 0, 30, 20) / 100

# 계산 결과
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = preset['mep'] + preset['cp'] + preset['map'] + preset['mwp'] - preset['imbp']
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)
owner_extra_profit_yr = annual_gen * owner_net_extra_unit
base_rev_yr = annual_gen * fixed_p

# 메인 UI
st.title("📑 V-GEN VPP 수익 분석")
st.metric("연간 추가 순수익 예상", f"{owner_extra_profit_yr/10000:,.0f} 만원")

# --- 3. PDF 다운로드 섹션 (강조) ---
st.divider()
st.subheader("📥 맞춤형 분석 리포트 생성")
st.info("입력하신 설정값을 바탕으로 'V-GEN 공식 수익 분석서'를 한글 PDF로 내려받을 수 있습니다.")

report_params = {
    "date": datetime.now().strftime("%Y년 %m월 %d일"),
    "region": selected_region,
    "cap": cap_mw,
    "gen_time": gen_time,
    "base_rev": base_rev_yr,
    "extra_profit": owner_extra_profit_yr
}

try:
    pdf_data = create_pdf(report_params)
    st.download_button(
        label="🚀 한글 리포트(PDF) 다운로드",
        data=pdf_data,
        file_name=f"브이젠_VPP_분석결과_{datetime.now().strftime('%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
except Exception as e:
    st.error(f"PDF 생성 중 오류: {e}")
