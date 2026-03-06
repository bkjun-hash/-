import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="V-GEN 제주 시범사업 정산 시뮬레이터", layout="wide")

# 스타일링
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stMetric { border: 1px solid #e1e4e8; padding: 15px; border-radius: 12px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📑 브이젠(V-GEN) 제주 시범사업 공식 정산 시뮬레이터")
st.info("전력거래소(KPX) 정산 교육 자료의 이중정산체계 및 재생에너지 입찰제도 공식 항목을 적용했습니다.")

# --- 사이드바: 입력 섹션 ---
with st.sidebar:
    st.header("1️⃣ 발전소 및 기본 정보")
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간 (시간)", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("기존 고정가격 단가 (원/kWh)", min_value=100, value=180)
    
    st.divider()
    
    st.header("2️⃣ 5대 공식 정산 단가 (원/kWh)")
    in_mep = st.number_input("전력량정산금 (MEP) 증분", value=0.5)
    in_cp = st.number_input("용량정산금 (CP)", value=5.5)
    in_map = st.number_input("기대이익정산금 (MAP)", value=2.0)
    in_mwp = st.number_input("변동비보전정산금 (MWP)", value=0.1)
    in_imbp = st.number_input("임밸런스 페널티 (IMBP)", value=0.3)
    
    st.divider()
    
    st.header("3️⃣ 수수료 및 배분 설정 (%)")
    vgen_fee_rate = st.slider("브이젠 수수료율 (%)", 0, 30, 20) / 100
    partner_fee_rate = st.slider("영업 채널 배분율 (%)", 0, 20, 10) / 100

# --- 핵심 계산 로직 ---
# 1. 연간 발전량
annual_gen = cap_mw * 1000 * gen_time * 365

# 2. 5대 정산 단가 합계 (Gross 추가 단가) - 요청하신 항목
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp

# 3. 수익 배분 계산 (Net)
vgen_gross_fee_unit = gross_extra_unit * vgen_fee_rate          # kWh당 브이젠 총 수수료
owner_net_extra_unit = gross_extra_unit - vgen_gross_fee_unit   # kWh당 사업자 순 추가수익

# 4. 연간 총액 계산
non_participate_rev = annual_gen * fixed_p                      # 미참여 시 수익
owner_extra_profit_yr = annual_gen * owner_net_extra_unit       # 사업자 연간 순이익 증분
final_total_rev_yr = non_participate_rev + owner_extra_profit_yr # 참여 시 최종 수익

# --- 결과 출력 ---
st.subheader("💰 단가 합산 및 수익 비교")
# 상단 지표 4개 배치
c1, c2, c3, c4 = st.columns(4)
with c1:
    # 요청하신 항목: 5대 정산 항목의 총 합계 (세전)
    st.metric("5대 정산 단가 합계", f"{gross_extra_unit:.2f} 원/kWh", "세전 추가 단가")
with c2:
    # 사업자가 수수료 떼고 실제로 받는 단가
    st.metric("사업자 순 추가단가", f"{owner_net_extra_unit:.2f} 원/kWh", "수수료 차감 후")
with c3:
    st.metric("참여 시 최종 단가", f"{fixed_p + owner_net_extra_unit:.2f} 원/kWh", f"기본 {fixed_p}원")
with c4:
    st.metric("사업자 연 순증분", f"{owner_extra_profit_yr:,.0f} 원")

st.divider()

col_l, col_r = st.columns([1.5, 1])

with col_l:
    st.subheader("📊 수익 시나리오 비교")
    compare_df = pd.DataFrame({
        "구분": ["미 참여 (기본)", "브이젠 참여 (최종)"],
        "단가 (원/kWh)": [fixed_p, fixed_p + owner_net_extra_unit]
    })
    st.bar_chart(compare_df, x="구분", y="단가 (원/kWh)", color="#1F77B4")

    st.subheader("💸 상세 배분 내역 (연간 총액)")
    # 브이젠 및 파트너 수익 계산
    partner_comm_yr = (annual_gen * vgen_gross_fee_unit) * partner_fee_rate
    vgen_net_yr = (annual_gen * vgen_gross_fee_unit) - partner_comm_yr
    
    fee_data = pd.DataFrame({
        "항목": ["발전사업자 추가 순익", "브이젠 운영 순수익", "영업 채널 수수료"],
        "금액": [f"{owner_extra_profit_yr:,.0f} 원", f"{vgen_net_yr:,.0f} 원", f"{partner_comm_yr:,.0f} 원"]
    })
    st.table(fee_data)

with col_r:
    st.subheader("📋 5대 정산 항목 구성 (원/kWh)")
    # 5대 항목 단가 시각화
    item_df = pd.DataFrame({
        "공식 항목": ["전력량(MEP)", "용량(CP)", "기대이익(MAP)", "변동비(MWP)", "페널티(IMBP)"],
        "단가": [in_mep, in_cp, in_map, in_mwp, -in_imbp]
    })
    st.bar_chart(item_df, x="공식 항목", y="단가", color="#FF7F0E")

st.success(f"✅ **영업 포인트:** 입찰 시장을 통해 총 **{gross_extra_unit:.2f}원/kWh**의 추가 재원이 발생하며, 수수료 제외 후 사장님께는 **{owner_net_extra_unit:.2f}원/kWh**의 순수익이 돌아갑니다.")
