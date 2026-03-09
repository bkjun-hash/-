import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (가독성 및 수익 차이 강조 버전) ---
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
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 22)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(190, 20, "V-GEN VPP 수익 분석 보고서", ln=True, align='C')
    pdf.ln(5)
    
    # 1. 요약 정보
    pdf.set_font(font_name, "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(190, 10, " [1] 분석 대상 정보", ln=True, fill=True)
    pdf.ln(2)
    pdf.cell(95, 10, f" 지역: {data['region']}")
    pdf.cell(95, 10, f" 용량: {data['cap']} MW", ln=True)
    pdf.ln(5)

    # 2. 수익 비교 도표 (만원 단위 절사 및 강조)
    pdf.set_font(font_name, "", 12)
    pdf.cell(190, 10, " [2] VPP 참여에 따른 연간 수익 변화 (예상)", ln=True, fill=True)
    pdf.ln(3)
    
    # 표 헤더
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(70, 12, "구분 항목", border=1, align='C', fill=True)
    pdf.cell(60, 12, "현재 (VPP 미참여)", border=1, align='C', fill=True)
    pdf.cell(60, 12, "V-GEN (VPP 참여)", border=1, align='C', fill=True)
    pdf.ln()
    
    # 표 내용 (만원 단위로 표시)
    pdf.cell(70, 12, "기본 전력판매 수익", border=1)
    pdf.cell(60, 12, f"{data['base_rev']/10000:,.0f} 만원", border=1, align='R')
    pdf.cell(60, 12, f"{data['base_rev']/10000:,.0f} 만원", border=1, align='R')
    pdf.ln()
    
    # 추가 수익 강조
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 12)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(70, 12, "VPP 추가 정산 순수익", border=1)
    pdf.cell(60, 12, "-", border=1, align='C')
    pdf.set_fill_color(230, 242, 255)
    pdf.cell(60, 12, f"+ {data['extra_profit']/10000:,.0f} 만원", border=1, align='R', fill=True)
    pdf.ln()
    
    # 합계 강조
    pdf.set_text_color(200, 0, 0)
    pdf.cell(70, 14, "최종 연간 예상 매출", border=1)
    pdf.cell(60, 14, f"{data['base_rev']/10000:,.0f} 만원", border=1, align='R')
    pdf.set_fill_color(255, 235, 235)
    pdf.cell(60, 14, f"{(data['base_rev']+data['extra_profit'])/10000:,.0f} 만원", border=1, align='R', fill=True)
    pdf.ln(15)

    # 3. 브이젠의 핵심 가치 설명
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, "", 13)
    pdf.cell(190, 10, " [3] 왜 브이젠 VPP인가?", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font(font_name, "", 10)
    pdf.multi_cell(190, 8, 
        "- 독보적 운영 실적: 남동발전 제주 풍력 VPP를 실제 운영 중인 검증된 알고리즘입니다.\n"
        "- 손실의 수익화: 출력제어로 인한 발전 중단 손실을 MAP 정산금으로 완벽 보전합니다.\n"
        "- AI 예측 기술: 국내 최고 수준의 발전량 예측으로 페널티(IMBP)를 최소화합니다.")

    return bytes(pdf.output())

# --- 2. 입력 및 데이터 처리 ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

with st.sidebar:
    st.header("📍 발전소 제원 설정")
    selected_region = st.selectbox("위치 선택", list(region_presets.keys()))
    preset = region_presets[selected_region]
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("고정가격 (원/kWh)", value=180)
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# 계산
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = preset['mep'] + preset['cp'] + preset['map'] + preset['mwp'] - preset['imbp']
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)

base_rev_yr = annual_gen * fixed_p
extra_profit_yr = annual_gen * owner_net_extra_unit
total_rev_yr = base_rev_yr + extra_profit_yr

# --- 3. 메인 화면 구성 (시각적 강조) ---
st.title("📑 V-GEN VPP 수익 분석")
st.markdown("### **기존 고정가 매출 대비 추가 수익을 확인하세요!**")

# 상단 지표 (Delta를 크게 강조)
c1, c2 = st.columns(2)
with c1:
    st.metric("현재 연간 매출 (VPP 미참여)", f"{base_rev_yr/10000:,.0f} 만원")
with c2:
    st.metric("V-GEN 참여 후 연간 매출", f"{total_rev_yr/10000:,.0f} 만원", 
              delta=f"+ {extra_profit_yr/10000:,.0f} 만원 증분", delta_color="normal")

st.divider()

# 수익 차이 비교 막대 그래프
st.subheader("📊 수익 체감 비교")
compare_df = pd.DataFrame({
    "구분": ["기존 매출", "V-GEN 참여"],
    "금액(만원)": [base_rev_yr/10000, total_rev_yr/10000],
    "유형": ["기본", "기본 + VPP수익"]
})
fig_bar = px.bar(compare_df, x="구분", y="금액(만원)", color="유형",
                 text_auto='.0f', color_discrete_map={"기본": "#ADB5BD", "기본 + VPP수익": "#00529C"})
fig_bar.update_layout(showlegend=False, yaxis_title="연간 수익 (단위: 만원)")
st.plotly_chart(fig_bar, use_container_width=True)



# --- 4. PDF 리포트 다운로드 ---
st.divider()
st.subheader("📥 전문 리포트 발급")
report_params = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "region": selected_region,
    "cap": cap_mw,
    "base_rev": base_rev_yr,
    "extra_profit": extra_profit_yr
}

if st.button("📄 한글 분석 리포트(PDF) 생성 및 공유"):
    try:
        pdf_out = create_pdf(report_params)
        st.download_button(
            label="📩 리포트 파일 다운로드",
            data=pdf_out,
            file_name=f"VGEN_VPP_Report_{datetime.now().strftime('%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.success("리포트가 성공적으로 생성되었습니다. 카카오톡이나 메일로 공유하세요!")
    except Exception as e:
        st.error(f"오류 발생: {e}")
