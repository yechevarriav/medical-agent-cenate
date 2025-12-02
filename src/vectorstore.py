from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class MedicalVectorStore:
    def __init__(self, persist_path: str = "data/faiss_index"):
        self.persist_path = persist_path
        self.embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-3-small"
        )
        self.vectorstore = None

        # Intentar cargar índice existente
        if Path(f"{persist_path}/index.faiss").exists():
            print("📂 Cargando índice existente...")
            try:
                self.vectorstore = FAISS.load_local(
                    persist_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ Índice cargado correctamente")
            except Exception as e:
                print(f"⚠️  Error cargando índice: {e}")
                self.vectorstore = None

    def add_documents(self, documents: List[Dict[str, str]]):
        """Añade documentos al vector store"""
        if not documents:
            print("⚠️  No hay documentos para añadir")
            return

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        all_texts = []
        all_metadatas = []

        print("📝 Procesando chunks...")
        for doc in documents:
            chunks = text_splitter.split_text(doc['content'])
            print(f"   - {doc['source']}: {len(chunks)} chunks")

            for chunk_idx, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_metadatas.append({
                    "source": doc['source'],
                    "chunk_id": chunk_idx,
                    **doc.get('metadata', {})
                })

        print(f"\n🔄 Creando embeddings para {len(all_texts)} chunks...")

        # Crear vectorstore
        self.vectorstore = FAISS.from_texts(
            texts=all_texts,
            embedding=self.embeddings,
            metadatas=all_metadatas
        )

        # Guardar índice
        os.makedirs(self.persist_path, exist_ok=True)
        self.vectorstore.save_local(self.persist_path)

        print(f"✅ Vectorstore creado y guardado en {self.persist_path}")

    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """Busca documentos similares"""
        if not self.vectorstore:
            raise ValueError("❌ Vectorstore no inicializado. Ejecuta add_documents() primero.")

        docs_and_scores = self.vectorstore.similarity_search_with_score(
            query, k=n_results
        )

        results = []
        for doc, score in docs_and_scores:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(1 / (1 + score))  # Convertir distancia a score
            })

        return results

# Script de ingesta
if __name__ == "__main__":
    from data_processor import PDFProcessor

    print("="*80)
    print("🚀 INICIANDO PROCESAMIENTO DE DOCUMENTOS")
    print("="*80)

    # 1. Procesar PDFs
    processor = PDFProcessor()
    documents = processor.process_all_pdfs()

    if not documents:
        print("\n❌ ERROR: Copia tus PDFs a la carpeta data/raw/")
        exit(1)

    # 2. Crear vector store
    print("\n" + "="*80)
    print("🔄 CREANDO VECTOR STORE")
    print("="*80)
    vectorstore = MedicalVectorStore()
    vectorstore.add_documents(documents)

    # 3. Test de búsqueda
    print("\n" + "="*80)
    print("🔍 TEST DE BÚSQUEDA")
    print("="*80)

    test_queries = [
        "¿Cómo atender pacientes crónicos con diabetes?",
        "¿Qué es una telecolposcopía síncrona?",
        "¿Quiénes son los responsables del procedimiento?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        results = vectorstore.search(query, n_results=2)

        for j, result in enumerate(results, 1):
            print(f"\n📄 Resultado {j}:")
            print(f"   Fuente: {result['metadata']['source']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Contenido: {result['content'][:150]}...")

    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)
