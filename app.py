import streamlit as st
import os
from fpdf import FPDF
from datetime import datetime

# --- PDF 생성 함수 (경로 체크 및 에러 방지 강화) ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. 폰트 파일 경로 설정 (현재 실행 파일과 같은 위치)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "NanumGothic.ttf")
    
    # 2. 폰트 로드 시도
    font_ready = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("Nanum", "", font_path)
            pdf.set_font("Nanum", "", 12)
            font_name = "Nanum"
            font_ready = True
        except Exception as e:
            st.error(f"폰트 로딩 중 기술적 오류: {e}")
            font_name = "Arial"
    else:
        # 파일이 없을 경우 현재 경로의 파일 목록을 보여줌 (디버깅용)
        files_in_dir = os.listdir(current_dir)
        st.error(f"폰트 파일을 찾을 수 없습니다. (현재 폴더 내 파일: {files_in_dir})")
        font_name = "Arial"

    # 3. PDF 내용 작성 (한글 폰트가 없을 때를 대비한 처리)
    pdf.set_font(font_name, "B" if font_name=="Arial" else "", 20)
    
    if font_ready:
        title_text = "V-GEN 수익 분석 보고서"
        summary_label = "1. 분석 개요"
    else:
        # 폰트가 없으면 한글 대신 영문으로 출력하여 에러 방지
        title_text = "V-GEN Profit Analysis Report"
        summary_label = "1. Analysis Summary"
        st.warning("한글 폰트가 없어 리포트가 영문으로 생성됩니다.")

    pdf.cell(190, 20, title_text, ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font(font_name, "", 12)
    pdf.cell(190, 10, summary_label, ln=True)
    
    # 데이터 출력 (한글 포함 여부에 따라 분기)
    if font_ready:
        pdf.cell(190, 10, f"지역: {data['region']}", ln=True)
    else:
        pdf.cell(190, 10, f"Region: {data['region_eng']}", ln=True)
        
    pdf.cell(190, 10, f"Capacity: {data['cap']} MW", ln=True)
    pdf.cell(190, 10, f"Profit: {data['extra_profit']:,.0f} KRW", ln=True)

    return bytes(pdf.output())

# --- 메인 실행부 ---
# (기존 데이터 프리셋 및 사이드바 로직은 그대로 유지하세요)

# PDF 버튼 부분 수정
st.subheader("리포트 다운로드")
report_params = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "region": selected_region, # 한글 지역명
    "region_eng": "Jeju" if "제주" in selected_region else "Mainland", # 영문 지역명(백업용)
    "cap": cap_mw,
    "extra_profit": owner_extra_profit_yr
}

if st.button("PDF 생성 및 다운로드 준비"):
    try:
        pdf_bytes = create_pdf(report_params)
        st.download_button(
            label="📩 분석 리포트 다운로드",
            data=pdf_bytes,
            file_name=f"VGEN_Report.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"최종 생성 실패: {e}")
