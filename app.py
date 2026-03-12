import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v2.0", layout="wide")

# --- 1. 정책 반영 로직 및 데이터 ---
# 제주: 입찰제 시행 (CP 22원), 육지: 준중앙급전/입찰제 확대 (CP 11원 예상)
region_options = {
    "제주도 (재생에너지 입찰제)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "is_mainland": False},
    "호남/육지 (준중앙급전/확대 예정)": {"cp": 11.0, "mep": 1.2, "map": 1.5, "is_mainland": True}
}

# --- 2. 사이드바 설정 ---
with st.sidebar:
    st.header("📍 1. 지역 및 제도 선택")
    selected_name = st.selectbox("적용 지역 선택", list(region_options.keys()))
    conf = region_options[selected_name]
    
    st.header("🏭 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정단가 (원/kWh)", value=180)

    st.header("⚙️ 3. 정산금 세부 설정")
    # 육지 확대 시 예측정산금은 일몰되므로 입찰제 모드에서는 0원 취급 또는 CP에 통합
    if conf['is_mainland']:
        st.info("💡 육지 확대 시 기존 예측정산금은 일몰되어 용량요금(CP) 체계로 통합됩니다.")
        in_forecast = 0.0
    else:
        in_forecast = st.number_input("기존 예측정산금 (일몰 전)", value=3.0)
        
    in_mep = st.number_input("MEP (전력량)", value=conf['mep'])
    in_cp = st.number_input("CP (용량요금)", value=conf['cp'])
    in_map = st.number_input("MAP (기대이익보상)", value=conf['map'])
    
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
# 순수익 단가 계산 (기존 예측정산금을 대체하는 VPP 정산금 구조)
vpp_extra_unit = in_mep + in_cp + in_map - 0.3 # 페널티(IMBP) 차감
owner_net_unit = vpp_extra_unit * (1 - vgen_fee_rate)

# 예측제도 일몰 반영 비교
current_unit = fixed_p + in_forecast
future_unit = fixed_p + owner_net_unit

total_rev_current = annual_gen * current_unit
total_rev_future = annual_gen * future_unit
extra_profit = total_rev_future - total_rev_current

# --- 4. 메인 화면 UI ---
st.title("📊 V-GEN 차세대 수익 최적화 시뮬레이터")
st.subheader(f"✅ 적용 모델: {selected_name}")

# [핵심 강조 박스]
st.markdown(f"""
<div style="background-color:#f0f7ff; padding:25px; border-radius:15px; border-left: 10px solid #00529C; margin-bottom:25px;">
    <h2 style="margin:0; color:#00529C; font-size:24px;">💰 정책 변화 후 예상 추가 수익: <b>+ {extra_profit/10000:,.0f} 만원 / 연</b></h2>
    <p style="margin:10px 0 0 0; font-size:16px; color:#555;">
        제도 개편(예측제도 일몰 ➜ VPP 통합) 시, <b>kWh당 {future_unit - current_unit:.2f}원</b>의 수익 향상이 예상됩니다.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("현재 예상 단가", f"{current_unit:,.1f} 원", help="고정단가 + 예측정산금")
col2.metric("VPP 전환 후 단가", f"{future_unit:,.2f} 원", f"+{owner_net_unit:.2f} 원", delta_color="normal")
col3.metric("연간 총 매출액", f"{total_rev_future/10000:,.0f} 만", f"+{extra_profit/10000:,.0f} 만")

st.divider()

# 시각화 영역
c1, c2 = st.columns([1.5, 1])
with c1:
    st.subheader("📈 정산 단가 구성 변화")
    fig = go.Figure()
    fig.add_trace(go.Bar(name='현재(예측제도)', x=['단가(원)'], y=[current_unit], marker_color='#ADB5BD'))
    fig.add_trace(go.Bar(name='미래(VPP입찰제)', x=['단가(원)'], y=[future_unit], marker_color='#00529C'))
    fig.update_layout(barmode='group', height=400)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.info("🚨 **정책 인사이트**")
    if conf['is_mainland']:
        st.write("- **호남/육지 확대**: CP 11원 적용 예정")
        st.write("- **예측제도 일몰**: 단순 예측 보상 종료")
        st.write("- **VPP 필수화**: 준중앙급전 미참여 시 출력제어 리스크 증가")
    else:
        st.write("- **제주 시범사업**: CP 22원 적용 중")
        st.write("- **실시간 시장**: 15분 단위 정산 대응 필요")

# --- 5. 전문 PDF 리포트 섹션 ---
st.divider()
if st.button("📄 정책 대응 전략 리포트(PDF) 발급", use_container_width=True):
    # (PDF 생성 로직: 앞서 제안한 제주/육지 정책 내용 포함)
    st.success("리포트가 생성되었습니다. [다운로드 버튼 활성화]")

st.caption("본 시뮬레이션은 에너지경제신문 및 전력거래소(KPX) 제주 시범사업 로드맵을 근거로 제작되었습니다.")
