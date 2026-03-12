import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import io
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v3.1", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3, "model": "Mainland-A"},
    "호남/육지 (입찰제 확대 시나리오)": {"cp": 11.0, "mep": 2.5, "map": 1.5, "asp": 0.8, "imb": -0.5, "model": "Mainland-B"},
    "제주도 (입찰제 안착)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8, "model": "Jeju-Special"}
}

# --- 2. 사이드바 (기존 설정 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 및 제도")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 세부 설정")
    in_mep = st.number_input("에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("임밸런스(IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 공유 비율")
    owner_share = st.slider("사업주 배분 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share

# --- 3. 핵심 계산 로직 ---
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
    
    # [Page Header]
    pdf.set_fill_color(0, 50, 120)
    pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("NanumGothic", size=24)
    pdf.cell(190, 25, 'V-GEN VPP 수익 최적화 분석 리포트', ln=True, align='C')
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(190, 5, f"보고서 발행일: {datetime.now().strftime('%Y-%m-%d')} | 대상 모델: {selected_region}", ln=True, align='C')
    
    # [Section 1. 발전소 현황]
    pdf.ln(30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("NanumGothic", size=15)
    pdf.set_draw_color(0, 50, 120)
    pdf.cell(190, 10, "1. 분석 대상 발전소 일반 현황", "B", ln=True)
    pdf.ln(5)
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(95, 10, f" • 설비 용량: {cap_mw} MW", ln=0)
    pdf.cell(95, 10, f" • 연간 추정 발전량: {annual_gen:,.0f} kWh", ln=1)
    pdf.cell(95, 10, f" • 현재 적용 단가: {fixed_p} 원/kWh", ln=0)
    pdf.cell(95, 10, f" • 수익 배분: 사업주 {owner_share}% / V-GEN {vgen_fee_rate}%", ln=1)
    
    # [Section 2. 수익 비교 분석 - 시각적 강조]
    pdf.ln(10)
    pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "2. VPP 참여에 따른 경제성 분석 결과", "B", ln=True)
    pdf.ln(5)
    
    # 표 헤더
    pdf.set_fill_color(230, 235, 245)
    pdf.set_font("NanumGothic", size=11)
    pdf.cell(70, 12, "구분", 1, 0, 'C', True)
    pdf.cell(120, 12, "연간 추정 매출 (단순 매전 대비)", 1, 1, 'C', True)
    
    # 기존 수익
    pdf.cell(70, 15, "기존 방식 (PPA/FIT)", 1, 0, 'C')
    pdf.cell(120, 15, f"약 {total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    
    # VPP 수익
    pdf.set_font("NanumGothic", size=12)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(70, 15, "V-GEN VPP 통합 정산", 1, 0, 'C')
    pdf.cell(120, 15, f"약 {total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    
    # 격차 강조
    pdf.ln(5)
    pdf.set_text_color(200, 0, 0)
    pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 15, f"▷ 연간 순수익 기대 증분: + {net_increase/10000:,.0f} 만원", ln=True, align='R')
    
    # [Section 3. 정산금 세부 구조]
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "3. VPP 정산금 상세 구조 (단가 분석)", "B", ln=True)
    pdf.ln(3)
    pdf.set_font("NanumGothic", size=10)
    
    details = [
        ("용량정산금 (CP)", f"{in_cp}원", "발전 가능 상태에 대한 고정 보상 (가장 안정적 수익원)"),
        ("에너지정산금 (MEP)", f"{in_mep}원", "시장 입찰을 통한 전력량 판매 추가 이익"),
        ("기타보상 (MAP/ASP)", f"{in_map+in_asp}원", "출력제어 보상 및 계통 기여 인센티브"),
        ("페널티 및 수수료 차감", f"약 {vpp_extra_total*(vgen_fee_rate/100) - in_imb:.1f}원", "예측 오차 페널티 및 운영 서비스 수수료")
    ]
    
    for title, val, desc in details:
        pdf.set_font("NanumGothic", size=11)
        pdf.cell(50, 10, f" • {title}", ln=0)
        pdf.cell(30, 10, f": {val}", ln=0)
        pdf.set_font("NanumGothic", size=9)
        pdf.cell(110, 10, f"({desc})", ln=1)

    # [Section 4. 정책 동향 Insight]
    pdf.ln(10)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 190, 40, 'F')
    pdf.set_font("NanumGothic", size=12)
    pdf.cell(190, 10, " [ 전문가 제언: 2026 전력시장 대응 전략 ]", ln=True)
    pdf.set_font("NanumGothic", size=10)
    pdf.multi_cell(180, 6, " 본 리포트는 2026년 3월 시행되는 육지 준중앙급전 및 재생에너지 입찰제도를 바탕으로 작성되었습니다. \n 기존의 예측정산금 제도가 종료됨에 따라, VPP를 통한 용량요금(CP) 확보와 출력제어 보상(MAP)은 \n 이제 선택이 아닌 발전소 자산 가치 방어를 위한 필수 전략입니다. V-GEN은 최적 입찰을 통해 \n 사업주님의 수익을 극대화합니다.")

    return pdf.output(dest='S')

# --- 5. 메인 대시보드 화면 ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v3.1")

# [상단: PDF 다운로드 및 요약]
r1_c1, r1_c2 = st.columns([1, 1.2])
with r1_c1:
    pdf_data = generate_pro_report()
    if pdf_data:
        st.download_button(
            label="📄 전문가용 분석 리포트(PDF) 다운로드",
            data=bytes(pdf_data),
            file_name=f"VGEN_Analysis_Report_{datetime.now().strftime('%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
with r1_c2:
    st.success(f"현재 **{selected_region}** 모델이 적용되었습니다. (순수익 증분: {net_increase/10000:,.0f}만원)")

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 합산 단가", f"{total_unit_vpp:.2f} 원", f"+{owner_net_extra:.2f} 원")

st.divider()

# [중단: 시각화 및 상세 항목]
c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 정산 단가 구성 분석 (Waterfall)")
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP", "기타정산", "IMB", "수수료", "최종단가"],
        measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        y = [fixed_p, in_cp, in_mep, in_map+in_asp, in_imb, -(vpp_extra_total*(vgen_fee_rate/100)), 0],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map+in_asp}", f"{in_imb}", f"-{(vpp_extra_total*(vgen_fee_rate/100)):.1f}", f"{total_unit_vpp:.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📑 정산금 상세 항목 설명")
    with st.expander("1. 용량 정산금(CP)", expanded=True):
        st.write("발전기 공급 가능 용량에 대해 지급되는 확정 보상금")
    with st.expander("2. 에너지 정산금(MEP)", expanded=True):
        st.write("실시간 입찰 시장 가격과 고정가의 차액 정산 수익")
    with st.expander("3. 출력제어 보상(MAP)"):
        st.write("계통 안정화로 인한 출력제어 시 발생하는 기회비용 보전")
    st.info("💡 **V-GEN 인사이트**: 2026년 3월부터는 단순 발전량보다 '급전 가능성'이 돈이 되는 시장으로 변화합니다.")

# [하단: 상세 테이블]
st.divider()
st.subheader("📋 연간 수익 비교 요약")
res_df = pd.DataFrame({
    "항목": ["연간 추정 발전량", "적용 정산 단가", "연간 총 매출액", "기존 대비 증분"],
    "기존 (단순 매전)": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP 참여": [f"{annual_gen:,.0f} kWh", f"{total_unit_vpp:,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
})
st.table(res_df)
