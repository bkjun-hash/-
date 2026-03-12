import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import io
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v3.4", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 (참고자료 기반 최신화) ---
region_config = {
    "호남/육지 (26년 3월 준중앙 확대)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "육지 (입찰제 전면 시행 시나리오)": {"cp": 11.0, "mep": 2.5, "map": 1.5, "asp": 0.8, "imb": -0.5},
    "제주도 (입찰제 안착 모델)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (기능 100% 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 및 제도 설정")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 5대 정산 항목 설정")
    in_mep = st.number_input("1. 에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스 페널티(IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 배분 설정")
    owner_share = st.slider("사업주 수익 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_extra_total = in_mep + in_cp + in_map + in_asp + in_imb
owner_net_extra = vpp_extra_total * (owner_share / 100)
total_unit_vpp = fixed_p + owner_net_extra

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_increase = total_rev_vpp - total_rev_base

# --- 4. 전문 한글 PDF 생성 (인사이트 강화형) ---
def generate_final_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=12)
    else: return None
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(0, 40, 100); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=22)
    pdf.cell(190, 20, '재생에너지 입찰제 수익 분석 보고서', ln=True, align='C')
    pdf.set_font("NanumGothic", size=10); pdf.cell(190, 5, f"Issued by V-GEN | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    
    # 발전소 특성
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, f"■ 발전소 제원 및 모델: {selected_region}", "B", ln=True)
    pdf.set_font("NanumGothic", size=11); pdf.ln(3)
    pdf.cell(95, 8, f" • 설비 용량: {cap_mw} MW", ln=0); pdf.cell(95, 8, f" • 고정 계약 단가: {fixed_p} 원/kWh", ln=1)
    
    # 수익 차이 극명하게 단순화
    pdf.ln(10); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "■ VPP 참여 전/후 연간 수익 비교", "B", ln=True)
    pdf.ln(5); pdf.set_fill_color(245, 245, 245)
    pdf.cell(80, 12, "구분", 1, 0, 'C', True); pdf.cell(110, 12, "연간 총 매출액 (추정)", 1, 1, 'C', True)
    pdf.cell(80, 15, "미참여 (단순 매전)", 1, 0, 'C'); pdf.cell(110, 15, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(0, 70, 150); pdf.set_font("NanumGothic", size=12)
    pdf.cell(80, 15, "브이젠 VPP 참여", 1, 0, 'C'); pdf.cell(110, 15, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    
    pdf.ln(5); pdf.set_text_color(200, 0, 0); pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 15, f"연간 추가 순수익: + {net_increase/10000:,.0f} 만원 / Year", ln=True, align='R')
    
    # 상세 정산 항목 (5개 모두)
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=14)
    pdf.cell(190, 10, "■ 5대 정산 항목 세부 명세", "B", ln=True)
    pdf.set_font("NanumGothic", size=10); pdf.ln(3)
    items = [("1. 에너지(MEP)", in_mep), ("2. 용량(CP)", in_cp), ("3. 보상(MAP)", in_map), ("4. 부가(ASP)", in_asp), ("5. 페널티(IMB)", in_imb)]
    for t, v in items:
        pdf.cell(50, 7, f" • {t}", ln=0); pdf.cell(140, 7, f": {v}원/kWh (참여 시 확보 가능)", ln=1)

    # 참고자료 기반 Insight
    pdf.ln(10); pdf.set_fill_color(240, 245, 255); pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    pdf.set_font("NanumGothic", size=11); pdf.cell(190, 8, " [ 정책 요약 및 사업자 대응 전략 ]", ln=True)
    pdf.set_font("NanumGothic", size=9)
    pdf.multi_cell(180, 5, " - 2026년 3월부터 육지 전역 준중앙급전 확대 시행에 따라 '예측정산금' 제도가 공식 일몰됩니다.\n - 실시간 입찰 시장 참여 시에만 용량요금(CP) 및 출력제어 보상(MAP) 수익 수취가 가능합니다.\n - 브이젠은 최첨단 AI 알고리즘을 통해 임밸런스(IMB) 페널티를 최소화하고 수익을 극대화합니다.")

    return pdf.output(dest='S')

# --- 5. 메인 대시보드 (모든 항목 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v3.4")

# [PDF 다운로드 버튼]
pdf_bytes = generate_final_report()
if pdf_bytes:
    st.download_button(label="📄 전문가용 분석 리포트(PDF) 다운로드", data=bytes(pdf_bytes), file_name="VGEN_Profit_Analysis.pdf", mime="application/pdf", use_container_width=True)

# [핵심 수치]
m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 합산 단가", f"{total_unit_vpp:.2f} 원", f"+{owner_net_extra:.2f} 원")

st.divider()

# [시각화 및 항목 설명]
c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 정산 단가 구성 분석 (Waterfall)")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP", "MAP", "ASP", "IMB", "수수료", "최종단가"],
        measure = ["relative", "relative", "relative", "relative", "relative", "relative", "relative", "total"],
        y = [fixed_p, in_cp, in_mep, in_map, in_asp, in_imb, -(vpp_extra_total*(vgen_fee_rate/100)), 0],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map}", f"+{in_asp}", f"{in_imb}", f"-{(vpp_extra_total*(vgen_fee_rate/100)):.1f}", f"{total_unit_vpp:.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 5대 정산 항목 상세")
    items = {"1. 에너지 정산금(MEP)": "실시간 시장 가격과 고정가 차액 정산", "2. 용량 정산금(CP)": "공급 가능 용량에 대한 확정 보상 (11~22원)", "3. 기대이익 보상(MAP)": "출력제어 손실에 대한 시장가 보전", "4. 부가 서비스(ASP)": "계통 안정화 기여 인센티브", "5. 임밸런스(IMB)": "예측 오차 차감 페널티"}
    for k, v in items.items():
        with st.expander(k): st.write(v)

# [정책 동향 및 인사이트 섹션 - 참고자료 반영 고도화]
st.divider()
st.subheader("🚀 2026년 3월 전력시장 패러다임 변화 (정책 자료 요약)")
st.info("💡 **사업주가 반드시 알아야 할 시장 변화 포인트**")
ic1, ic2 = st.columns(2)
with ic1:
    st.markdown("""
    #### ✅ 1. '예측정산금' 일몰과 'CP'의 도입
    뉴스 보도와 같이, 2026년 3월부터 육지 전역에 **준중앙급전**이 확대됩니다. 기존의 단순 예측 정산금(예: 7~9원)은 폐지되며, VPP 입찰을 통해 중앙급전 자원으로 인정받아야만 **kWh당 11원의 용량요금(CP)**을 받을 수 있습니다.
    """)
    
with ic2:
    st.markdown("""
    #### ✅ 2. 출력제어 손실 방어 (MAP)
    최근 전력 계통 불안정으로 호남권 출력제어가 빈번해지고 있습니다. 일반 매전 발전소는 제어 시 수익이 0원이지만, **VPP 참여 자원은 MAP(기대이익보상)**를 통해 제어된 발전량만큼의 수익을 시장 가격으로 보전받습니다.
    """)
    

st.divider()
st.subheader("📋 수익 비교 요약 테이블")
st.table(pd.DataFrame({
    "항목": ["연간 발전량", "적용 단가", "연간 총 수익", "수익 증분"],
    "미참여 (기존)": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "V-GEN VPP 참여": [f"{annual_gen:,.0f} kWh", f"{total_unit_vpp:,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))
