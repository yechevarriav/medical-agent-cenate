import pypdf
from pathlib import Path
from typing import List, Dict

class PDFProcessor:
    def __init__(self, pdf_folder: str = "data/raw"):
        self.pdf_folder = Path(pdf_folder)

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extrae texto de un PDF"""
        try:
            reader = pypdf.PdfReader(pdf_path)
            text = ""
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                text += f"\n--- Página {page_num} ---\n{page_text}\n"
            return text
        except Exception as e:
            print(f"❌ Error procesando {pdf_path.name}: {e}")
            return ""

    def process_all_pdfs(self) -> List[Dict[str, str]]:
        """Procesa todos los PDFs de la carpeta"""
        documents = []

        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        if not pdf_files:
            print(f"⚠️  No se encontraron PDFs en {self.pdf_folder}")
            return documents

        for pdf_file in pdf_files:
            print(f"📄 Procesando: {pdf_file.name}")
            text = self.extract_text_from_pdf(pdf_file)

            if text:
                documents.append({
                    "source": pdf_file.stem,
                    "content": text,
                    "metadata": {
                        "filename": pdf_file.name,
                        "pages": len(pypdf.PdfReader(pdf_file).pages)
                    }
                })
                print(f"   ✅ {len(text)} caracteres extraídos")

        return documents

if __name__ == "__main__":
    processor = PDFProcessor()
    docs = processor.process_all_pdfs()
    print(f"\n✅ Total procesados: {len(docs)} documentos")

    for doc in docs:
        print(f"   - {doc['source']}: {doc['metadata']['pages']} páginas")
