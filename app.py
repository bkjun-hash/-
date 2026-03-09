import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (단가 상세, 도표, 기술 설명 포함 전문 레이아웃) ---
class VPP_PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(150)
        self.cell(0, 10, 'V-GEN Virtual Power Plant Analysis Report', 0, 1, 'R')
        self.ln(5)

def create_pdf(data):
    pdf = VPP_PDF()
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

    # [1] 리포트 타이틀
    pdf.set_font(font_name, "B" if not font_ready else "", 22)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(190, 20, "VPP 수익 분석 상세 보고서", ln=True, align='C')
    pdf.set_font(font_name, "", 10)
    pdf.set_text_color(100)
    pdf.cell(190, 5, f"분석 일시: {data['date']} | 분석 ID: VGEN-{datetime.now().strftime('%m%d%H%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # [2] 핵심 요약 (단가 상향 및 수익 증대 강조)
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font(font_name, "", 14)
    pdf.set_text_color(0)
    pdf.cell(190, 12, " [핵심] VPP 참여를 통한 수익성 개선 결과", ln=True, fill=True)
    pdf.ln(5)
    pdf.set_font(font_name, "", 18)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(190, 12, f"연간 추가 순수익: + {data['extra_profit']/10000:,.0f} 만원", ln=True, align='C')
    pdf.set_font(font_name, "", 13)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(190, 10, f"적용 단가: {data['fixed_p']}원 -> {data['total_unit']:.2f} 원/kWh", ln=True, align='C')
    pdf.ln(10)

    # [3] 수익 비교 도표
    pdf.set_text_color(0)
    pdf.set_font(font_name, "", 11)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(60, 12, "구분 항목", 1, 0, 'C', True)
    pdf.cell(65, 12, "현재 (VPP 미참여)", 1, 0, 'C', True)
    pdf.cell(65, 12, "V-GEN (VPP 참여)", 1, 1, 'C', True)
    
    pdf.cell(60, 11, "적용 단가 (원/kWh)", 1, 0, 'C')
    pdf.cell(65, 11, f"{data['fixed_p']}", 1, 0, 'C')
    pdf.cell(65, 11, f"{data['total_unit']:.2f}", 1, 1, 'C')
    
    pdf.cell(60, 11, "연간 총 매출액 (만원)", 1, 0, 'C')
    pdf.cell(65, 11, f"{data['base_rev']/10000:,.0f}", 1, 0, 'C')
    pdf.cell(65, 11, f"{(data['base_rev']+data['extra_profit'])/10000:,.0f}", 1, 1, 'C')
    pdf.ln(10)

    # [4] 정산금 구성 기술 설명
    pdf.set_font(font_name, "", 12)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(190, 10, " [참고] VPP 정산금 상세 구성", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font(font_name, "", 10)
    descriptions = [
        (f"MEP (전력량정산금): {data['mep']}원", "시장 입찰 최적화에 따른 추가 전력 판매 수익"),
        (f"CP (용량정산금): {data['cp']}원", "공급 가능 용량에 대한 고정 보상 수익"),
        (f"MAP (기대이익보상): {data['map']}원", "출력제어 발생 시 손실액을 수익으로 전액 보전")
    ]
    for title, desc in descriptions:
        pdf.cell(190, 8, f" - {title} : {desc}", ln=True)

    return bytes(pdf.output())

# --- 2. 데이터 프리셋 및 사이드바 (기존 상세 입력 유지) ---
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

    st.header("💰 3. 수수료 및 정책")
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)

base_rev_yr = annual_gen * fixed_p
extra_profit_yr = annual_gen * owner_net_extra_unit
total_rev_yr = base_rev_yr + extra_profit_yr
total_unit_price = fixed_p + owner_net_extra_unit

# --- 4. 메인 대시보드 (풀 스펙 레이아웃) ---
st.title("📑 V-GEN VPP 통합 수익 분석 대시보드")

# [핵심 강조 섹션]
st.markdown(f"""
<div style="background-color:#f0f7ff; padding:25px; border-radius:15px; border-left: 10px solid #00529C; margin-bottom:25px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
    <h2 style="margin:0; color:#00529C; font-size:26px;">💰 연간 예상 순수익 증가액: <b>+ {extra_profit_yr/10000:,.0f} 만원</b></h2>
    <hr style="margin:15px 0; border:0.5px solid #00529C; opacity: 0.3;">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <p style="margin:5px 0; font-size:18px;">현재 단가: <b>{fixed_p} 원/kWh</b></p>
        <p style="margin:5px 0; font-size:20px; color:#f63366;">VPP 적용 단가: <b>{total_unit_price:.2f} 원/kWh</b></p>
        <p style="margin:5px 0; font-size:18px; color:#00529C;">수익 상향률: <b>+ {(extra_profit_yr/base_rev_yr)*100:.1f}%</b></p>
    </div>
</div>
""", unsafe_allow_html=True)

# 4대 지표 나란히 배치
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("5대 정산금 합계", f"{gross_extra_unit:.2f} 원")
with m2: st.metric("사업자 순증분(단가)", f"{owner_net_extra_unit:.2f} 원")
with m3: st.metric("연매출 (VPP 미참여)", f"{base_rev_yr/10000:,.0f} 만원")
with m4: st.metric("연매출 (VPP 참여)", f"{total_rev_yr/10000:,.0f} 만원", delta=f"+{extra_profit_yr/10000:,.0f}만")

st.divider()

# 시각화 영역 (워터폴 + 확대 바 차트)
col1, col2 = st.columns([1.5, 1])
with col1:
    st.subheader("📈 정산 단가 상세 구성 (Waterfall)")
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "CP", "MEP", "MAP", "기타/페널티", "최종단가"],
        y = [fixed_p, in_cp, in_mep, in_map, in_mwp-in_imbp, 0],
        measure = ["relative", "relative", "relative", "relative", "relative", "total"],
        textposition = "outside",
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map}", f"{in_mwp-in_imbp:.2f}", f"={total_unit_price:.1f}"]
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with col2:
    st.subheader("🔥 연간 수익 변화 시각화 (Y축 줌)")
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(
        x=['기존 매출', 'V-GEN 참여'],
        y=[base_rev_yr/10000, total_rev_yr/10000],
        marker_color=['#ADB5BD', '#00529C'],
        text=[f"{base_rev_yr/10000:,.0f}만", f"{total_rev_yr/10000:,.0f}만"],
        textposition='auto',
    ))
    # 시각적 격차 강조를 위한 Y축 범위 설정 (94% ~ 106%)
    fig_compare.update_layout(yaxis_range=[(base_rev_yr/10000)*0.94, (total_rev_yr/10000)*1.06])
    st.plotly_chart(fig_compare, use_container_width=True)

