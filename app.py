import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v4.5", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 (유지) ---
region_config = {
    "호남/육지 (입찰제 확대 모델)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "제주도 (입찰제 안착 모델)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (기존 기능 100% 유지) ---
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

    st.header("⚡ 4. VPP 기술력 민감도")
    tech_option = st.radio("VPP 파트너 선택", options=["기술력 없는 회사", "보통 수준의 회사", "브이젠 (V-GEN)"], index=2)
    
    tech_impact = {
        "기술력 없는 회사": {"mep_mult": 0.4, "imb_mult": 2.0},
        "보통 수준의 회사": {"mep_mult": 0.8, "imb_mult": 1.2},
        "브이젠 (V-GEN)": {"mep_mult": 1.6, "imb_mult": 0.4}
    }
    
    adj_mep = in_mep * tech_impact[tech_option]["mep_mult"]
    adj_imb = in_imb * tech_impact[tech_option]["imb_mult"]

    st.header("💰 5. 참여 비용 및 수수료")
    vgen_fee_rate = st.slider("VPP 수수료 (%)", 0, 50, 20)
    rtu_cost = st.number_input("RTU 설치비 (만원)", value=500)
    data_device_cost = st.number_input("신재생자료취득장치 (만원)", value=300)

# --- 3. 수익 계산 로직 (유지) ---
annual_gen = cap_mw * 1000 * gen_time * 365
fee_factor = (1 - (vgen_fee_rate / 100))
net_items = {
    "용량정산금(CP)": in_cp * fee_factor,
    "에너지정산금(MEP)": adj_mep * fee_factor,
    "기대이익보상(MAP)": in_map * fee_factor,
    "부가서비스(ASP)": in_asp * fee_factor,
    "임밸런스(IMB)": adj_imb * fee_factor
}

owner_net_extra_unit = sum(net_items.values())
total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * (fixed_p + owner_net_extra_unit)
net_increase = total_rev_vpp - total_rev_base
initial_investment = rtu_cost + data_device_cost

# --- 4. PDF 생성 함수 (총 수익 및 브이젠 강점 섹션 보강) ---
def generate_pro_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=11)
    else: return None
    
    # [Page 1] 상세 항목 및 비교 (기존 유지)
    pdf.add_page()
    pdf.set_fill_color(0, 32, 96); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=22)
    pdf.ln(12); pdf.cell(190, 10, "VPP 자산 가치 극대화 전략 리포트", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.ln(30); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "1. 항목별 연간 기대 순수익 상세", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=10)
    
    # 항목 테이블
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(60, 10, "정산 항목", 1, 0, 'C', True); pdf.cell(65, 10, "단가 (원/kWh)", 1, 0, 'C', True); pdf.cell(65, 10, "연간 예상 순수익", 1, 1, 'C', True)
    for item, unit in net_items.items():
        pdf.cell(60, 10, item, 1, 0, 'C')
        pdf.cell(65, 10, f"{unit:.2f} 원", 1, 0, 'C')
        pdf.cell(65, 10, f"{(unit * annual_gen)/10000:,.1f} 만원", 1, 1, 'C')
    
    # [신규 추가] 총 수익 강조 및 클로징 섹션
    pdf.ln(10); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "2. 결론: 왜 브이젠(V-GEN)과 함께해야 하는가?", "B", ln=True)
    pdf.ln(5)
    
    # 강점 1: 출력제어 대응
    pdf.set_font("NanumGothic", size=12); pdf.set_text_color(0, 50, 150)
    pdf.cell(190, 10, "① 출력제어 리스크를 수익 기회로 전환 (MAP 대응)", ln=True)
    pdf.set_font("NanumGothic", size=10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(190, 7, "단순 매전 시 출력제어는 곧 100% 수익 손실을 의미합니다. 브이젠 VPP는 출력제어 발생 시에도 기대이익보상(MAP)을 통해 손실을 방어하며, 이는 고도화된 계통 유연성 자원으로서의 권리입니다.")
    
    # 강점 2: AI 입찰 기술
    pdf.ln(3); pdf.set_font("NanumGothic", size=12); pdf.set_text_color(0, 50, 150)
    pdf.cell(190, 10, "② 초격차 AI 입찰 엔진을 통한 수익 극대화", ln=True)
    pdf.set_font("NanumGothic", size=10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(190, 7, "2026년 입찰 시장의 핵심은 'MEP(에너지정산금)'입니다. 브이젠의 독보적인 AI 예측 알고리즘은 오차율을 최소화하여 페널티(IMB)를 방어하고, 최적 가격 구간 입찰을 통해 타사 대비 최대 2배 이상의 MEP 수익을 보장합니다.")

    # 하단 총 수익 박스
    pdf.ln(10); pdf.set_fill_color(0, 32, 96); pdf.rect(10, pdf.get_y(), 190, 30, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=16)
    pdf.set_y(pdf.get_y() + 10)
    pdf.cell(190, 10, f"총 예상 연간 매출액: {total_rev_vpp/10000:,.0f} 만원", ln=True, align='C')

    return pdf.output(dest='S')

# --- 5. 메인 UI (전 기능 100% 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v4.5")

# PDF 버튼
pdf_data = generate_pro_report()
if pdf_data:
    st.download_button(label="📄 [전략 및 총 수익 강조] 최종 분석 리포트 다운로드", data=bytes(pdf_data), file_name=f"VGEN_Strategic_Final_Report.pdf", mime="application/pdf", use_container_width=True)

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 순수익 증분", f"{owner_net_extra_unit:.2f} 원/kWh", f"회수기간: {initial_investment/(net_increase/120000):.1f}개월")

st.divider()

c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 기술 격차에 따른 정산 단가 구성")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP", "MAP", "ASP", "IMB", "VPP수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_asp, adj_imb, -(owner_net_extra_unit/(1-(vgen_fee_rate/100))*(vgen_fee_rate/100)), 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_asp}", f"{adj_imb:.1f}", f"-{(owner_net_extra_unit/(1-(vgen_fee_rate/100))*(vgen_fee_rate/100)):.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 실시간 기술 민감도 및 가중치")
    with st.expander("⚡ 파트너 선택에 따른 수익 가중치", expanded=True):
        st.write(f"**현재 설정:** {tech_option}")
        st.write(f"- MEP 기여도: **{tech_impact[tech_option]['mep_mult']}배**")
        st.write(f"- IMB 방어력: **{tech_impact[tech_option]['imb_mult']}배**")
    with st.expander("🛠️ 비용 및 정책 가이드"):
        st.write(f"- 초기 투자비: {initial_investment} 만원")
        st.write(f"- 제도 변화: 예측정산금 공식 일몰 예정")

st.divider()
st.subheader("🚀 전력시장 패러다임 변화 안내")
st.warning("⚠️ 육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다.")

# 하단 요약 테이블
st.table(pd.DataFrame({
    "구분": ["연간 발전량", "VPP 정산 단가", "연간 총 매출액", "순이익 증분"],
    "기본 매전": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))
