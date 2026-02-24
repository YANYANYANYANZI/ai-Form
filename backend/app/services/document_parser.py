import fitz  # PyMuPDF 的包名
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """从 PDF 字节流中提取纯文本，尽量简单"""
    try:
        # 在内存中直接打开 PDF 字节流
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"❌ PDF 解析失败: {e}")
        return ""