# --- 5. 상세 데이터 테이블 및 PDF 리포트 발급 ---
st.divider()
st.subheader("📋 정산 상세 데이터 분석")
st.table(pd.DataFrame({
    "구분 항목": ["기존 고정가격 단가", "VPP 추가 단가(순증분)", "VPP 최종 합산 단가", "연간 총 예상 매출액(VPP)"],
    "상세 수치": [f"{fixed_p} 원/kWh", f"+ {owner_net_extra_unit:.2f} 원/kWh", f"{total_unit_price:.2f} 원/kWh", f"{total_rev_yr/10000:,.0f} 만원"]
}))

if st.button("📄 전문 한글 분석 리포트(PDF) 다운로드", use_container_width=True):
    try:
        pdf_params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "region": selected_region,
            "cap": cap_mw,
            "fixed_p": fixed_p,
            "total_unit": total_unit_price,
            "base_rev": base_rev_yr,
            "extra_profit": extra_profit_yr,
            "mep": in_mep, "cp": in_cp, "map": in_map, "mwp": in_mwp, "imbp": in_imbp
        }
        pdf_bytes = create_pdf(pdf_params)
        st.download_button(label="📩 리포트 파일 저장하기", data=pdf_bytes, file_name="VGEN_VPP_Report.pdf", mime="application/pdf", use_container_width=True)
    except Exception as e:
        st.error(f"오류: {e}")

st.caption("📱 스마트폰 미팅 시 QR코드를 스캔하여 대시보드를 즉시 공유하세요.")
st.image("https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=https://vgen-vpp.streamlit.app")
