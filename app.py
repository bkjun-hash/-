import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v3.9", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (26년 3월 준중앙 확대)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "제주도 (입찰제 안착 모델)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (기존 항목 유지 + 기술 민감도 추가) ---
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

    st.header("⚡ 4. VPP 기술 기여 민감도")
    # 기술력에 따른 변동성 추가
    tech_level = st.select_slider(
        "VPP 운영사 기술 수준",
        options=["낮음", "보통", "높음"],
        value="높음",
        help="기술력이 높을수록 MEP 정산 효율이 상승하고 IMB 페널티가 방어됩니다."
    )
    
    # 기술력 매커니즘: MEP 가중치 및 IMB 방어율
    tech_impact = {
        "낮음": {"mep_mult": 0.6, "imb_mult": 1.5, "desc": "입찰 오차 빈번, 수익 누수 발생"},
        "보통": {"mep_mult": 1.0, "imb_mult": 1.0, "desc": "시장 평균 수준의 정산 효율"},
        "높음": {"mep_mult": 1.4, "imb_mult": 0.5, "desc": "AI 최적 입찰로 수익 극대화"}
    }
    
    adj_mep = in_mep * tech_impact[tech_level]["mep_mult"]
    adj_imb = in_imb * tech_impact[tech_level]["imb_mult"]

    st.header("💰 5. 참여 비용 및 수수료")
    vgen_fee_rate = st.slider("VPP 수수료 (%)", 0, 50, 20)
    rtu_cost = st.number_input("RTU/단말기 설치비 (만원)", value=500)
    data_device_cost = st.number_input("신재생자료취득장치 (만원)", value=300)

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
# 기술 기여도가 반영된 총 정산금
vpp_total_unit = adj_mep + in_cp + in_map + in_asp + adj_imb
vpp_fee_unit = vpp_total_unit * (vgen_fee_rate / 100)
owner_net_extra_unit = vpp_total_unit - vpp_fee_unit

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * (fixed_p + owner_net_extra_unit)
net_increase = total_rev_vpp - total_rev_base
initial_investment = rtu_cost + data_device_cost

# --- 4. 고도화된 한글 PDF 생성 (민감도 내용 포함) ---
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
    pdf.cell(190, 20, 'VPP 기술 기여도 및 수익 민감도 분석서', ln=True, align='C')
    pdf.set_font("NanumGothic", size=10); pdf.cell(190, 5, f"Issued by V-GEN | 분석 모델: {selected_region}", ln=True, align='C')
    
    # 1. 기술 민감도 분석
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, f"■ VPP 운영 기술 수준 분석: [{tech_level}]", "B", ln=True)
    pdf.set_font("NanumGothic", size=11); pdf.ln(3)
    pdf.multi_cell(190, 7, f"선택하신 기술 수준({tech_level}) 적용 시, 에너지 정산금(MEP)은 기본 대비 {tech_impact[tech_level]['mep_mult']}배 조정되며, 임밸런스 페널티는 {tech_impact[tech_level]['imb_mult']}배 수준으로 관리됩니다. 이는 수익 최적화 알고리즘의 정밀도 차이를 반영한 결과입니다.")
    
    # 2. 경제성 요약
    pdf.ln(10); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "■ 연간 기대 수익 및 비용 회수", "B", ln=True)
    pdf.set_font("NanumGothic", size=12); pdf.ln(5)
    pdf.cell(80, 10, "기존 매전 방식", 1, 0, 'C'); pdf.cell(110, 10, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(0, 70, 150)
    pdf.cell(80, 10, "V-GEN VPP 참여", 1, 0, 'C'); pdf.cell(110, 10, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    
    pdf.ln(5); pdf.set_text_color(200, 0, 0); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 15, f"연간 순수익 증분: + {net_increase/10000:,.0f} 만원", ln=True, align='R')
    
    # 3. 전문가 제언
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=13)
    pdf.cell(190, 10, "■ 전문가 제언", ln=True)
    pdf.set_font("NanumGothic", size=10)
    pdf.multi_cell(190, 6, "2026년 3월 준중앙급전 확대 이후, 예측정산금 제도는 공식 일몰됩니다. 단순히 참여하는 것을 넘어, 높은 기술력을 가진 VPP 파트너를 선택하여 MEP 수익을 극대화하고 페널티를 방어하는 것이 자산 관리의 핵심입니다.")

    return pdf.output(dest='S')

# --- 5. 메인 UI (항목 유지 + 시각화) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v3.9")

# [상단: PDF 및 메트릭]
pdf_out = generate_pro_report()
if pdf_out:
    st.download_button(label="📄 전문가용 분석 리포트(PDF) 다운로드", data=bytes(pdf_out), file_name="VGEN_Tech_Analysis.pdf", mime="application/pdf", use_container_width=True)

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 순수익 증분", f"{owner_net_extra_unit:.2f} 원/kWh", f"기술수준: {tech_level}")

st.divider()

# [중단: Waterfall 및 비용/기술 설명]
c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 정산 단가 구성 (기술 민감도 반영)")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP(기술반영)", "MAP", "ASP", "IMB(기술반영)", "VPP수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_asp, adj_imb, -vpp_fee_unit, 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_asp}", f"{adj_imb:.1f}", f"-{vpp_fee_unit:.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 참여 비용 및 기술 기여")
    with st.expander("🛠️ 초기 참여 비용 (CAPEX)", expanded=True):
        st.write(f"- 총 투자비: {initial_investment} 만원")
        st.caption(f"RTU {rtu_cost}만원 + 취득장치 {data_device_cost}만원")
    with st.expander("⚡ VPP 기술 기여 상세"):
        st.write(f"**상태:** {tech_impact[tech_level]['desc']}")
        st.write(f"- MEP 수익 효율: {tech_impact[tech_level]['mep_mult']}배")
        st.write(f"- IMB 페널티 방어: {tech_impact[tech_level]['imb_mult']}배")

# [하단: 정책 및 인사이트]
st.divider()
st.subheader("🚀 2026년 전력시장 패러다임 변화")
st.info("💡 2026년 3월부터 육지 전역 준중앙급전 확대 시행에 따라 '예측정산금' 제도는 공식 일몰됩니다.")
ic1, ic2 = st.columns(2)
with ic1:
    st.markdown("#### ✅ VPP 기술력이 수익의 격차를 만듭니다")
    st.write("단순 참여가 아닌 '최적 입찰'이 중요합니다. 브이젠의 기술력은 MEP를 높이고 IMB를 낮추는 핵심 동력입니다.")
    
with ic2:
    st.markdown("#### ✅ 투자 회수 및 수익 방어권")
    st.write(f"현재 시나리오 기준 초기 투자비 회수 기간은 약 **{initial_investment/(net_increase/120000):.1f}개월**입니다.")
    

# [최하단: 테이블]
st.table(pd.DataFrame({
    "항목": ["연간 발전량", "VPP 참여 단가", "연간 총 매출액", "순이익 증분"],
    "기본 방식": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "V-GEN VPP": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))
