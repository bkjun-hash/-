import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v4.0", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (입찰제 확대 모델)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "제주도 (입찰제 안착 모델)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (모든 항목 유지 + 가중치 드라마틱 조정) ---
with st.sidebar:
    st.header("📍 1. 지역 및 제도 설정")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 5대 정산 항목 (Base)")
    in_mep = st.number_input("1. 에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스 페널티(IMB)", value=conf['imb'])

    st.header("⚡ 4. VPP 기술력 민감도 (수익 격차)")
    # 가중치 드라마틱 조정: 기술력 없는 회사(0.4) vs 보통(0.8) vs 브이젠(1.6)
    tech_option = st.radio(
        "VPP 파트너 선택",
        options=["기술력 없는 회사", "보통 수준의 회사", "브이젠 (V-GEN)"],
        index=2,
        help="브이젠은 AI 최적 입찰을 통해 MEP 수익을 극대화합니다."
    )
    
    tech_impact = {
        "기술력 없는 회사": {"mep_mult": 0.4, "imb_mult": 2.0, "label": "수익 누수 심각"},
        "보통 수준의 회사": {"mep_mult": 0.8, "imb_mult": 1.2, "label": "시장 평균 미달"},
        "브이젠 (V-GEN)": {"mep_mult": 1.6, "imb_mult": 0.4, "label": "수익 극대화 달성"}
    }
    
    adj_mep = in_mep * tech_impact[tech_option]["mep_mult"]
    adj_imb = in_imb * tech_impact[tech_option]["imb_mult"]

    st.header("💰 5. 참여 비용 및 수수료")
    vgen_fee_rate = st.slider("VPP 수수료 (%)", 0, 50, 20)
    rtu_cost = st.number_input("RTU 설치비 (만원)", value=150)
    data_device_cost = st.number_input("신재생자료취득장치 (만원)", value=150)

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_total_unit = adj_mep + in_cp + in_map + in_asp + adj_imb
vpp_fee_unit = vpp_total_unit * (vgen_fee_rate / 100)
owner_net_extra_unit = vpp_total_unit - vpp_fee_unit

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * (fixed_p + owner_net_extra_unit)
net_increase = total_rev_vpp - total_rev_base
initial_investment = rtu_cost + data_device_cost

# --- 4. 한글 PDF 생성 ---
def generate_pro_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=12)
    else: return None
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(0, 40, 100); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=22)
    pdf.cell(190, 20, 'VPP 기술 격차 분석 및 경제성 리포트', ln=True, align='C')
    pdf.set_font("NanumGothic", size=10); pdf.cell(190, 5, f"Issued by V-GEN | 파트너: {tech_option}", ln=True, align='C')
    
    # 분석 결과
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, f"■ [{tech_option}] 적용 시 수익성 결과", "B", ln=True)
    pdf.set_font("NanumGothic", size=11); pdf.ln(5)
    pdf.cell(80, 10, "기존 매전 수익", 1, 0, 'C'); pdf.cell(110, 10, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(0, 70, 150)
    pdf.cell(80, 10, "브이젠 VPP 수익", 1, 0, 'C'); pdf.cell(110, 10, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    
    # 정책 문구 수정 반영
    pdf.ln(10); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=12)
    pdf.set_fill_color(240, 240, 240)
    pdf.multi_cell(190, 10, "육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다.", border=1, fill=True, align='C')

    return pdf.output(dest='S')

# --- 5. 메인 UI ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v4.0")

# PDF 버튼
pdf_out = generate_pro_report()
if pdf_out:
    st.download_button(label="📄 전문가용 분석 리포트(PDF) 다운로드", data=bytes(pdf_out), file_name="VGEN_Economic_Report.pdf", mime="application/pdf", use_container_width=True)

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 순수익 증분", f"{owner_net_extra_unit:.2f} 원/kWh", f"투자회수: {initial_investment/(net_increase/120000):.1f}개월")

st.divider()

c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 기술 격차에 따른 정산 단가 구성")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP(기술반영)", "MAP", "ASP", "IMB(기술반영)", "VPP수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_asp, adj_imb, -vpp_fee_unit, 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_asp}", f"{adj_imb:.1f}", f"-{vpp_fee_unit:.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 정산 및 비용 상세")
    with st.expander("⚡ 기술력 기여도 분석", expanded=True):
        st.write(f"**선택:** {tech_option}")
        st.write(f"- MEP 수익 효율: **{tech_impact[tech_option]['mep_mult']}배**")
        st.write(f"- IMB 페널티 방어: **{tech_impact[tech_option]['imb_mult']}배**")
    with st.expander("🛠️ 초기 참여 비용"):
        st.write(f"총 투자비: {initial_investment} 만원 (RTU 등)")

st.divider()
st.subheader("🚀 전력시장 패러다임 변화 안내")
st.warning("⚠️ 육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다.")

# 하단 요약 테이블
st.table(pd.DataFrame({
    "구분": ["연간 발전량", "적용 단가", "연간 총 매출", "비고"],
    "기존 매전": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "V-GEN VPP": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", "최적 입찰 반영"]
}))
