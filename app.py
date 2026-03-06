import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="브이젠 VPP 수익 시뮬레이터", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 브이젠(V-GEN) VPP 입찰 수익 시뮬레이터")
st.caption("제주 1위 기술력 기반 육지 태양광/풍력 수익 예측 도구")

# --- 사이드바: 입력 변수 ---
with st.sidebar:
    st.header("📍 발전소 정보 입력")
    capacity_mw = st.number_input("설비 용량 (MW)", min_value=0.1, max_value=100.0, value=1.0, step=0.1)
    fixed_price = st.number_input("고정가격계약 단가 (원/kWh)", min_value=100, max_value=250, value=180)
    
    resource_type = st.radio("자원 및 지역 선택", ["육지 태양광", "제주 풍력"])
    
    st.divider()
    st.header("⚙️ 고급 설정 (수익 계수)")
    if resource_type == "육지 태양광":
        util_rate = st.slider("이용률 (%)", 10, 20, 15) / 100
        cp_val = 5.5   # 용량정산금 예상
        map_val = 2.0  # 부가정산금 예상
        imbp_val = 0.3 # 페널티 예상
    else:
        util_rate = st.slider("이용률 (%)", 20, 40, 25) / 100
        cp_val = 11.0
        map_val = 5.0
        imbp_val = 1.6

# --- 계산 로직 ---
# 연간 발전량
annual_gen = capacity_mw * 1000 * 24 * 365 * util_rate
# kWh당 추가 단가 (CP + MAP - IMBP)
net_extra_unit = cp_val + map_val - imbp_val
# 연간 총 추가 수익
total_alpha = annual_gen * net_extra_unit
# 수익 배분 (80% : 20%)
owner_share = total_alpha * 0.8
vgen_share = total_alpha * 0.2
partner_share = vgen_share * 0.1  # 브이젠 몫의 10%

# --- 결과 화면 ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("연간 사업자 추가 수익", f"{owner_share:,.0f} 원", f"+{net_extra_unit:.1f} 원/kWh")
with col2:
    st.metric("20년 누적 추가 수익", f"{owner_share * 20:,.0f} 원")
with col3:
    st.metric("영업 파트너 연 수수료", f"{partner_share:,.0f} 원", "Passive Income")

st.divider()

# --- 상세 분석 그래프 ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 20년 누적 매출 비교")
    base_revenue_20y = annual_gen * fixed_price * 20
    vpp_revenue_20y = base_revenue_20y + (owner_share * 20)
    
    chart_data = pd.DataFrame({
        "구분": ["기존 고정계약", "브이젠 입찰 참여"],
        "누적 매출 (억원)": [base_revenue_20y / 1e8, vpp_revenue_20y / 1e8]
    })
    st.bar_chart(data=chart_data, x="구분", y="누적 매출 (억원)", color="#007bff")

with col_right:
    st.subheader("💰 추가 수익 구성")
    source_data = pd.DataFrame({
        "항목": ["용량요금(CP)", "부가정산(MAP)", "페널티(IMBP) 차감"],
        "금액 (원/kWh)": [cp_val, map_val, -imbp_val]
    })
    st.table(source_data)

st.info(f"💡 **PM 가이드:** 본 시뮬레이션은 브이젠의 제주 풍력 수익률 8% 증대 레퍼런스를 육지 환경에 맞춰 보수적으로 산출한 결과입니다.")
