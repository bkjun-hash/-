import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (전문 레이아웃 및 각종 도표/단가 보강) ---
class VPP_PDF(FPDF):
    def header(self):
        # 상단 로고/제목 영역
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(150)
        self.cell(0, 10, 'V-GEN Virtual Power Plant Analysis Report', 0, 1, 'R')
        self.ln(5)

def create_pdf(data):
    pdf = VPP_PDF()
    pdf.add_page()
    
    # 폰트 설정 (한글 지원)
    font_path = "NanumGothic.ttf"
    font_ready = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("Nanum", "", font_path)
            pdf.add_font("NanumB", "", font_path) # Bold 대용
            pdf.set_font("Nanum", "", 12)
            font_name = "Nanum"
            font_ready = True
        except: font_name = "Arial"
    else: font_name = "Arial"

    # [1] 리포트 타이틀
    pdf.set_font(font_name, "B" if not font_ready else "", 24)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(190, 25, "VPP 수익 분석 상세 보고서", ln=True, align='C')
    pdf.set_font(font_name, "", 10)
    pdf.set_text_color(100)
    pdf.cell(190, 5, f"분석 일시: {data['date']} | 분석 ID: VGEN-{datetime.now().strftime('%m%d%H%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # [2] 발전소 기본 정보 (표 형태)
    pdf.set_text_color(0)
    pdf.set_font(font_name, "", 12)
    pdf.set_fill_color(240, 245, 250)
    pdf.cell(190, 10, " 1. 발전소 제원 및 분석 조건", ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font(font_name, "", 11)
    pdf.cell(45, 10, "  발전소 위치", border='B')
    pdf.cell(50, 10, f"{data['region']}", border='B', ln=0)
    pdf.cell(45, 10, "  설비 용량", border='B')
    pdf.cell(50, 10, f"{data['cap']} MW", border='B', ln=1)
    
    pdf.cell(45, 10, "  현재 고정단가", border='B')
    pdf.cell(50, 10, f"{data['fixed_p']} 원/kWh", border='B', ln=0)
    pdf.cell(45, 10, "  연간 예상 발전량", border='B')
    pdf.cell(50, 10, f"{data['annual_gen']/10000:,.0f} 만 kWh", border='B', ln=1)
    pdf.ln(10)

    # [3] 핵심 요약: 단가 및 매출 증대 (가장 강조)
    pdf.set_font(font_name, "", 12)
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(190, 10, " 2. VPP 참여 후 수익성 변화 요약", ln=True, fill=True)
    pdf.ln(5)
    
    # 큰 글씨로 강조
    pdf.set_font(font_name, "", 20)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(190, 15, f"연간 예상 추가 순수익: + {data['extra_profit']/10000:,.0f} 만원", ln=True, align='C')
    
    pdf.set_font(font_name, "", 14)
    pdf.set_text_color(0, 82, 156)
    pdf.cell(190, 10, f"최종 합산 단가: {data['total_unit']:.2f} 원/kWh (+{data['unit_diff']:.2f}원 상향)", ln=True, align='C')
    pdf.ln(10)

    # [4] 정산 상세 비교 도표
    pdf.set_text_color(0)
    pdf.set_font(font_name, "", 11)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(60, 12, "구분", 1, 0, 'C', True)
    pdf.cell(65, 12, "기본 고정가격(VPP 미참여)", 1, 0, 'C', True)
    pdf.cell(65, 12, "V-GEN 입찰대행(VPP 참여)", 1, 1, 'C', True)
    
    pdf.cell(60, 11, "적용 단가 (원/kWh)", 1, 0, 'C')
    pdf.cell(65, 11, f"{data['fixed_p']}", 1, 0, 'C')
    pdf.cell(65, 11, f"{data['total_unit']:.2f}", 1, 1, 'C')
    
    pdf.cell(60, 11, "연간 총 매출액 (만원)", 1, 0, 'C')
    pdf.cell(65, 11, f"{data['base_rev']/10000:,.0f}", 1, 0, 'C')
    pdf.set_font(font_name, "", 11)
    pdf.cell(65, 11, f"{(data['base_rev']+data['extra_profit'])/10000:,.0f}", 1, 1, 'C')
    pdf.ln(10)

    # [5] 5대 정산금 구성 상세 (기술적 근거)
    pdf.set_font(font_name, "", 12)
    pdf.set_fill_color(240, 245, 250)
    pdf.cell(190, 10, " 3. VPP 정산금 세부 구성 내역", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font(font_name, "", 10)
    
    items = [
        ("MEP (전력량정산금)", f"{data['mep']}원", "시장 단가와 입찰량 최적화에 따른 수익"),
        ("CP (용량정산금)", f"{data['cp']}원", "발전 가능 용량에 대한 보상 (고정 수익형)"),
        ("MAP (기대이익보상)", f"{data['map']}원", "출력제어 발생 시 손실 보전 정산금"),
        ("기타(MWP/IMBP)", f"{data['mwp']-data['imbp']:.2f}원", "변동비 보상 및 예측 오차 페널티 관리"),
    ]
    
    for item, val, desc in items:
        pdf.set_font(font_name, "", 10)
        pdf.cell(40, 8, f" - {item}:", 0, 0)
        pdf.set_font(font_name, "", 10)
        pdf.cell(20, 8, val, 0, 0)
        pdf.set_font(font_name, "", 9)
        pdf.set_text_color(100)
        pdf.cell(130, 8, f"({desc})", 0, 1)
    
    pdf.ln(15)
    pdf.set_text_color(150)
    pdf.set_font(font_name, "", 8)
    pdf.multi_cell(190, 5, "본 보고서는 V-GEN의 예측 알고리즘에 기초한 시뮬레이션 결과로, 실제 정산액은 전력거래소의 최종 확정 데이터 및 시장 상황에 따라 변동될 수 있습니다.", align='C')

    return bytes(pdf.output())

# --- 2. 사이드바 및 계산 로직 (기존 항목 100% 유지) ---
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

# 계산
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)
total_unit_price = fixed_p + owner_net_extra_unit

base_rev_yr = annual_gen * fixed_p
extra_profit_yr = annual_gen * owner_net_extra_unit
total_rev_yr = base_rev_yr + extra_profit_yr

# --- 3. 메인 화면 시각화 (기존 강조 기능 유지) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")

# 강조 박스 (기존 요청 사항 유지)
st.markdown(f"""
<div style="background-color:#f0f7ff; padding:25px; border-radius:15px; border: 2px solid #00529C; margin-bottom:25px;">
    <h2 style="margin:0; color:#00529C; font-size:24px;">💰 연간 순수익 증가액: <b>+ {extra_profit_yr/10000:,.0f} 만원</b></h2>
    <hr style="margin:15px 0; border:0.5px solid #00529C;">
    <div style="display: flex; justify-content: space-between;">
        <p style="margin:0; font-size:18px;">현재 단가: <b>{fixed_p} 원/kWh</b></p>
        <p style="margin:0; font-size:18px; color:#f63366;">VPP 적용 단가: <b>{total_unit_price:.2f} 원/kWh</b></p>
        <p style="margin:0; font-size:18px; color:#00529C;">수익 향상률: <b>{(extra_profit_yr/base_rev_yr)*100:.1f}%</b></p>
    </div>
</div>
""", unsafe_allow_html=True)

# 시각화 그래프 영역
col1, col2 = st.columns([1.5, 1])
with col1:
    st.subheader("📈 정산 단가 구성 (Waterfall)")
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "CP", "MEP", "MAP", "기타", "최종단가"],
        y = [fixed_p, in_cp, in_mep, in_map, in_mwp-in_imbp, 0],
        measure = ["relative", "relative", "relative", "relative", "relative", "total"],
        textposition = "outside",
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map}", f"{in_mwp-in_imbp}", f"={total_unit_price:.1f}"]
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with col2:
    st.subheader("🔥 수익 증가 시각화")
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(
        x=['기존 매출', 'V-GEN 참여'],
        y=[base_rev_yr/10000, total_rev_yr/10000],
        marker_color=['#ADB5BD', '#00529C'],
        text=[f"{base_rev_yr/10000:,.0f}만", f"{total_rev_yr/10000:,.0f}만"],
        textposition='auto',
    ))
    fig_compare.update_layout(yaxis_range=[(base_rev_yr/10000)*0.94, (total_rev_yr/10000)*1.06])
    st.plotly_chart(fig_compare, use_container_width=True)

# --- 4. 전문 PDF 리포트 생성 섹션 ---
st.divider()
if st.button("📄 전문 한글 분석 리포트(PDF) 생성 및 다운로드", use_container_width=True):
    try:
        pdf_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "region": selected_region,
            "cap": cap_mw,
            "fixed_p": fixed_p,
            "annual_gen": annual_gen,
            "total_unit": total_unit_price,
            "unit_diff": owner_net_extra_unit,
            "base_rev": base_rev_yr,
            "extra_profit": extra_profit_yr,
            "mep": in_mep, "cp": in_cp, "map": in_map, "mwp": in_mwp, "imbp": in_imbp
        }
        pdf_bytes = create_pdf(pdf_data)
        st.download_button(label="📩 분석 리포트 PDF 저장", data=pdf_bytes, 
                           file_name=f"VGEN_VPP_Report_{datetime.now().strftime('%m%d')}.pdf", 
                           mime="application/pdf", use_container_width=True)
    except Exception as e:
        st.error(f"PDF 생성 오류: {e}")
