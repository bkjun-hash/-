import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import io
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v3.3", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "호남/육지 (입찰제 확대 시나리오)": {"cp": 11.0, "mep": 2.5, "map": 1.5, "asp": 0.8, "imb": -0.5},
    "제주도 (입찰제 안착)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (모든 설정 항목 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 및 제도")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 상세 설정 (5대 항목)")
    in_mep = st.number_input("1. 에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스 페널티(IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 공유 비율")
    owner_share = st.slider("사업주 수익 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_extra_total = in_mep + in_cp + in_map + in_asp + in_imb
owner_net_extra = vpp_extra_total * (owner_share / 100)
total_unit_vpp = fixed_p + owner_net_extra

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_increase = total_rev_vpp - total_rev_base

# --- 4. 고도화된 한글 PDF 생성 함수 ---
def generate_pro_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
    else: return None
    pdf.add_page()
    
    pdf.set_fill_color(0, 50, 120); pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=24)
    pdf.cell(190, 25, 'V-GEN VPP 수익 분석 리포트', ln=True, align='C')
    pdf.set_font("NanumGothic", size=11); pdf.cell(190, 5, f"발행일: {datetime.now().strftime('%Y-%m-%d')} | 모델: {selected_region}", ln=True, align='C')
    
    pdf.ln(30); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "1. 분석 대상 발전소 정보", "B", ln=True)
    pdf.set_font("NanumGothic", size=11); pdf.ln(5)
    pdf.cell(95, 10, f" • 설비 용량: {cap_mw} MW", ln=0); pdf.cell(95, 10, f" • 추정 연간 발전량: {annual_gen:,.0f} kWh", ln=1)
    
    pdf.ln(10); pdf.set_font("NanumGothic", size=15); pdf.cell(190, 10, "2. 경제성 분석 결과", "B", ln=True)
    pdf.set_font("NanumGothic", size=12); pdf.ln(5)
    pdf.cell(70, 15, "기존 매전 수익", 1, 0, 'C'); pdf.cell(120, 15, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(0, 82, 156); pdf.cell(70, 15, "V-GEN VPP 수익", 1, 0, 'C'); pdf.cell(120, 15, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(200, 0, 0); pdf.set_font("NanumGothic", size=16); pdf.cell(190, 15, f"연간 순수익 증분: + {net_increase/10000:,.0f} 만원", ln=True, align='R')
    
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("NanumGothic", size=15); pdf.cell(190, 10, "3. 5대 정산 항목 상세 (kWh 기준)", "B", ln=True)
    item_details = [("에너지(MEP)", in_mep), ("용량(CP)", in_cp), ("보상(MAP)", in_map), ("부가(ASP)", in_asp), ("페널티(IMB)", in_imb)]
    pdf.set_font("NanumGothic", size=11); pdf.ln(5)
    for t, v in item_details:
        pdf.cell(50, 8, f" • {t}", ln=0); pdf.cell(140, 8, f": {v}원", ln=1)

    return pdf.output(dest='S')

# --- 5. 메인 대시보드 UI (기존 기능 100% 복구) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v3.3")

# [PDF 다운로드]
pdf_data = generate_pro_report()
if pdf_data:
    st.download_button(label="📄 전문가용 한글 분석 리포트 다운로드", data=bytes(pdf_data), file_name="VGEN_Report.pdf", mime="application/pdf", use_container_width=True)

# [핵심 지표]
m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 정산 단가", f"{total_unit_vpp:.2f} 원", f"+{owner_net_extra:.2f} 원")

st.divider()

# [중단: 시각화 및 상세 설명]
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
    st.subheader("📋 5대 정산 항목 상세 설명")
    items = {"1. 에너지 정산금(MEP)": "시장 입찰 수익", "2. 용량 정산금(CP)": "공급 가능 용량 보상(11~22원)", "3. 기대이익 보상(MAP)": "출력제어 손실 보전", "4. 부가 서비스(ASP)": "계통 기여 보상", "5. 임밸런스(IMB)": "예측 오차 차감"}
    for k, v in items.items():
        with st.expander(k): st.write(v)

# [정책 동향 인사이트 섹션 - 복구 완료]
st.divider()
st.subheader("🚀 2026년 3월 전력시장 정책 동향 및 인사이트")
st.info("💡 **전문가 분석: 육지 재생에너지의 자원화가 수익의 핵심입니다.**")
ic1, ic2 = st.columns(2)
with ic1:
    st.markdown("""
    #### 1. 예측제도 일몰과 용량요금(CP)의 시대
    과거의 단순 예측 정산금은 사라집니다. 이제는 전력거래소의 지시를 받는 **'준중앙급전'** 자원으로 등록되어야만 **kWh당 11~22원의 고정 CP**를 확보하여 안정적인 현금 흐름을 만들 수 있습니다.
    """)
    
with ic2:
    st.markdown("""
    #### 2. 출력제어 리스크를 수익으로 (MAP)
    호남 지역 등에서 발생하는 출력제어는 사업자에게 치명적입니다. 하지만 VPP 입찰에 참여하면 **기대이익보상(MAP)**을 통해 발전하지 못한 부분에 대해서도 시장 가격으로 보전받을 수 있습니다.
    """)

# [하단: 상세 테이블]
st.divider()
st.subheader("📋 연간 수익 비교 요약")
st.table(pd.DataFrame({
    "항목": ["연간 발전량", "적용 단가", "연간 매출액", "기존 대비 증분"],
    "기존 방식": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP": [f"{annual_gen:,.0f} kWh", f"{total_unit_vpp:,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))
