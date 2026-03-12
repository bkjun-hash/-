import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v5.6", layout="wide")

# --- 폰트 설정 ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 (유지) ---
region_config = {
    "호남/육지 (입찰제 확대 모델)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "mwp": 0.5, "imb": -0.3},
    "제주도 (입찰제 안착 모델)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "mwp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (100% 유지) ---
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
    in_map = st.number_input("3. 기대이익 정산금(MAP)", value=conf['map'])
    in_mwp = st.number_input("4. 변동비보전 정산금(MWP)", value=conf['mwp'])
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

    st.header("🛠️ 6. 참여 비용 (상환 모델)")
    st.info("💡 RTU(150만) + 신자취(150만) 총 300만원은 수수료 쉐어를 통해 분할 상환되므로 사업주 실부담금은 0원입니다.")

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
fee_factor = (1 - (vgen_fee_rate / 100))
net_items = {
    "용량정산금(CP)": in_cp * fee_factor,
    "에너지정산금(MEP)": adj_mep * fee_factor,
    "기대이익정산금(MAP)": in_map * fee_factor,
    "변동비보전정산금(MWP)": in_mwp * fee_factor,
    "임밸런스(IMB)": adj_imb * fee_factor
}
owner_net_extra_unit = sum(net_items.values())
total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * (fixed_p + owner_net_extra_unit)
net_increase = total_rev_vpp - total_rev_base

# --- 4. PDF 생성 함수 (에러 수정: style='B' 제거) ---
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
    pdf.cell(190, 10, "1. 입찰 참여를 통한 연간 순증가 수익 상세", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=10)
    
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(70, 10, "정산 항목", 1, 0, 'C', True)
    pdf.cell(120, 10, "연간 추가 수익 (기존 매전 수익 外)", 1, 1, 'C', True)
    
    for item, unit in net_items.items():
        pdf.cell(70, 10, item, 1, 0, 'C')
        item_annual = (unit * annual_gen) / 10000
        pdf.cell(120, 10, f" + {item_annual:,.0f} 만원", 1, 1, 'R')
    
    # [수정] style='B' 에러 해결을 위해 일반 폰트 사용 + 배경색으로 강조
    pdf.set_fill_color(255, 240, 240)
    pdf.cell(70, 10, "초기 구축 비용", 1, 0, 'C', True)
    pdf.cell(120, 10, "실부담금 0원 (수수료 내 쉐어 방식 상환)", 1, 1, 'R', True)

    pdf.ln(5); pdf.set_font("NanumGothic", size=15)
    pdf.cell(190, 10, "2. 수익 창출 근거: 왜 브이젠(V-GEN)인가?", "B", ln=True)
    pdf.ln(5); pdf.set_font("NanumGothic", size=10)
    
    reasons = [
        ("에너지정산금(MEP) 극대화", "V-GEN의 고성능 AI 예측 엔진은 오차를 최소화하여 일반 업체 대비 최대 4배 높은 MEP 수익을 확보합니다."),
        ("초기 투자 비용 Zero (상환제)", "RTU 및 신재생자료취득장치(총 300만원) 설치비를 수수료에서 분할 차감하는 방식으로 사업주의 실질 지출이 전혀 없습니다."),
        ("부가정산금(MAP/MWP) 보호", "출력 제어 발생 시에도 기대이익(MAP)과 변동비(MWP)를 보전받아 손실을 수익으로 전환합니다."),
        ("임밸런스(IMB) 리스크 방어", "정밀한 입찰 제어를 통해 예측 실패로 인한 페널티를 철저히 방어하여 순수익을 지켜냅니다.")
    ]
    
    for title, desc in reasons:
        pdf.set_font("NanumGothic", size=11); pdf.set_text_color(0, 50, 150)
        pdf.cell(190, 7, f"■ {title}", ln=True)
        pdf.set_font("NanumGothic", size=9); pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(180, 6, desc)
        pdf.ln(2)

    pdf.ln(5); pdf.set_fill_color(0, 32, 96); pdf.rect(10, pdf.get_y(), 190, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_y(pdf.get_y() + 8); pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 10, f"총 예상 연간 매출액: {total_rev_vpp/10000:,.0f} 만원", ln=True, align='C')
    pdf.set_font("NanumGothic", size=13)
    pdf.cell(190, 10, f"▶ 입찰 참여 시 기존 대비 연간 추가 순수익: {net_increase/10000:,.0f} 만원", ln=True, align='C')

    return pdf.output(dest='S')

# --- 5. 메인 UI (100% 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드 v5.6")

m1, m2, m3 = st.columns(3)
m1.metric("기존 연간 수익", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 연간 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("초기 부담금", "0원", "수수료 쉐어 상환")

st.divider()

c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📊 기술 격차에 따른 정산 단가 구성")
    vpp_fee_display = -(owner_net_extra_unit/(1-(vgen_fee_rate/100))*(vgen_fee_rate/100))
    fig = go.Figure(go.Waterfall(
        x = ["기존단가", "CP", "MEP", "MAP", "MWP", "IMB", "수수료", "최종단가"],
        y = [fixed_p, in_cp, adj_mep, in_map, in_mwp, adj_imb, vpp_fee_display, 0],
        measure = ["relative"]*7 + ["total"],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{adj_mep:.1f}", f"+{in_map}", f"+{in_mwp}", f"{adj_imb:.1f}", f"{vpp_fee_display:.1f}", f"{(fixed_p + owner_net_extra_unit):.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📋 실시간 분석 세부 정보")
    with st.expander("⚡ 기술력 가중치 안내", expanded=True):
        st.write(f"**현재 설정:** {tech_option}")
        st.write(f"- MEP 수익 효율: **{tech_impact[tech_option]['mep_mult']}배**")
        st.write(f"- IMB 페널티 방어: **{tech_impact[tech_option]['imb_mult']}배**")
    with st.expander("💰 수수료 및 상환 모델"):
        st.write(f"- 운영 수수료: **{vgen_fee_rate}%**")
        st.success("✅ 초기 인프라 비용(300만원)은 별도 청구 없이 수수료 내에서 상환 처리됩니다.")

st.divider()
st.subheader("🚀 전력시장 패러다임 변화 안내")
st.warning("⚠️ 육지 전역 재생에너지 입찰 시장 확대 시행에 따라 \"예측정산금\" 제도는 공식 일몰되어질 예정입니다.")

# 하단 요약 테이블
st.table(pd.DataFrame({
    "구분": ["연간 발전량", "VPP 정산 단가", "연간 총 매출액", "초기 투자 비용"],
    "기본 매전": [f"{annual_gen:,.0f} kWh", f"{fixed_p:,.1f} 원", f"{total_rev_base/10000:,.0f} 만원", "-"],
    "브이젠 VPP": [f"{annual_gen:,.0f} kWh", f"{(fixed_p + owner_net_extra_unit):,.2f} 원", f"{total_rev_vpp/10000:,.0f} 만원", "0원 (상환 방식)"]
}))

# 최하단 PDF 대형 버튼
st.divider()
st.subheader("📄 분석 결과 보고서 추출")
pdf_data = generate_pro_report()
if pdf_data:
    st.download_button(
        label="📥 [클릭]VPP 자산 가치 극대화 전략 리포트",
        data=bytes(pdf_data),
        file_name="VGEN_Strategic_Profit_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
