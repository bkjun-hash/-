import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import io
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v3.0", layout="wide")

# --- 폰트 설정 (나눔고딕 경로 확인) ---
FONT_FILENAME = "NanumGothic.ttf"
FONT_PATH = os.path.join(os.getcwd(), FONT_FILENAME)

# --- 1. 정책 데이터 (2026년 3월 준중앙급전 반영) ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "asp": 0.5, "imb": -0.3},
    "호남/육지 (입찰제 확대 시나리오)": {"cp": 11.0, "mep": 2.5, "map": 1.5, "asp": 0.8, "imb": -0.5},
    "제주도 (입찰제 안착)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "asp": 1.0, "imb": -0.8}
}

# --- 2. 사이드바 (기존 설정 항목) ---
with st.sidebar:
    st.header("📍 1. 지역 선택")
    selected_region = st.selectbox("지역 및 제도 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 상세 설정")
    in_mep = st.number_input("1. 에너지 정산금(MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금(CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상(MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스(ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스(IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 배분 설정")
    owner_share = st.slider("사업주 수익 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_extra_total_unit = in_mep + in_cp + in_map + in_asp + in_imb
owner_net_extra_unit = vpp_extra_total_unit * (owner_share / 100)
total_unit_vpp = fixed_p + owner_net_extra_unit

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_increase = total_rev_vpp - total_rev_base

# --- 4. 한글 PDF 생성 함수 ---
def generate_korean_pdf():
    pdf = FPDF()
    if os.path.exists(FONT_PATH):
        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
        pdf.set_font("NanumGothic", size=12)
    else:
        return None

    pdf.add_page()
    # 헤더
    pdf.set_fill_color(0, 82, 156)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("NanumGothic", size=22)
    pdf.cell(190, 30, 'V-GEN VPP 수익 분석 리포트', ln=True, align='C')
    
    # 본문
    pdf.set_text_color(0, 0, 0)
    pdf.ln(15)
    pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 10, f"1. 발전소 분석 제원 ({selected_region})", ln=True)
    pdf.set_font("NanumGothic", size=12)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.cell(95, 10, f" - 설비 용량: {cap_mw} MW", ln=0)
    pdf.cell(95, 10, f" - 일평균 발전시간: {gen_time} 시간", ln=1)
    pdf.cell(190, 10, f" - 현재 고정단가: {fixed_p} 원/kWh", ln=1)
    
    pdf.ln(10)
    pdf.set_font("NanumGothic", size=16)
    pdf.cell(190, 10, "2. 참여 여부에 따른 연간 수익 비교", ln=True)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("NanumGothic", size=12)
    pdf.cell(80, 12, "구분", 1, 0, 'C', True)
    pdf.cell(110, 12, "연간 총 수익 (예상)", 1, 1, 'C', True)
    pdf.cell(80, 15, "VPP 미참여 (단순 매전)", 1, 0, 'C')
    pdf.cell(110, 15, f"{total_rev_base/10000:,.0f} 만원", 1, 1, 'C')
    pdf.set_text_color(0, 82, 156)
    pdf.cell(80, 15, "V-GEN VPP 참여 시", 1, 0, 'C')
    pdf.cell(110, 15, f"{total_rev_vpp/10000:,.0f} 만원", 1, 1, 'C')
    
    pdf.ln(5)
    pdf.set_text_color(246, 51, 102)
    pdf.set_font("NanumGothic", size=18)
    pdf.cell(190, 20, f"연간 순수익 증대액: + {net_increase/10000:,.0f} 만원", ln=True, align='R')
    
    return pdf.output(dest='S')

# --- 5. 메인 화면 구성 (기본 대시보드 유지 + PDF 추가) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")

# [섹션 1: PDF 다운로드 및 핵심 지표]
col_pdf, col_spacer = st.columns([1, 1])
with col_pdf:
    pdf_out = generate_korean_pdf()
    if pdf_out:
        st.download_button(
            label="📄 한글 분석 리포트(PDF) 다운로드",
            data=bytes(pdf_out),
            file_name=f"VGEN_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.error("나눔고딕 폰트 파일을 찾을 수 없습니다.")

st.markdown(f"#### 💰 현재 {selected_region} 모델 적용 중")
m1, m2, m3 = st.columns(3)
m1.metric("기존 총 수익 (매전)", f"{total_rev_base/10000:,.0f} 만원")
m2.metric("VPP 참여 총 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_increase/10000:,.0f} 만원")
m3.metric("최종 정산 단가", f"{total_unit_vpp:.2f} 원", f"+{owner_net_extra_unit:.2f} 원")

st.divider()

# [섹션 2: 시각화 분석]
c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📈 정산 단가 구성 분석 (원/kWh)")
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "CP(용량)", "MEP(에너지)", "기타보상", "페널티", "수수료", "최종단가"],
        measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        y = [fixed_p, in_cp, in_mep, in_map+in_asp, in_imb, -(vpp_extra_total_unit*(vgen_fee_rate/100)), 0],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map+in_asp}", f"{in_imb}", f"-{(vpp_extra_total_unit*(vgen_fee_rate/100)):.1f}", f"{total_unit_vpp:.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with c2:
    st.subheader("📋 정산금 항목 상세")
    with st.expander("1. 에너지 정산금 (MEP)", expanded=True):
        st.caption("실시간 시장 수익 분배")
    with st.expander("2. 용량 정산금 (CP)", expanded=True):
        st.caption("가동 가능 상태 유지에 대한 확정 보상 (11~22원)")
    with st.expander("3. 기대이익 보상 (MAP)"):
        st.caption("출력제어 시 발생하는 기회비용 보전")
    st.info("**2026년 3월 정책 동향**\n\n호남권 준중앙급전 시행으로 VPP를 통한 CP 확보가 수익 방어의 핵심입니다.")

# [섹션 3: 데이터 테이블 요약]
st.divider()
st.subheader("📅 연간 매전 수익 상세 비교")
res_df = pd.DataFrame({
    "구분": ["기존 방식 (매전)", "브이젠 VPP (최종)"],
    "적용 단가 (원/kWh)": [f"{fixed_p:,.1f} 원", f"{total_unit_vpp:,.2f} 원"],
    "연간 총 매출 (만원)": [f"{total_rev_base/10000:,.0f} 만원", f"{total_rev_vpp/10000:,.0f} 만원"],
    "수익 증분 (만원)": ["-", f"+ {net_increase/10000:,.0f} 만원"]
})
st.table(res_df)
