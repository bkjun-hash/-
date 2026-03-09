import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 PRO", layout="wide")

# --- 1. PDF 생성 함수 (에러 수정 버전) ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 헤더 디자인
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 123, 255) # V-GEN Blue
    pdf.cell(190, 20, "V-GEN VPP Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    # 기본 정보
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, "1. Summary Information", ln=True)
    pdf.line(10, 45, 200, 45)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 10, f"Date: {data['date']}")
    pdf.cell(60, 10, f"Region: {data['region_eng']}")
    pdf.cell(70, 10, f"Capacity: {data['cap']} MW", ln=True)
    pdf.ln(5)
    
    # 수익 분석 결과
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "2. Annual Financial Forecast", ln=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(100, 10, "Current Base Revenue (Est.):")
    pdf.cell(90, 10, f"{data['base_rev']:,.0f} KRW", ln=True, align='R')
    
    pdf.set_text_color(0, 123, 255)
    pdf.cell(100, 10, "VPP Extra Net Profit (V-GEN):")
    pdf.cell(90, 10, f"+ {data['extra_profit']:,.0f} KRW", ln=True, align='R')
    
    pdf.set_text_color(0, 0, 0)
    pdf.line(110, 95, 200, 95)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 15, "Total Expected Revenue:")
    pdf.cell(90, 15, f"{data['base_rev'] + data['extra_profit']:,.0f} KRW", ln=True, align='R')
    pdf.ln(15)
    
    # 면책 조항
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(190, 5, "Notice: This report is a simulation based on KPX rules and V-GEN's optimization algorithm. Actual returns may vary.")
    
    # [핵심 수정] bytearray를 bytes로 강제 변환하여 에러 방지
    return bytes(pdf.output())

# --- 2. 데이터 프리셋 ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

# --- 3. 사이드바 (모든 입력 항목 포함) ---
with st.sidebar:
    st.header("📍 1. 지역 및 제원 설정")
    selected_region = st.selectbox("발전소 위치", list(region_presets.keys()))
    preset = region_presets[selected_region]
    
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("고정가격 단가 (원/kWh)", value=180)

    st.header("📊 2. 5대 정산 단가 (원/kWh)")
    in_mep = st.number_input("전력량정산금 (MEP)", value=preset['mep'])
    in_cp = st.number_input("용량정산금 (CP)", value=preset['cp'])
    in_map = st.number_input("기대이익정산금 (MAP)", value=preset['map'])
    in_mwp = st.number_input("변동비보전 (MWP)", value=preset['mwp'])
    in_imbp = st.number_input("임밸런스 페널티 (IMBP)", value=preset['imbp'])

    st.header("💰 3. 수수료 설정")
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100
    partner_fee_rate = st.slider("영업 채널 배분율 (%)", 0, 20, 10) / 100

# --- 4. 핵심 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
vgen_total_fee_unit = gross_extra_unit * vgen_fee_rate
owner_net_extra_unit = gross_extra_unit - vgen_total_fee_unit

non_vpp_rev = annual_gen * fixed_p
owner_extra_profit_yr = annual_gen * owner_net_extra_unit
vgen_total_fee_yr = annual_gen * vgen_total_fee_unit
partner_comm_yr = vgen_total_fee_yr * partner_fee_rate
vgen_net_profit_yr = vgen_total_fee_yr - partner_comm_yr

# --- 5. 메인 화면 구성 ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")

# 상단 핵심 지표
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("5대 정산금 합계", f"{gross_extra_unit:.2f}원")
with c2: st.metric("사업자 순증분", f"{owner_net_extra_unit:.2f}원")
with c3: st.metric("연 순이익 증분", f"{owner_extra_profit_yr/10000:,.0f}만원")
with c4: st.metric("최종 예상 단가", f"{fixed_p + owner_net_extra_unit:.1f}원")

st.divider()

# 그래프 영역
col_l, col_r = st.columns([1.5, 1])
with col_l:
    st.subheader("📊 수익 구성 워터폴")
    fig_wf = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "relative", "total"],
        x = ["기본단가", "CP", "MEP", "MAP", "기타/페널티", "최종단가"],
        y = [fixed_p, in_cp, in_mep, in_map, in_mwp-in_imbp, 0],
        increasing = {"marker":{"color":"#007BFF"}},
        totals = {"marker":{"color":"#764BA2"}}
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with col_r:
    st.subheader("🧾 수수료 배분 구조")
    df_dist = pd.DataFrame({"구분": ["사업자(80%)", "브이젠(18%)", "채널(2%)"], 
                            "금액": [owner_extra_profit_yr, vgen_net_profit_yr, partner_comm_yr]})
    fig_pie = px.pie(df_dist, values='금액', names='구분', hole=0.4, 
                     color_discrete_sequence=["#007BFF", "#764BA2", "#FFC107"])
    st.plotly_chart(fig_pie, use_container_width=True)

# 상세 내역 테이블
st.subheader("📋 연간 정산 상세 내역")
detail_df = pd.DataFrame({
    "항목": ["기존 고정가격 매출", "VPP 추가 정산금 (세전)", "브이젠 운영 수수료 (합계)", "사업자 최종 순매출"],
    "금액 (원/연간)": [f"{non_vpp_rev:,.0f}", f"{annual_gen * gross_extra_unit:,.0f}", 
                     f"-{vgen_total_fee_yr:,.0f}", f"{non_vpp_rev + owner_extra_profit_yr:,.0f}"]
})
st.table(detail_df)

# --- 6. PDF 리포트 다운로드 (하단 배치) ---
st.divider()
st.subheader("📥 분석 리포트 PDF 저장")

region_eng_map = {"제주도 (출력제어 매우 높음)": "Jeju", "전라도/호남 (출력제어 높음)": "Honam", 
                  "경상도/영남 (출력제어 보통)": "Yeongnam", "기타 육지 (출력제어 낮음)": "Others"}

report_params = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "region_eng": region_eng_map.get(selected_region, "Others"),
    "cap": cap_mw,
    "base_rev": non_vpp_rev,
    "extra_profit": owner_extra_profit_yr
}

try:
    pdf_bytes = create_pdf(report_params)
    st.download_button(
        label="📩 전문 수익 분석 PDF 리포트 다운로드",
        data=pdf_bytes,
        file_name=f"VGEN_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
except Exception as e:
    st.error(f"PDF 생성 중 오류 발생: {e}")
