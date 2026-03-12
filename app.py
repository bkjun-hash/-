import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v2.7", layout="wide")

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3, "tag": "육지 준중앙"},
    "호남/육지 (입찰제 확대 시나리오)": {"cp": 11.0, "mep": 2.5, "map": 1.5, "asp": 0.8, "imb": -0.5, "tag": "육지 입찰제"},
    "제주도 (입찰제 안착)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8, "tag": "제주 입찰제"}
}

# --- 2. 사이드바 구성 ---
with st.sidebar:
    st.header("📍 1. 지역 선택")
    selected_region = st.selectbox("지역 및 제도 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 설정")
    in_mep = st.number_input("에너지(MEP)", value=conf['mep'])
    in_cp = st.number_input("용량(CP)", value=conf['cp'])
    in_map = st.number_input("기대보상(MAP)", value=conf['map'])
    in_asp = st.number_input("부가서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("페널티(IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 배분")
    owner_share = st.slider("사업주 배분 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_extra_total = in_mep + in_cp + in_map + in_asp + in_imb
owner_net_extra = vpp_extra_total * (owner_share / 100)
total_unit_vpp = fixed_p + owner_net_extra

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_increase = total_rev_vpp - total_rev_base

# --- 4. PDF 생성 함수 (전문가용 레이아웃) ---
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(0, 82, 156) # V-GEN Blue
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(190, 25, 'V-GEN VPP Profit Analysis Report', ln=True, align='C')
    
    # 발전소 제원
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.ln(20)
    pdf.cell(190, 10, f"1. Plant Information ({selected_region})", ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(95, 10, f"- Capacity: {cap_mw} MW", ln=0)
    pdf.cell(95, 10, f"- Daily Gen Time: {gen_time} hrs", ln=1)
    pdf.cell(190, 10, f"- Fixed Price (PPA/FIT): {fixed_p} KRW/kWh", ln=1)
    
    # 수익 비교 (핵심 섹션)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(190, 10, "2. Annual Revenue Comparison", ln=True)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(80, 12, "Classification", 1, 0, 'C', True)
    pdf.cell(110, 12, "Annual Total Revenue (Estimate)", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(80, 15, "Non-Participating (Base)", 1, 0, 'C')
    pdf.cell(110, 15, f"{total_rev_base/10000:,.0f} ten thousand KRW", 1, 1, 'C')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(80, 15, "V-GEN VPP Participating", 1, 0, 'C')
    pdf.cell(110, 15, f"{total_rev_vpp/10000:,.0f} ten thousand KRW", 1, 1, 'C')
    
    # 수익 차이 강조
    pdf.ln(5)
    pdf.set_text_color(246, 51, 102) # Highlight Red
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 15, f"Expected Net Profit Increase: + {net_increase/10000:,.0f} ten thousand KRW / Year", ln=True, align='R')
    
    # 정산금 상세
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(190, 10, "3. VPP Settlement Breakdown (per kWh)", ln=True)
    pdf.set_font('Arial', '', 11)
    items = [
        f"- Capacity Price (CP): {in_cp} KRW",
        f"- Energy Price (MEP): {in_mep} KRW",
        f"- MAP / ASP / IMB: {in_map + in_asp + in_imb:.1f} KRW",
        f"- Owner's Net Profit Rate: {owner_share}%"
    ]
    for item in items:
        pdf.cell(190, 8, item, ln=1)
        
    # 정책 인사이트
    pdf.ln(10)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(190, 8, " [ V-GEN Policy Insight ]", ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(180, 6, "By March 2026, renewable energy forecasting incentives are replaced by CP (Capacity Price). Participation in VPP is essential to hedge against curtailment risks and secure 11-22 KRW/kWh of additional revenue.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- 5. 메인 화면 ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")

# 대시보드 요약 (v2.6 기능 유지)
st.markdown(f"### 💰 연간 총 수익: {total_rev_vpp/10000:,.0f} 만원 (현행 대비 +{net_increase/10000:,.0f} 만원)")

# PDF 다운로드 버튼
pdf_data = generate_pdf()
st.download_button(
    label="📄 전문 분석 리포트(PDF) 다운로드",
    data=pdf_data,
    file_name=f"VGEN_VPP_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
    mime="application/pdf",
    use_container_width=True
)

st.divider()

# 워터폴 차트 및 상세 설명 (v2.6 유지)
c1, c2 = st.columns([1.5, 1])
with c1:
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "CP(용량)", "MEP(에너지)", "기타정산", "IMB(페널티)", "수수료", "최종단가"],
        measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        y = [fixed_p, in_cp, in_mep, in_map+in_asp, in_imb, -(vpp_extra_total*(vgen_fee_rate/100)), 0],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map+in_asp}", f"{in_imb}", f"-{(vpp_extra_total*(vgen_fee_rate/100)):.1f}", f"{total_unit_vpp:.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with c2:
    st.subheader("📋 정산금 항목 및 정책")
    st.markdown(f"""
    - **지역**: {selected_region}
    - **용량요금(CP)**: {in_cp}원 (안정적 확정 수익)
    - **보상(MAP)**: 출력제어 손실 방어액
    - **인사이트**: 2026년 3월 호남권 확대 시행에 따른 VPP 가입 필수화
    """)
