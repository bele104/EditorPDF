import fitz  # PyMuPDF
from docx import Document

class Geradora:
    def __init__(self, caminho_pdf, ordem_paginas, parent=None):
        """
        caminho_pdf: caminho do PDF a ser manipulado
        ordem_paginas: lista de índices de páginas
        parent: janela PyQt (opcional, só se precisar usar QMessageBox)
        """
        self.caminho_pdf = caminho_pdf
        self.ordem_paginas = ordem_paginas
        self.parent = parent  

    def salvar_como_pdf(self, caminho_salvar):
        """Salva o PDF reordenado no caminho especificado"""
        try:
            doc_original = fitz.open(self.caminho_pdf)
            novo_doc = fitz.open()
            for i in self.ordem_paginas:
              
                novo_doc.insert_pdf(doc_original, from_page=i, to_page=i)
            novo_doc.save(caminho_salvar)
            novo_doc.close()
            doc_original.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar PDF: {e}")
            return False
        
    def salvar_como_imagem(self, caminho_base, formato="PNG"):
        """
        Salva cada página do PDF como imagem no formato especificado.
        Exemplo: caminho_base = 'saida/arquivo' gera arquivos
        arquivo_pagina_1.png, arquivo_pagina_2.png, etc.
        """
        try:
            doc = fitz.open(self.caminho_pdf)
            for i, pagina in enumerate(self.ordem_paginas):
                pix = doc.load_page(pagina).get_pixmap()
                caminho_img = f"{caminho_base}_pagina_{i+1}.{formato.lower()}"
                pix.save(caminho_img)
            doc.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar imagens: {e}")
            return False

    def salvar_como_docx(self, caminho_docx):
        """Salva o PDF como arquivo Word (DOCX)"""
        try:
            doc_pdf = fitz.open(self.caminho_pdf)
            documento = Document()

            for i, pagina in enumerate(self.ordem_paginas):
                texto = doc_pdf.load_page(pagina).get_text("text")
                documento.add_paragraph(texto)
                documento.add_page_break()

            documento.save(caminho_docx)
            doc_pdf.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar DOCX: {e}")
            return False

    def salvar_como_txt(self, caminho_txt):
        """Salva o PDF como arquivo TXT"""
        try:
            doc = fitz.open(self.caminho_pdf)
            with open(caminho_txt, "w", encoding="utf-8") as f:
                for pagina in self.ordem_paginas:
                    texto = doc.load_page(pagina).get_text("text")
                    f.write(texto + "\n\n")
            doc.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar TXT: {e}")
            return False
