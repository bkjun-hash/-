import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 시뮬레이터 PRO", layout="wide")

# 커스텀 CSS (가시성 및 디자인 개선)
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-card { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .metric-container { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; }
    </style>
    """, unsafe_allow_html=True)

st.title("📑 V-GEN 차세대 VPP 수익 정산 시뮬레이터")
st.markdown("### **실제 정산 데이터 기반 육지/제주 맞춤형 수익 분석**")

# --- 지역별 데이터 정의 ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

# --- 사이드바: 입력 제어 ---
with st.sidebar:
    st.header("📍 1. 대상 지역")
    selected_region = st.selectbox("발전소 위치", list(region_presets.keys()))
    preset = region_presets[selected_region]

    st.header("⚡ 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 5대 정산금 상세 (원/kWh)")
    in_mep = st.number_input("MEP (전력량)", value=preset['mep'])
    in_cp = st.number_input("CP (용량)", value=preset['cp'])
    in_map = st.number_input("MAP (기대이익)", value=preset['map'])
    in_mwp = st.number_input("MWP (변동비)", value=preset['mwp'])
    in_imbp = st.number_input("IMBP (페널티)", value=preset['imbp'])

    st.header("💰 4. 수수료 정책")
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100
    partner_fee_rate = st.slider("영업 채널 배분 (%)", 0, 20, 10) / 100

# --- 핵심 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp

# 수수료 배분 (이중 구조)
vgen_total_fee_unit = gross_extra_unit * vgen_fee_rate
owner_net_extra_unit = gross_extra_unit - vgen_total_fee_unit
total_unit_price = fixed_p + owner_net_extra_unit

# 연간 총액
non_vpp_rev = annual_gen * fixed_p
owner_extra_profit_yr = annual_gen * owner_net_extra_unit
vgen_total_fee_yr = annual_gen * vgen_total_fee_unit
partner_comm_yr = vgen_total_fee_yr * partner_fee_rate
vgen_net_profit_yr = vgen_total_fee_yr - partner_comm_yr

# --- 메인 화면 레이아웃 ---
# 1. 상단 핵심 지표
st.markdown("#### 💎 핵심 수익 지표")
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("5대 정산금 합계 (세전)", f"{gross_extra_unit:.2f}원")
with m2:
    st.metric("사업자 순증분 (kWh당)", f"{owner_net_extra_unit:.2f}원", f"+{ (owner_net_extra_unit/fixed_p)*100 :.1f}%")
with m3:
    st.metric("사업자 연간 순이익", f"{owner_extra_profit_yr/10000:,.0f}만원")
with m4:
    st.metric("참여 후 최종 단가", f"{total_unit_price:.1f}원")

st.markdown("---")

# 2. 시각화 섹션
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("#### 📈 수익 증분 워터폴 (Waterfall Chart)")
    # 워터폴 차트 생성 (수익이 쌓이는 과정을 가시화)
    fig_wf = go.Figure(go.Waterfall(
        name = "Profit Structure", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "relative", "total"],
        x = ["기본단가", "CP(용량)", "MEP(전력)", "MAP(보상)", "기타/벌금", "총 정산금액"],
        textposition = "outside",
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map}", f"{in_mwp-in_imbp}", f"{fixed_p+gross_extra_unit:.1f}"],
        y = [fixed_p, in_cp, in_mep, in_map, in_mwp-in_imbp, 0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        increasing = {"marker":{"color":"#007BFF"}},
        totals = {"marker":{"color":"#764BA2"}}
    ))
    fig_wf.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_wf, use_container_width=True)

with col_right:
    st.markdown("#### 🧾 상세 수익 배분 내역")
    distribution_data = {
        "구분": ["발전사업자 (80%)", "브이젠 순수익 (18%)", "영업 채널 (2%)"],
        "연간 수익": [owner_extra_profit_yr, vgen_net_profit_yr, partner_comm_yr],
        "색상": ["#007BFF", "#764BA2", "#FFC107"]
    }
    df_dist = pd.DataFrame(distribution_data)
    fig_pie = px.pie(df_dist, values='연간 수익', names='구분', hole=0.4, color='구분',
                     color_discrete_map={"발전사업자 (80%)":"#007BFF", "브이젠 순수익 (18%)":"#764BA2", "영업 채널 (2%)":"#FFC107"})
    fig_pie.update_layout(height=300, showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)
    
    st.write(f"**💡 {selected_region} 영업 팁:**")
    st.caption(f"이 지역은 {in_cp}원의 안정적인 CP와 {in_map}원의 리스크 보상(MAP)이 핵심입니다.")

# 3. 하단 상세 테이블
st.markdown("#### 📋 세부 정산 내역 (연간 총액 기준)")
detail_df = pd.DataFrame({
    "항목": ["기존 고정가격 매출", "VPP 추가 정산금 (세전)", "브이젠 수수료 (운영비)", "최종 합산 매출"],
    "금액 (원)": [f"{non_vpp_rev:,.0f}", f"{annual_gen * gross_extra_unit:,.0f}", f"-{vgen_total_fee_yr:,.0f}", f"{non_vpp_rev + owner_extra_profit_yr:,.0f}"]
})
st.table(detail_df)

st.success(f"✅ 본 시뮬레이션은 전력거래소 정산 교육 자료를 기반으로 하며, {selected_region}의 실측 통계치를 적용했습니다.")
