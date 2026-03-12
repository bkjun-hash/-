import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import io
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기", layout="wide")

# --- 폰트 설정 (나눔고딕이 프로젝트 폴더 내 fonts/ 폴더에 있다고 가정) ---
# 파일 경로 예: './fonts/NanumGothic.ttf' 또는 './NanumGothic.ttf'
FONT_PATH = "NanumGothic.ttf" 

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "호남/육지 (입찰제 확대 시나리오)": {"cp": 11.0, "mep": 2.5, "map": 1.5, "asp": 0.8, "imb": -0.5},
    "제주도 (입찰제 안착)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (기본 항목 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 선택")
    selected_region = st.selectbox("지역 및 제도 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 상세 설정")
    in_mep = st.number_input("1. 에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스(IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 배분 설정")
    owner_share = st.slider("사업주 수익 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_extra_unit = in_mep + in_cp + in_map + in_asp + in_imb
owner_net_extra = vpp_extra_total_unit = vpp_extra_unit * (owner_share / 100)
total_unit_vpp = fixed_p + owner_net_extra

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_increase = total_rev_vpp - total_rev_base

# --- 4. 한글 PDF 생성 함수 ---
def generate_korean_pdf():
    pdf = FPDF()
    # 유니코드 폰트 추가 (나눔고딕)
    try:
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=12)
    except:
        # 폰트 로드 실패 시 에러 메시지를 PDF에 출력하거나 예외 처리
        pass

    pdf.add_page()
    
    # [헤더 섹션]
    pdf.set_fill_color(0, 82, 156)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("NanumGothic", size=22)
    pdf.cell(190, 30, 'V-GEN VPP 수익 분석 리포트', ln=True, align='C')
    
    # [발전소 정보]
    pdf.set_text_color(0, 0, 0)
    pdf.ln(15)
    pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 10, f"1. 발전소 분석 제원 ({selected_region})", ln=True)
    pdf.set_font("NanumGothic", size=12)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.cell(95, 10, f"● 설비 용량: {cap_mw} MW", ln=0)
    pdf.cell(95, 10, f"● 일평균 발전시간: {gen_time} 시간", ln=1)
    pdf.cell(190, 10, f"● 현재 고정단가: {fixed_p} 원/kWh", ln=1)
    
    # [수익 비교 - 미참여 vs 참여]
    pdf.ln(10)
    pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 10, "2. 참여 여부에 따른 연간 수익 비교", ln=True)
    
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("NanumGothic", size=12)
    pdf.cell(80, 12, "구분", 1, 0, 'C', True)
    pdf.cell(110, 12, "연간 총 수익 (예상)", 1, 1, 'C', True)
    
    pdf.cell(80, 15, "VPP 미참여 (단순 매전)", 1, 0, 'C')
    pdf.cell(110, 15, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    
    pdf.set_font("NanumGothic", size=13)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(80, 15, "V-GEN VPP 참여 시", 1, 0, 'C')
    pdf.cell(110, 15, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    
    # 수익 차이 극대화 강조
    pdf.ln(5)
    pdf.set_text_color(246, 51, 102)
    pdf.set_font("NanumGothic", size=18)
    pdf.cell(190, 20, f"연간 순수익 증대액: + {net_increase/10000:,.0f} 만원", ln=True, align='R')
    
    # [정산금 상세 명세]
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "3. VPP 정산금 상세 명세 (단가 기준)", ln=True)
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(190, 8, f"- 용량 정산금(CP): {in_cp}원", ln=1)
    pdf.cell(190, 8, f"- 에너지 정산금(MEP): {in_mep}원", ln=1)
    pdf.cell(190, 8, f"- 기타 정산 및 보상(MAP/ASP/IMB): {in_map + in_asp + in_imb:.1f}원", ln=1)
    pdf.cell(190, 8, f"- 사업주 수익 배분 비율: {owner_share}%", ln=1)

    # [정책 인사이트]
    pdf.ln(10)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, pdf.get_y(), 190, 30, 'F')
    pdf.set_font("NanumGothic", size=10)
    pdf.cell(190, 8, " [ V-GEN 전문가 분석 ]", ln=1)
    pdf.multi_cell(180, 6, " 2026년 3월 호남/육지권 준중앙급전 시행으로 기존 예측정산금은 일몰되었습니다. \n 이제 CP(11원) 확보와 출력제어 리스크를 방어하는 MAP 수익이 사업의 핵심 지표입니다.")

    return pdf.output(dest='S').encode('latin-1')

# --- 5. 메인 UI ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")

# PDF 다운로드 섹션
try:
    pdf_bytes = generate_korean_pdf()
    st.download_button(
        label="📄 한글 분석 리포트(PDF) 다운로드",
        data=pdf_bytes,
        file_name=f"브이젠_수익분석_리포트_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
except Exception as e:
    st.error(f"폰트 파일 확인 필요: {e}")

st.divider()

# 대시보드 그래프 및 상세 명세 (기존 v2.6~2.7 기능 유지)
# ... [워터폴 차트 및 상세 설명 코드 생략 - 동일함] ...
