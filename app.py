import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (수익 강조 레이아웃) ---
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
    
    # 1. 수익 비교 요약 (글자 크기 키움)
    pdf.set_font(font_name, "", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, " [핵심] 연간 수익 증대 예상액", ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 16)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(190, 15, f"연간 + {data['extra_profit']/10000:,.0f} 만원 추가 수익 발생", ln=True, align='C')
    
    # 2. 상세 도표
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, "", 11)
    pdf.ln(5)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(70, 12, "구분 항목", border=1, align='C', fill=True)
    pdf.cell(60, 12, "현재 (VPP 미참여)", border=1, align='C', fill=True)
    pdf.cell(60, 12, "V-GEN (VPP 참여)", border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.cell(70, 12, "기본 전력판매 매출", border=1)
    pdf.cell(60, 12, f"{data['base_rev']/10000:,.0f} 만원", border=1, align='R')
    pdf.cell(60, 12, f"{data['base_rev']/10000:,.0f} 만원", border=1, align='R')
    pdf.ln()
    
    pdf.set_text_color(0, 82, 156)
    pdf.cell(70, 12, "VPP 추가 순수익", border=1)
    pdf.cell(60, 12, "0 만원", border=1, align='R')
    pdf.cell(60, 12, f"+ {data['extra_profit']/10000:,.0f} 만원", border=1, align='R', fill=True)
    pdf.ln()
    
    pdf.set_text_color(200, 0, 0)
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 12)
    pdf.cell(70, 15, "총 예상 매출 합계", border=1)
    pdf.cell(60, 15, f"{data['base_rev']/10000:,.0f} 만원", border=1, align='R')
    pdf.set_fill_color(255, 235, 235)
    pdf.cell(60, 15, f"{(data['base_rev']+data['extra_profit'])/10000:,.0f} 만원", border=1, align='R', fill=True)
    
    return bytes(pdf.output())

# --- 2. 데이터 프리셋 및 사이드바 (기존 항목 유지) ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

with st.sidebar:
    st.header("📍 1. 발전소 제원")
    selected_region = st.selectbox("위치 선택", list(region_presets.keys()))
    preset = region_presets[selected_region]
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("고정가격 단가 (원/kWh)", value=180)

    st.header("📊 2. 5대 정산금 직접수정")
    in_mep = st.number_input("MEP (전력량)", value=preset['mep'])
    in_cp = st.number_input("CP (용량)", value=preset['cp'])
    in_map = st.number_input("MAP (기대이익)", value=preset['map'])
    in_mwp = st.number_input("MWP (변동비)", value=preset['mwp'])
    in_imbp = st.number_input("IMBP (페널티)", value=preset['imbp'])

    st.header("💰 3. 수수료 설정")
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)

base_rev_yr = annual_gen * fixed_p
extra_profit_yr = annual_gen * owner_net_extra_unit
total_rev_yr = base_rev_yr + extra_profit_yr

# --- 4. 메인 화면 시각화 (차이 극대화 버전) ---
st.title("📑 V-GEN VPP 수익 분석")

# [핵심] 상단에 아주 큰 강조 지표 배치
st.markdown(f"""
<div style="background-color:#e6f2ff; padding:20px; border-radius:10px; border-left: 8px solid #00529C; margin-bottom:20px;">
    <h3 style="margin:0; color:#00529C;">💰 VPP 참여 시 연간 순수익 증가액</h3>
    <p style="font-size:40px; font-weight:bold; color:#f63366; margin:10px 0;">+ {extra_profit_yr/10000:,.0f} 만원 / 年</p>
    <p style="margin:0; color:#666;">기존 고정가격 매출 대비 약 <b>{(extra_profit_yr/base_rev_yr)*100:.1f}%</b> 수익이 향상됩니다.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("📈 정산 단가 구성 (Waterfall)")
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "CP", "MEP", "MAP", "기타", "최종단가"],
        y = [fixed_p, in_cp, in_mep, in_map, in_mwp-in_imbp, 0],
        measure = ["relative", "relative", "relative", "relative", "relative", "total"],
        textposition = "outside",
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map}", f"{in_mwp-in_imbp}", f"={fixed_p+owner_net_extra_unit:.1f}"]
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with col2:
    st.subheader("🔥 수익 증가 집중 비교")
    # Y축 범위를 조정하여 차이를 크게 보이게 함 (Baseline 조정)
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(
        name='수익 비교',
        x=['기존 매출', 'V-GEN 참여'],
        y=[base_rev_yr/10000, total_rev_yr/10000],
        marker_color=['#ADB5BD', '#00529C'],
        text=[f"{base_rev_yr/10000:,.0f}만", f"{total_rev_yr/10000:,.0f}만"],
        textposition='auto',
    ))
    # Y축 하한선을 기본 매출의 80% 지점으로 설정하여 차이를 시각적으로 증폭
    fig_compare.update_layout(
        yaxis_range=[(base_rev_yr/10000)*0.95, (total_rev_yr/10000)*1.05],
        yaxis_title="연간 수익 (만원)"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

# --- 5. 상세 테이블 및 PDF ---
st.divider()
st.subheader("📋 정산 상세 데이터 (만원 단위)")
detail_df = pd.DataFrame({
    "항목": ["기존 고정가격 예상 매출", "VPP 추가 정산 순이익 (사업자 몫)", "합계 (VPP 참여 시 예상 매출)"],
    "금액 (만원/연간)": [f"{base_rev_yr/10000:,.0f}", f"+ {extra_profit_yr/10000:,.0f}", f"{total_rev_yr/10000:,.0f}"]
})
st.table(detail_df)

if st.button("📄 전문 한글 리포트(PDF) 생성 및 다운로드", use_container_width=True):
    try:
        report_params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "region": selected_region,
            "cap": cap_mw,
            "base_rev": base_rev_yr,
            "extra_profit": extra_profit_yr
        }
        pdf_bytes = create_pdf(report_params)
        st.download_button(label="📩 PDF 파일 저장", data=pdf_bytes, file_name="VGEN_Report.pdf", mime="application/pdf", use_container_width=True)
    except Exception as e:
        st.error(f"오류: {e}")
