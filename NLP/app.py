import fitz  # PyMuPDF
import re
from flask import Flask, request, render_template
from PIL import Image
import pytesseract

# Tesseract OCR 경로 설정 (설치된 Tesseract 실행 파일 경로를 설정하세요)
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Step 1: PDF Text Extraction
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        # 텍스트가 비어 있으면 OCR 시도
        if not text.strip():
            print("PDF is likely image-based, attempting OCR...")
            text = extract_text_from_pdf_with_ocr(pdf_path)
        return text
    except Exception as e:
        print("Error extracting text:", e)
        return ""

# OCR을 활용한 텍스트 추출
def extract_text_from_pdf_with_ocr(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_number, page in enumerate(doc):
        # 페이지를 이미지로 변환
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 디버깅용 이미지 저장
        img.save(f"page_{page_number}.png")
        print(f"Saved page_{page_number}.png for debugging")

        # OCR 수행
        page_text = pytesseract.image_to_string(img, lang="eng")
        print(f"Extracted text from page {page_number}:\n", page_text)
        text += page_text
    doc.close()
    return text

# Step 2: Parameter Extraction
def extract_parameters(text):
    parameters = []

    # 정규식을 이용한 데이터 추출
    voltage_matches = re.findall(r"VDD\s+Local Power\s+(\d+\.\d+V\s+to\s+\d+\.\d+V)", text, re.IGNORECASE)
    temperature_matches = re.findall(r"Operating Temperature\s+([-+]?\d+°C\s+to\s+[-+]?\d+°C)", text, re.IGNORECASE)
    power_matches = re.findall(r"Active Current.*?(\d+\.\d+mA)", text, re.IGNORECASE)

    # 데이터 병합 (부족한 값은 N/A로 처리)
    max_length = max(len(voltage_matches), len(temperature_matches), len(power_matches))
    for i in range(max_length):
        parameters.append({
            "Voltage": voltage_matches[i] if i < len(voltage_matches) else "N/A",
            "Temperature": temperature_matches[i] if i < len(temperature_matches) else "N/A",
            "Power": power_matches[i] if i < len(power_matches) else "N/A",
        })

    return parameters

# Step 3: Flask Web App Setup
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("pdf_files")
    all_parameters = []

    for file in uploaded_files:
        # PDF 텍스트 추출
        text = extract_text_from_pdf(file.stream)
        print("PDF Text Extracted:\n", text)  # PDF에서 추출한 텍스트 확인

        # 파라미터 추출
        parameters = extract_parameters(text)
        print("Extracted Parameters:", parameters)  # 추출된 데이터 확인

        all_parameters.extend(parameters)

    return render_template('results.html', parameters=all_parameters)

# Main Execution
if __name__ == '__main__':
    app.run(debug=True)
