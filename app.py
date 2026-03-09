import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 전문 수익 분석기", layout="wide")

# --- 1. PDF 생성 함수 (강조 및 상세 설명 대폭 추가) ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    font_path = "NanumGothic.ttf"
    font_ready = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("Nanum", "", font_path)
            pdf.set_font("Nanum", "", 12)
            font_name = "Nanum"
            font_ready = True
        except: font_name = "Arial"
    else: font_name = "Arial"

    # 헤더
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 24)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(190, 25, "V-GEN VPP 통합 수익 분석 보고서", ln=True, align='C')
    pdf.ln(5)
    
    # 1. 발전소 현황
    pdf.set_font(font_name, "", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, " 1. 분석 대상 발전소 정보", ln=True, fill=True)
    pdf.set_font(font_name, "", 11)
    pdf.ln(3)
    pdf.cell(95, 10, f"분석 지역: {data['region']}")
    pdf.cell(95, 10, f"설비 용량: {data['cap']} MW", ln=True)
    pdf.cell(95, 10, f"예상 발전시간: {data['gen_time']} h")
    pdf.cell(95, 10, f"적용 고정단가: {data['fixed_p']} 원", ln=True)
    pdf.ln(5)

    # 2. 수익 비교 (가장 강조되는 부분)
    pdf.set_font(font_name, "", 14)
    pdf.cell(190, 10, " 2. VPP 참여 전/후 연간 수익 비교", ln=True, fill=True)
    pdf.ln(5)
    
    # 표 디자인 (강조)
    pdf.set_font(font_name, "", 12)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(70, 12, "구분 항목", border=1, align='C', fill=True)
    pdf.cell(60, 12, "현행 (참여 전)", border=1, align='C', fill=True)
    pdf.cell(60, 12, "V-GEN (참여 후)", border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.cell(70, 11, "연간 기본 매출액", border=1)
    pdf.cell(60, 11, f"{data['base_rev']:,.0f} 원", border=1, align='R')
    pdf.cell(60, 11, f"{data['base_rev']:,.0f} 원", border=1, align='R')
    pdf.ln()
    
    pdf.set_text_color(0, 82, 156)
    pdf.cell(70, 11, "VPP 추가 정산금 (순수익)", border=1)
    pdf.cell(60, 11, "0 원 (발생 없음)", border=1, align='C')
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 12)
    pdf.cell(60, 11, f"+ {data['extra_profit']:,.0f} 원", border=1, align='R')
    pdf.ln()
    
    pdf.set_text_color(200, 0, 0)
    pdf.cell(70, 13, "연간 최종 합계 수익", border=1, fill=True)
    pdf.cell(60, 13, f"{data['base_rev']:,.0f} 원", border=1, align='R', fill=True)
    pdf.cell(60, 13, f"{data['base_rev'] + data['extra_profit']:,.0f} 원", border=1, align='R', fill=True)
    pdf.ln(15)

    # 3. VPP 정산금 상세 및 기술 설명
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, "", 14)
    pdf.cell(190, 10, " 3. 수익 증대 기술 및 근거", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font(font_name, "", 10)
    pdf.multi_cell(190, 8, 
        f"- MEP(전력량정산금): 실시간 입찰을 통한 전력 판매 수익 최적화 ({data['mep']}원 적용)\n"
        f"- CP(용량정산금): 발전소의 공급 가능 용량에 대한 보상 수익 ({data['cp']}원 적용)\n"
        f"- MAP(기대이익보상): 출력제어 발생 시 손실을 수익으로 보전 ({data['map']}원 적용)\n"
        "- V-GEN AI 예측: 남동발전 제주 풍력 운영 노하우를 담은 정밀 예측 알고리즘 적용\n"
        "- 리스크 관리: 오차율 최소화를 통한 IMBP(페널티) 방어 체계 구축"
    )

    pdf.ln(10)
    pdf.set_font(font_name, "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(190, 5, "본 보고서는 V-GEN 시뮬레이션 결과이며 실제 정산은 전력거래소 규정을 따릅니다.", align='C')

    return bytes(pdf.output())

# --- 2. 입력 및 데이터 (기존 로직 보강) ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

st.title("📑 V-GEN VPP 차세대 수익 정산 시뮬레이터")
st.markdown("전력시장 개편에 따른 **제주/육지 발전소 수익 극대화 전략**을 확인하세요.")

with st.sidebar:
    st.header("⚙️ 발전소 정밀 제원")
    selected_region = st.selectbox("위치 선택", list(region_presets.keys()))
    preset = region_presets[selected_region]
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간 (h)", 2.0, 5.5, 3.6, help="지역별 기상 특성을 고려한 평균 시간입니다.")
    fixed_p = st.number_input("고정가격 단가 (원/kWh)", value=180, help="현재 계약 중인 고정가격을 입력하세요.")

    st.header("🔍 5대 정산 항목 상세")
    with st.expander("항목별 단가 수정 (원/kWh)"):
        in_mep = st.number_input("MEP (전력량)", value=preset['mep'])
        in_cp = st.number_input("CP (용량)", value=preset['cp'])
        in_map = st.number_input("MAP (기대이익)", value=preset['map'])
        in_mwp = st.number_input("MWP (변동비)", value=preset['mwp'])
        in_imbp = st.number_input("IMBP (페널티)", value=preset['imbp'])

    st.header("🏢 운영 정책")
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 정교한 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)

owner_extra_profit_yr = annual_gen * owner_net_extra_unit
base_rev_yr = annual_gen * fixed_p
total_rev_yr = base_rev_yr + owner_extra_profit_yr
profit_increase_rate = (owner_extra_profit_yr / base_rev_yr) * 100

# --- 4. 시각화 대시보드 (설명 강화) ---
st.info(f"💡 **분석 결과:** VPP 참여 시 기존 대비 약 **{profit_increase_rate:.1f}%** 의 추가 수익 창출이 예상됩니다.")

m1, m2, m3 = st.columns(3)
with m1: st.metric("참여 전 연매출", f"{base_rev_yr/10000:,.0f} 만원")
with m2: 
    st.metric("VPP 참여 후 연매출", f"{total_rev_yr/10000:,.0f} 만원", 
              delta=f"+{owner_extra_profit_yr/10000:,.0f} 만원", delta_color="normal")
with m3: st.metric("적용 단가 상승분", f"+{owner_net_extra_unit:.2f} 원/kWh")

st.divider()

# 그래프 섹션
c_left, c_right = st.columns([1.2, 1])
with c_left:
    st.subheader("📈 정산금 구성 요소 (Waterfall)")
    st.write("기본 고정가에 더해지는 항목별 수익 기여도입니다.")
    fig = go.Figure(go.Waterfall(
        x = ["고정가", "CP", "MEP", "MAP", "기타", "최종단가"],
        y = [fixed_p, in_cp, in_mep, in_map, in_mwp-in_imbp, 0],
        measure = ["relative", "relative", "relative", "relative", "relative", "total"],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    st.plotly_chart(fig, use_container_width=True)

with c_right:
    st.subheader("💰 연간 수익 비교 (Bar)")
    compare_df = pd.DataFrame({
        "구분": ["기존 매출", "VPP 참여 매출"],
        "금액(만원)": [base_rev_yr/10000, total_rev_yr/10000]
    })
    fig_bar = px.bar(compare_df, x="구분", y="금액(만원)", color="구분", 
                     text_auto='.0f', color_discrete_sequence=["#ADB5BD", "#00529C"])
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- 5. 상세 설명 및 PDF 다운로드 ---
st.subheader("📋 상세 분석 리포트 가이드")
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.markdown("""
    **왜 브이젠 VPP인가요?**
    * **출력제어 보상:** 제주 지역의 고질적인 제어 문제를 MAP 정산금으로 해결합니다.
    * **AI 예측:** 오차를 줄여 페널티(IMBP)를 방어하고 수익을 지킵니다.
    * **운영 노하우:** 실제 남동발전 제주 풍력 운영 데이터를 보유한 유일한 팀입니다.
    """)

report_params = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "region": selected_region,
    "cap": cap_mw,
    "gen_time": gen_time,
    "fixed_p": fixed_p,
    "base_rev": base_rev_yr,
    "extra_profit": owner_extra_profit_yr,
    "mep": in_mep, "cp": in_cp, "map": in_map
}

with col_info2:
    if st.button("📄 전문 분석 리포트 생성 (PDF)", use_container_width=True):
        try:
            pdf_bytes = create_pdf(report_params)
            st.download_button(
                label="📩 생성된 PDF 리포트 다운로드",
                data=pdf_bytes,
                file_name=f"VGEN_VPP_Report_{selected_region}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.success("리포트가 성공적으로 생성되었습니다. 위 버튼을 눌러 다운로드하세요!")
        except Exception as e:
            st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")

# QR 공유 기능 (이미지 태그 포함)
st.write("---")
st.caption("📱 스마트폰으로 이 결과를 공유하시려면 QR코드를 스캔하세요.")
st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=100x100&data={st.session_state.get('url', 'https://vgen-vpp.streamlit.app')}")
