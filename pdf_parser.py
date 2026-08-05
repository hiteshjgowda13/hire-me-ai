from pypdf import PdfReader

def read_pdf(file_path):
    reader = PdfReader(file_path)
    #parse into text get pdf parse into text using pypdf

    text =""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def read_resume(file_path):
    if file_path.suffix.lower() == ".pdf":
        return read_pdf(file_path)
    else:
        return ".pdf is accepted nothing else"