import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v4.3", layout="wide")

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

# --- 4. PDF 생성 함수 (참여 전후 및 인사이트 추가) ---
def generate_pro_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=11)
    else: return None
    
    # [Page 1] 표지 및 요약 (기본 유지)
    pdf.add_page()
    pdf.set_fill_color(0, 32, 96); pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=22)
    pdf.ln(15); pdf.cell(190, 10, "VPP 참여 전후 수익 비교 분석 리포트", ln=True, align='C')
    
    # [Page 1 내용] 1. 참여 전/후 핵심 지표 비교 (신규 섹션)
    pdf.set_text_color(0, 0, 0); pdf.ln(35); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "1. 입찰 시장 참여 전/후 수익 구조 비교", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=10)
    
    # 비교 테이블
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "구분 항목", 1, 0, 'C', True); pdf.cell(65, 10, "기존 매전 (VPP 미참여)", 1, 0, 'C', True); pdf.cell(65, 10, "브이젠 VPP (입찰 참여)", 1, 1, 'C', True)
    
    pdf.cell(60, 10, "주요 수익원", 1, 0, 'C'); pdf.cell(65, 10, "SMP + REC (또는 고정가)", 1, 0, 'C'); pdf.cell(65, 10, "고정가 + CP/MEP/MAP 인센티브", 1, 1, 'C')
    pdf.cell(60, 10, "예측정산금 수익", 1, 0, 'C'); pdf.cell(65, 10, "공식 일몰 (수익 소멸)", 1, 0, 'C'); pdf.cell(65, 10, "CP 및 MEP로 수익 대체", 1, 1, 'C')
    pdf.cell(60, 10, "출력제어 대응", 1, 0, 'C'); pdf.cell(65, 10, "수익 손실 발생 (0원)", 1, 0, 'C'); pdf.cell(65, 10, "기회비용 보상 (MAP 지급)", 1, 1, 'C')
    
    pdf.set_font("NanumGothic", size=12); pdf.ln(5); pdf.set_text_color(0, 32, 96)
    pdf.cell(190, 10, f"▶ VPP 참여 시 연간 순이익 증분: 약 {net_increase/10000:,.0f} 만원", ln=True)

    # [Page 1 내용] 2. 향후 시장 인사이트 (신규 섹션)
    pdf.ln(10); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "2. 향후 시장 변화 인사이트", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=10)
    
    insights = [
        "● 예측정산금 일몰 대응: 입찰 시장 미참여 시 기존 수익의 약 5~7%가 영구 소멸됩니다.",
        "● 중앙급전 자원화: 2026년 이후 단순 발전소가 아닌 '조절 가능한 자원'만이 계통 기여금을 보상받습니다.",
        "● VPP 기술 장벽: 입찰 오차 관리가 안 되는 파트너 선택 시 CP 수익보다 IMB 페널티가 커질 위험이 존재합니다.",
        "● 자산 가치 상승: 출력제어 보상권(MAP)을 확보한 발전소는 향후 매각/금융 시 더 높은 가치를 인정받습니다."
    ]
    for insight in insights:
        pdf.multi_cell(190, 8, insight)

    # [Page 2] 기존 상세 설명 유지 (생략 없이 통합)
    pdf.add_page(); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 15, "3. 기술 민감도 및 5대 정산 항목 상세", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=10)
    pdf.multi_cell(190, 7, f"선택하신 파트너({tech_option})의 기술력 적용 시, MEP 수익 가중치는 {tech_impact[tech_option]['mep_mult']}배로 적용되었습니다. 이는 정교한 AI 입찰을 통한 실시간 시장 가격 차액 정산을 의미합니다.")
    
    return pdf.output(dest='S')

# --- 5. 메인 UI (모든 항목 100% 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v4.3")

# PDF 버튼 (항목 강화된 버전)
pdf_data = generate_pro_report()
if pdf_data:
    st.download_button(label="📄 [참여 전후 비교/인사이트 포함] 심층 분석 리포트 다운로드", data=bytes(pdf_data), file_name=f"VGEN_Comparison_Report.pdf", mime="application/pdf", use_container_width=True)

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 순수익 증분", f"{owner_net_extra_unit:.2f} 원/kWh", f"회수기간: {initial_investment/(net_increase/120000):.1f}개월")

st.divider()

c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 기술 격차에 따른 정산 단가 구성 (Waterfall)")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP", "MAP", "ASP", "IMB", "VPP수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_asp, adj_imb, -vpp_fee_unit, 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_asp}", f"{adj_imb:.1f}", f"-{vpp_fee_unit:.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 상세 항목 및 기술 분석")
    with st.expander("⚡ 파트너사 기술력 분석", expanded=True):
        st.write(f"**현재 설정:** {tech_option}")
        st.write(f"- MEP 수익 가중치: **{tech_impact[tech_option]['mep_mult']}배**")
        st.write(f"- IMB 페널티 방어: **{tech_impact[tech_option]['imb_mult']}배**")
    with st.expander("🛠️ 초기 투자 및 수수료"):
        st.write(f"- 초기 투자비: {initial_investment} 만원")
        st.write(f"- VPP 운영 수수료: {vgen_fee_rate}%")

st.divider()
st.subheader("🚀 전력시장 패러다임 변화 안내")
st.warning("⚠️ 육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다.")

# 하단 테이블 (유지)
st.table(pd.DataFrame({
    "구분": ["연간 발전량", "VPP 정산 단가", "연간 총 매출", "수익 증분"],
    "기존 매전 방식": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP 시스템": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))
