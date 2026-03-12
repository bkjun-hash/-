import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v4.9", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 (유지) ---
region_config = {
    "호남/육지 (입찰제 확대 모델)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "제주도 (입찰제 안착 모델)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (5번 수수료 / 6번 참여비용 분리 유지) ---
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
    tech_impact = {
        "기술력 없는 회사": {"mep_mult": 0.4, "imb_mult": 2.0},
        "보통 수준의 회사": {"mep_mult": 0.8, "imb_mult": 1.2},
        "브이젠 (V-GEN)": {"mep_mult": 1.6, "imb_mult": 0.4}
    }
    tech_option = st.radio("VPP 파트너 선택", options=list(tech_impact.keys()), index=2)
    
    adj_mep = in_mep * tech_impact[tech_option]["mep_mult"]
    adj_imb = in_imb * tech_impact[tech_option]["imb_mult"]

    st.header("💰 5. VPP 수수료 설정")
    vgen_fee_rate = st.slider("수수료율 (%)", 0, 50, 20)

    st.header("🛠️ 6. 참여 비용 (CAPEX)")
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

# --- 4. PDF 생성 함수 (참여 전/후 비교 테이블 강화) ---
def generate_pro_report():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=11)
    else: return None
    
    pdf.add_page()
    pdf.set_fill_color(0, 32, 96); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("NanumGothic", size=22)
    pdf.ln(12); pdf.cell(190, 10, "VPP 자산 가치 극대화 전략 리포트", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.ln(30); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "1. 항목별 수익 비교 (입찰 참여 전 vs 참여 후)", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=9) # 테이블 가독성을 위해 폰트 살짝 조정
    
    # [수정] 3개 컬럼 비교 테이블 (항목 | 참여 전 | 참여 후 순수익)
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(55, 10, "정산 항목", 1, 0, 'C', True)
    pdf.cell(65, 10, "입찰 참여 전 (기존 매전)", 1, 0, 'C', True)
    pdf.cell(70, 10, "입찰 참여 후 (VPP 순수익)", 1, 1, 'C', True)
    
    # 5대 항목 출력
    for item, unit in net_items.items():
        pdf.cell(55, 10, item, 1, 0, 'C')
        pdf.cell(65, 10, "0 원 (수익 없음)", 1, 0, 'C') # 참여 전은 모두 0원
        item_annual = (unit * annual_gen) / 10000
        pdf.cell(70, 10, f"{unit:.2f} 원/kWh ({item_annual:,.0f}만원)", 1, 1, 'C')
    
    # 합계 행
    pdf.set_font("NanumGothic", size=10); pdf.set_fill_color(230, 230, 230)
    pdf.cell(55, 10, "추가 수익 합계", 1, 0, 'C', True)
    pdf.cell(65, 10, "0 만원", 1, 0, 'C', True)
    pdf.cell(70, 10, f"연간 +{net_increase/10000:,.0f} 만원", 1, 1, 'C', True)
    
    # [브이젠 강점 섹션 유지]
    pdf.ln(8); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "2. 결론: 왜 브이젠(V-GEN)과 함께해야 하는가?", "B", ln=True)
    pdf.ln(4); pdf.set_font("NanumGothic", size=11); pdf.set_text_color(0, 50, 150)
    pdf.cell(190, 8, "① 출력제어 리스크를 수익 기회로 전환 (MAP 보상 대응)", ln=True)
    pdf.cell(190, 8, "② 초격차 AI 입찰 엔진을 통한 에너지정산금(MEP) 수익 극대화", ln=True)
    
    # [하단 피날레 박스 유지]
    pdf.ln(8); pdf.set_fill_color(0, 32, 96); pdf.rect(10, pdf.get_y(), 190, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_y(pdf.get_y() + 8); pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 10, f"총 예상 연간 매출액: {total_rev_vpp/10000:,.0f} 만원", ln=True, align='C')
    pdf.set_font("NanumGothic", size=13)
    pdf.cell(190, 10, f"▶ 입찰 참여 시 기존 대비 연간 추가 순수익: {net_increase/10000:,.0f} 만원", ln=True, align='C')

    return pdf.output(dest='S')

# --- 5. 메인 UI (100% 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v4.9")

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 순수익 증분", f"{owner_net_extra_unit:.2f} 원/kWh", f"회수기간: {initial_investment/(net_increase/120000):.1f}개월")

st.divider()

c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 기술 격차에 따른 정산 단가 구성")
    vpp_fee_display = -(owner_net_extra_unit/(1-(vgen_fee_rate/100))*(vgen_fee_rate/100))
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP", "MAP", "ASP", "IMB", "수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_asp, adj_imb, vpp_fee_display, 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_asp}", f"{adj_imb:.1f}", f"{vpp_fee_display:.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 실시간 분석 세부 정보")
    with st.expander("⚡ 파트너별 기술 가중치", expanded=True):
        st.write(f"**현재 설정:** {tech_option}")
        st.write(f"- MEP 수익 효율: **{tech_impact[tech_option]['mep_mult']}배**")
        st.write(f"- IMB 페널티 방어: **{tech_impact[tech_option]['imb_mult']}배**")
    with st.expander("💰 수수료 및 참여 비용"):
        st.write(f"- 운영 수수료: **{vgen_fee_rate}%**")
        st.write(f"- 초기 투자비: **{initial_investment} 만원**")

st.divider()
st.subheader("🚀 전력시장 패러다임 변화 안내")
st.warning("⚠️ 육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다.")

# 하단 요약 테이블
st.table(pd.DataFrame({
    "구분": ["연간 발전량", "VPP 정산 단가", "연간 총 매출액", "순이익 증분"],
    "기본 매전": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", f"+ {net_increase/10000:,.0f} 만원"]
}))

# 하단 PDF 다운로드 버튼 (강조 유지)
st.divider()
st.subheader("📄 분석 결과 보고서 추출")
pdf_data = generate_pro_report()
if pdf_data:
    st.download_button(
        label="📥 [클릭] 입찰 참여 전후 수익 비교표가 포함된 전문가 리포트 다운로드",
        data=bytes(pdf_data),
        file_name=f"VGEN_Comparison_Strategic_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
