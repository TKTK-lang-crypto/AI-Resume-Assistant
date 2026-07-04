import io
import pdfplumber
import docx
from PyPDF2 import PdfReader


def parse_pdf(file_bytes: bytes) -> str:
    """
    解析 PDF 文件，返回文本内容。
    优先使用 pdfplumber，失败则回退到 PyPDF2。
    """
    try:
        # 尝试用 pdfplumber 解析
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if text.strip():
                return text
    except Exception:
        pass

    # 回退到 PyPDF2
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        raise ValueError(f"PDF 解析失败：{str(e)}")


def parse_docx(file_bytes: bytes) -> str:
    """解析 DOCX 文件，返回文本内容"""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        if text.strip():
            return text
        else:
            raise ValueError("DOCX 文件内容为空或无法解析")
    except Exception as e:
        raise ValueError(f"DOCX 解析失败：{str(e)}")


def parse_txt(file_bytes: bytes) -> str:
    """解析 TXT 文件，返回文本内容（尝试多种编码）"""
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
    for enc in encodings:
        try:
            text = file_bytes.decode(enc)
            if text.strip():
                return text
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别 TXT 文件编码，请保存为 UTF-8 或 GBK 格式")


def parse_resume_file(file_bytes: bytes, file_type: str) -> str:
    """
    统一入口，根据文件类型调用对应解析函数。
    file_type: 'pdf', 'docx', 'txt'
    """
    if file_type == "pdf":
        return parse_pdf(file_bytes)
    elif file_type == "docx":
        return parse_docx(file_bytes)
    elif file_type == "txt":
        return parse_txt(file_bytes)
    else:
        raise ValueError(f"不支持的文件类型：{file_type}")