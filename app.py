import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기", layout="wide")

# --- PDF 생성 함수 (수정됨) ---
def create_pdf(data):
    # FPDF 객체 생성
    pdf = FPDF()
    pdf.add_page()
    
    # 제목 (Arial은 기본 내장 폰트로 영문/숫자만 가능)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 123, 255) # 브이젠 블루 컬러
    pdf.cell(190, 20, "V-GEN VPP Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    # 기본 정보 섹션
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, f"Analysis Summary", ln=True)
    pdf.line(10, 45, 200, 45) # 구분선
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(50, 10, f"Date: {data['date']}")
    pdf.cell(70, 10, f"Region: {data['region_eng']}")
    pdf.cell(70, 10, f"Capacity: {data['cap']} MW", ln=True)
    pdf.ln(5)
    
    # 수익 분석 섹션
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "1. Financial Forecast (Annual)", ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(100, 8, f"- Base Revenue (Estimated):")
    pdf.cell(90, 8, f"{data['base_rev']:,.0f} KRW", ln=True, align='R')
    
    pdf.set_text_color(0, 123, 255) # 추가 수익 강조
    pdf.cell(100, 8, f"- V-GEN VPP Extra Profit:")
    pdf.cell(90, 8, f"+ {data['extra_profit']:,.0f} KRW", ln=True, align='R')
    
    pdf.set_text_color(0, 0, 0)
    pdf.line(110, 85, 200, 85)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 12, f"Total Forecasted Revenue:")
    pdf.cell(90, 12, f"{data['base_rev'] + data['extra_profit']:,.0f} KRW", ln=True, align='R')
    pdf.ln(10)

    # 면책 조항
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(190, 5, "Disclaimer: This report is a simulation based on V-GEN's algorithm and KPX rules. Actual settlement amounts may vary depending on actual generation and real-time market conditions.")
    
    # [수정 포인트] 최신 fpdf2에서는 output()이 bytes를 직접 반환합니다.
    return pdf.output()

# --- 기존 시뮬레이터 로직 ---
# (중략 - 기존의 지역 설정 및 계산 로직은 동일하게 유지)
# ... [기존 코드의 Sidebar 및 계산 부분 입력] ...

# 예시 데이터 셋팅 (에러 방지용)
region_eng_map = {
    "제주도 (출력제어 매우 높음)": "Jeju",
    "전라도/호남 (출력제어 높음)": "Honam",
    "경상도/영남 (출력제어 보통)": "Yeongnam",
    "기타 육지 (출력제어 낮음)": "Others"
}

# --- PDF 다운로드 버튼 섹션 ---
st.markdown("---")
st.subheader("📥 리포트 다운로드 (PDF)")

# PDF에 보낼 데이터 정리
report_params = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "region_eng": region_eng_map.get(selected_region, "Others"),
    "cap": cap_mw,
    "base_rev": annual_gen * fixed_p,
    "extra_profit": owner_extra_profit_yr
}

# PDF 생성 시도
try:
    pdf_out = create_pdf(report_params)
    
    st.download_button(
        label="📩 수익 분석 리포트 다운로드 (English Ver.)",
        data=pdf_out,
        file_name=f"VGEN_VPP_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
    st.caption("※ 현재 리포트는 시스템 폰트 제약으로 영문 위주로 생성됩니다.")

except Exception as e:
    st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")
    st.info("관리자에게 문의하거나 잠시 후 다시 시도해 주세요.")
