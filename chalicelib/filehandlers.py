from PyPDF2 import PdfFileReader
import docx

def get_pdf_content(file):
    pdf = PdfFileReader(file)
    n_pages = pdf.getNumPages()
    text = ''

    for i in range(n_pages):
        page = pdf.getPage(i)
        text += page.extractText()
    return text


def get_doc_content(file):
    doc = docx.Document(file)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return "\n".join(fullText)
