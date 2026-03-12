import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v3.8", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (26년 3월 준중앙 확대)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "제주도 (입찰제 안착 모델)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (모든 항목 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 및 제도 설정")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 5대 정산 항목")
    in_mep = st.number_input("1. 에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스 페널티(IMB)", value=conf['imb'])

    st.header("💰 4. 수수료 및 참여 비용")
    vgen_fee_rate = st.slider("VPP 수수료 (%)", 0, 50, 20)
    rtu_cost = st.number_input("RTU 설치비 (만원)", value=500)
    data_device_cost = st.number_input("신재생자료취득장치 (만원)", value=300)
    
    st.header("⚡ 5. VPP 기술 기여도")
    tech_level = st.select_slider("기술력 수준", options=["낮음", "보통", "높음"], value="높음")
    tech_multiplier = {"낮음": 0.7, "보통": 1.0, "높음": 1.3}
    adj_mep = in_mep * tech_multiplier[tech_level]

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_total_unit = adj_mep + in_cp + in_map + in_asp + in_imb
vpp_fee_unit = vpp_total_unit * (vgen_fee_rate / 100)
owner_net_extra_unit = vpp_total_unit - vpp_fee_unit

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * (fixed_p + owner_net_extra_unit)
net_increase = total_rev_vpp - total_rev_base
initial_investment = rtu_cost + data_device_cost

# --- 4. 고도화된 한글 PDF 생성 함수 (신규 항목 반영) ---
def generate_pro_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=12)
    else: return None
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(0, 50, 120); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=22)
    pdf.cell(190, 20, 'VPP 수익 분석 및 기술 기여 리포트', ln=True, align='C')
    pdf.set_font("NanumGothic", size=10); pdf.cell(190, 5, f"Issued by V-GEN | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    
    # 1. 발전소 현황
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "1. 분석 대상 발전소 및 기술 수준", "B", ln=True)
    pdf.set_font("NanumGothic", size=11); pdf.ln(3)
    pdf.cell(95, 8, f" • 설비 용량: {cap_mw} MW", ln=0); pdf.cell(95, 8, f" • 적용 기술 수준: {tech_level}", ln=1)
    pdf.cell(95, 8, f" • 초기 참여 비용: {initial_investment} 만원", ln=0); pdf.cell(95, 8, f" • VPP 운영 수수료: {vgen_fee_rate}%", ln=1)
    
    # 2. 수익 분석
    pdf.ln(10); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "2. 경제성 분석 결과 (연간 기준)", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=12)
    pdf.cell(80, 12, "기존 매전 수익", 1, 0, 'C'); pdf.cell(110, 12, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(0, 82, 156)
    pdf.cell(80, 12, "V-GEN VPP 수익", 1, 0, 'C'); pdf.cell(110, 12, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(200, 0, 0); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 15, f"연간 순수익 기대 증분: + {net_increase/10000:,.0f} 만원", ln=True, align='R')
    
    # 3. 정책 안내
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "3. 정책 변화 및 기술 기여 안내", "B", ln=True)
    pdf.set_font("NanumGothic", size=10); pdf.ln(3)
    pdf.multi_cell(190, 7, 
        "- 2026년 3월 준중앙급전 확대로 '예측정산금' 제도는 공식 일몰됩니다.\n"
        "- 브이젠의 고도화된 AI 기술은 MEP 수익을 최대화하고 IMB 페널티를 방어합니다.\n"
        "- 본 리포트의 수익은 정산 조정이 반영된 실질 순수익 프리미엄 기준입니다.", border=1)

    return pdf.output(dest='S')

# --- 5. 메인 UI (모든 섹션 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v3.8")

# [PDF 다운로드]
pdf_out = generate_pro_report()
if pdf_out:
    st.download_button(label="📄 전문가용 분석 리포트(PDF) 다운로드", data=bytes(pdf_out), file_name="VGEN_Pro_Report.pdf", mime="application/pdf", use_container_width=True)

# [핵심 수치]
m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 순수익 증분", f"{owner_net_extra_unit:.2f} 원/kWh", f"투자회수: {initial_investment/(net_increase/120000):.1f}개월")

st.divider()

# [중단: 차트 및 설명]
c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 정산 단가 및 수수료 구성 (Waterfall)")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP", "MAP", "ASP", "IMB", "VPP수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_asp, in_imb, -vpp_fee_unit, 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_asp}", f"{in_imb}", f"-{vpp_fee_unit:.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 상세 항목 및 비용")
    with st.expander("🛠️ 초기 참여 비용", expanded=True):
        st.write(f"총 투자비: {initial_investment} 만원 (RTU {rtu_cost} + 취득장치 {data_device_cost})")
    with st.expander("💸 VPP 운영 수수료"):
        st.write(f"총 정산금의 {vgen_fee_rate}% 차감 ({vpp_fee_unit:.2f} 원/kWh)")
    with st.expander("5대 정산 항목 정의"):
        st.caption("MEP, CP, MAP, ASP, IMB에 대한 상세 정의는 리포트를 참조하세요.")

# [하단: 인사이트 섹션]
st.divider()
st.subheader("🚀 2026년 전력시장 패러다임 변화")
st.info("육지 전역 재생에너지 입찰 제도 확대 시행에 따라 '예측정산금' 제도는 공식 일몰될 예정입니다.")
ic1, ic2 = st.columns(2)
with ic1:
    st.markdown("#### ✅ VPP 기술력이 수익을 결정합니다\n브이젠의 AI 기술은 MEP 수익을 극대화하고 페널티를 방어하는 핵심 자산입니다.")
with ic2:
    st.markdown("#### ✅ 실질적 수익 방어권 확보\n단순 수익을 넘어 출력제어 시 보상(MAP)을 받을 수 있는 유일한 권리를 확보하세요.")

# [최하단: 상세 테이블]
st.table(pd.DataFrame({
    "항목": ["연간 발전량", "VPP 참여 단가", "연간 총 매출액", "수익 증분"],
    "기본 방식": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))
