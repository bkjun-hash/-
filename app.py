import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import io
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v3.2", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "호남/육지 (입찰제 확대 시나리오)": {"cp": 11.0, "mep": 2.5, "map": 1.5, "asp": 0.8, "imb": -0.5},
    "제주도 (입찰제 안착)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (5가지 상세 항목 설정 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 및 제도")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 세부 설정 (5대 항목)")
    in_mep = st.number_input("1. 에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스 페널티(IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 공유 비율")
    owner_share = st.slider("사업주 배분 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share

# --- 3. 핵심 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
# VPP 추가 정산금 총합 (5가지 합산)
vpp_extra_total = in_mep + in_cp + in_map + in_asp + in_imb
# 사업주 순수익분 단가
owner_net_extra = vpp_extra_total * (owner_share / 100)
total_unit_vpp = fixed_p + owner_net_extra

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_increase = total_rev_vpp - total_rev_base

# --- 4. 고도화된 한글 PDF 생성 함수 (5가지 항목 상세 설명 포함) ---
def generate_pro_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
    else: return None

    pdf.add_page()
    
    # [Page Header]
    pdf.set_fill_color(0, 50, 120)
    pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("NanumGothic", size=24)
    pdf.cell(190, 25, 'V-GEN VPP 수익 최적화 분석 리포트', ln=True, align='C')
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(190, 5, f"발행일: {datetime.now().strftime('%Y-%m-%d')} | 적용 모델: {selected_region}", ln=True, align='C')
    
    # [Section 1. 발전소 현황]
    pdf.ln(30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "1. 분석 대상 발전소 일반 현황", "B", ln=True)
    pdf.ln(5)
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(95, 10, f" • 설비 용량: {cap_mw} MW", ln=0)
    pdf.cell(95, 10, f" • 추정 연간 발전량: {annual_gen:,.0f} kWh", ln=1)
    pdf.cell(95, 10, f" • 기준 고정단가: {fixed_p} 원/kWh", ln=0)
    pdf.cell(95, 10, f" • 수익 배분 비율: 사업주 {owner_share}%", ln=1)
    
    # [Section 2. 수익 비교 분석]
    pdf.ln(10)
    pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "2. VPP 참여 시 경제성 변화 추정", "B", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(240, 243, 250)
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(70, 12, "구분", 1, 0, 'C', True)
    pdf.cell(120, 12, "연간 추정 총 매출액", 1, 1, 'C', True)
    
    pdf.cell(70, 15, "기존 (단순 매전 방식)", 1, 0, 'C')
    pdf.cell(120, 15, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    
    pdf.set_font("NanumGothic", size=12)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(70, 15, "브이젠 VPP 통합 정산", 1, 0, 'C')
    pdf.cell(120, 15, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    
    pdf.ln(5)
    pdf.set_text_color(200, 0, 0)
    pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 15, f"▶ 연간 순수익 기대 증분: + {net_increase/10000:,.0f} 만원", ln=True, align='R')
    
    # [Section 3. 5대 정산 항목 상세 분석]
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "3. VPP 정산 항목별 세부 분석", "B", ln=True)
    pdf.ln(3)
    
    pdf.set_font("NanumGothic", size=10)
    # 항목 리스트 (KPX 기준 명칭 및 설명)
    item_details = [
        ("에너지 정산금 (MEP)", f"{in_mep}원", "실시간 전력시장 입찰 가격과 계통한계가격(SMP) 차액 정산 수익"),
        ("용량 정산금 (CP)", f"{in_cp}원", "발전기 공급 가능 용량(Availability) 유지에 대한 고정 대가"),
        ("기대이익 보상 (MAP)", f"{in_map}원", "계통 제약으로 인한 출력제어 발생 시 기회비용을 보전하는 보상금"),
        ("부가서비스 정산 (ASP)", f"{in_asp}원", "주파수 조정 등 계통 유연성 자원 제공에 따른 추가 정산 인센티브"),
        ("임밸런스 페널티 (IMB)", f"{in_imb}원", "입찰 발전량과 실제 발전량 오차에 따른 차감 항목 (V-GEN 관리항목)")
    ]
    
    for title, val, desc in item_details:
        pdf.set_font("NanumGothic", size=11)
        pdf.cell(50, 9, f" • {title}", ln=0)
        pdf.cell(30, 9, f": {val}", ln=0)
        pdf.set_font("NanumGothic", size=9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(110, 9, f"({desc})", ln=1)
        pdf.set_text_color(0, 0, 0)

    # [Section 4. 정책 동향 Insight]
    pdf.ln(10)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(190, 10, " [ 2026 전력시장 정책 동향 및 인사이트 ]", ln=True)
    pdf.set_font("NanumGothic", size=9)
    pdf.multi_cell(180, 5, " 2026년 3월 호남/육지권 재생에너지 입찰제 확대 적용에 따라, 기존 단순 매전 방식은 수익성이 악화될 우려가 있습니다.\n 중앙급전 발전기와 동등한 대가(CP 등)를 지급받는 VPP 참여를 통해 발전소의 자산 가치를 유지하고,\n 출력제어 리스크를 수익으로 전환하는 전략이 필수적입니다.")

    return pdf.output(dest='S')

# --- 5. 메인 대시보드 화면 ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v3.2")

# [상단: PDF 다운로드]
pdf_data = generate_pro_report()
if pdf_data:
    st.download_button(
        label="📄 전문가용 분석 리포트(PDF) 다운로드",
        data=bytes(pdf_data),
        file_name=f"VGEN_Analysis_Report_{datetime.now().strftime('%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 합산 단가", f"{total_unit_vpp:.2f} 원", f"+{owner_net_extra:.2f} 원")

st.divider()

# [중단: 시각화 및 5대 항목 설명]
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
    st.subheader("📑 5대 정산 항목 상세 설명")
    with st.expander("1. 에너지 정산금 (MEP)", expanded=True):
        st.write("시장 입찰 결과에 따라 전력 거래 대가를 정산받는 수익")
    with st.expander("2. 용량 정산금 (CP)", expanded=True):
        st.write("공급 가능 상태에 따라 지급되는 확정 보상 (11~22원)")
    with st.expander("3. 기대이익 보상 (MAP)"):
        st.write("출력제어로 인한 기회비용 손실을 시장가격으로 보전")
    with st.expander("4. 부가 서비스 (ASP)"):
        st.write("계통 주파수 조정 및 신뢰도 유지 기여에 따른 보상")
    with st.expander("5. 임밸런스 페널티 (IMB)"):
        st.write("예측 발전량과 실적 간 오차에 따른 페널티 (차감)")

# [하단: 상세 테이블]
st.divider()
st.subheader("📋 연간 수익 비교 요약")
res_df = pd.DataFrame({
    "항목": ["연간 추정 발전량", "적용 정산 단가", "연간 총 매출액", "기존 대비 증분"],
    "기존 (단순 매전)": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP 참여": [f"{annual_gen:,.0f} kWh", f"{total_unit_vpp:,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
})
st.table(res_df)
