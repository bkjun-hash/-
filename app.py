import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v4.2", layout="wide")

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

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_total_unit = adj_mep + in_cp + in_map + in_asp + adj_imb
vpp_fee_unit = vpp_total_unit * (vgen_fee_rate / 100)
owner_net_extra_unit = vpp_total_unit - vpp_fee_unit

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * (fixed_p + owner_net_extra_unit)
net_increase = total_rev_vpp - total_rev_base
initial_investment = rtu_cost + data_device_cost

# --- 4. 심층 PDF 리포트 생성 함수 (대폭 강화) ---
def generate_advanced_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=11)
    else: return None
    
    # [Page 1] 전략 리포트 표지 및 요약
    pdf.add_page()
    pdf.set_fill_color(0, 51, 102); pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=28)
    pdf.ln(60); pdf.cell(190, 20, "VPP 수익 최적화", ln=True, align='C')
    pdf.cell(190, 20, "마스터 컨설팅 보고서", ln=True, align='C')
    pdf.ln(10); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, f"대상: {cap_mw}MW급 재생에너지 발전소", ln=True, align='C')
    pdf.ln(80); pdf.set_font("NanumGothic", size=12)
    pdf.cell(190, 10, f"발행일: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.cell(190, 10, "발행처: (주)브이젠 (V-GEN)", ln=True, align='C')

    # [Page 2] 상세 수익 분석 및 타사 비교
    pdf.add_page(); pdf.set_text_color(0, 0, 0)
    pdf.set_font("NanumGothic", size=16); pdf.cell(190, 15, "1. 기술력 기반 수익 민감도 분석", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=11)
    pdf.multi_cell(190, 7, f"선택 파트너: {tech_option}\n브이젠의 AI 최적 입찰 알고리즘은 에너지정산금(MEP) 수익을 극대화(기본 대비 1.6배)하고, 예측 오차에 따른 페널티(IMB)를 최소화(기본 대비 0.4배)하여 타사 대비 압도적인 수익 증분을 실현합니다.")
    
    # 수익 비교 테이블
    pdf.ln(5); pdf.set_fill_color(220, 230, 241)
    pdf.cell(50, 12, "비교 항목", 1, 0, 'C', True); pdf.cell(45, 12, "기술력 미흡", 1, 0, 'C', True)
    pdf.cell(45, 12, "일반 VPP", 1, 0, 'C', True); pdf.cell(50, 12, "브이젠 (V-GEN)", 1, 1, 'C', True)
    
    pdf.cell(50, 12, "연간 예상 매출", 1, 0, 'C')
    pdf.cell(45, 12, "평균 이하", 1, 0, 'C'); pdf.cell(45, 12, "평균 수준", 1, 0, 'C')
    pdf.set_text_color(0, 51, 153); pdf.cell(50, 12, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C'); pdf.set_text_color(0, 0, 0)
    
    # 5대 정산금 기여도 설명
    pdf.ln(10); pdf.set_font("NanumGothic", size=16); pdf.cell(190, 15, "2. 5대 정산 항목별 수익 기여도", "B", ln=True)
    pdf.set_font("NanumGothic", size=10); pdf.ln(3)
    items_desc = [
        (f"에너지 정산금(MEP): {adj_mep:.2f}원", "실시간 시장가 차액 정산. 브이젠 기술력으로 수익 극대화"),
        (f"용량 정산금(CP): {in_cp:.2f}원", "공급 가능 용량에 대한 보상. 2026년 이후 핵심 수익원"),
        (f"출력제어 보상(MAP): {in_map:.2f}원", "출력제어 발생 시 손실을 보전하는 안전장치"),
        (f"부가 서비스(ASP): {in_asp:.2f}원", "계통 안정화 기여에 따른 인센티브"),
        (f"임밸런스(IMB): {adj_imb:.2f}원", "예측 오차 차감액. 브이젠 알고리즘으로 최소화")
    ]
    for title, desc in items_desc:
        pdf.set_font("NanumGothic", size=11); pdf.cell(60, 10, f" • {title}", ln=0)
        pdf.set_font("NanumGothic", size=10); pdf.cell(130, 10, f": {desc}", ln=1)

    # 정책 가이드 (하단 고정)
    pdf.ln(10); pdf.set_fill_color(255, 235, 235); pdf.rect(10, pdf.get_y(), 190, 30, 'F')
    pdf.set_font("NanumGothic", size=11); pdf.set_text_color(200, 0, 0)
    pdf.multi_cell(190, 10, "\n[정책 알림] 육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다. 선제적 대응이 필수적입니다.", align='C')

    return pdf.output(dest='S')

# --- 5. 메인 UI (모든 항목 및 로직 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v4.2")

# PDF 버튼
pdf_data = generate_advanced_report()
if pdf_data:
    st.download_button(label="📄 심층 분석 컨설팅 리포트(PDF) 다운로드", data=bytes(pdf_data), file_name=f"VGEN_Consulting_Report_{tech_option}.pdf", mime="application/pdf", use_container_width=True)

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 순수익 증분", f"{owner_net_extra_unit:.2f} 원/kWh", f"회수기간: {initial_investment/(net_increase/120000):.1f}개월")

st.divider()

c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 기술 격차에 따른 정산 단가 구성")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP(반영)", "MAP", "ASP", "IMB(반영)", "VPP수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_asp, adj_imb, -vpp_fee_unit, 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_asp}", f"{adj_imb:.1f}", f"-{vpp_fee_unit:.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 정산 및 비용 상세")
    with st.expander("⚡ 파트너사 기술력 분석", expanded=True):
        st.write(f"**현재 설정:** {tech_option}")
        st.write(f"- MEP 수익 효율: **{tech_impact[tech_option]['mep_mult']}배**")
        st.write(f"- IMB 페널티 관리: **{tech_impact[tech_option]['imb_mult']}배**")
    with st.expander("🛠️ 초기 투자비 (CAPEX)"):
        st.write(f"- 총 {initial_investment} 만원 (RTU 및 단말기 포함)")

st.divider()
st.subheader("🚀 전력시장 패러다임 변화 안내")
st.warning("⚠️ 육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다.")

# 하단 테이블 (유지)
st.table(pd.DataFrame({
    "구분": ["연간 발전량", "VPP 정산 단가", "연간 총 매출", "수익 증분"],
    "기존 매전 방식": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP 시스템": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))
