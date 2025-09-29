import fitz  # PyMuPDF
from PyPDF2 import PdfWriter, PdfReader
from PyQt6.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox
)
from geradorDocumentos import Geradora  # sua classe de geração de arquivos


class LogicaPagina:
    def __init__(self):
        self.caminho_pdf = None       # caminho do PDF atual
        self.ordem_paginas = []       # ordem atual das páginas
        self.descricao_paginas = {}   # descrições opcionais das páginas
        self.doc = None               # documento aberto em memória

    # -----------------------------
    # ABRIR DOCUMENTO
    # -----------------------------
    def abrir_documento(self, parent):
        """Abre um diálogo para escolher e carregar um PDF"""
        arquivo, _ = QFileDialog.getOpenFileName(
            parent, "Abrir PDF", "", "Arquivos PDF (*.pdf)"
        )
        if not arquivo:
            return False

        self.caminho_pdf = arquivo
        self.doc = fitz.open(arquivo)
        self.ordem_paginas = list(range(len(self.doc)))
        return True

    # -----------------------------
    # SALVAR DOCUMENTO
    # -----------------------------
    def salvar_documento(self, parent):
        """Abre diálogo de salvar e exporta em vários formatos"""
        if not self.caminho_pdf:
            QMessageBox.warning(parent, "Aviso", "Nenhum documento carregado.")
            return False

        # Diálogo para escolher formato
        dialog = QDialog(parent)
        dialog.setWindowTitle("Escolher formato")
        dialog.setFixedSize(300, 150)

        layout = QVBoxLayout(dialog)
        label = QLabel("Selecione o formato para salvar:")
        layout.addWidget(label)

        combo_formatos = QComboBox()
        combo_formatos.addItems(["PDF", "PNG", "JPG", "DOCX", "TXT"])
        layout.addWidget(combo_formatos)

        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.clicked.connect(dialog.accept)
        layout.addWidget(btn_confirmar)

        if dialog.exec():
            formato = combo_formatos.currentText()
            filtro = f"{formato} (*.{formato.lower()})"
            novo_caminho, _ = QFileDialog.getSaveFileName(
                parent, f"Salvar como {formato}", "", filtro
            )
            if not novo_caminho:
                return False

            # Usa a classe Geradora para criar os arquivos
            geradora = Geradora(self.caminho_pdf, self.ordem_paginas, parent)

            if formato == "PDF":
                geradora.salvar_como_pdf(novo_caminho)
            elif formato in ["PNG", "JPG"]:
                geradora.salvar_como_imagem(novo_caminho, formato)
            elif formato == "DOCX":
                geradora.salvar_como_docx(novo_caminho)
            elif formato == "TXT":
                geradora.salvar_como_txt(novo_caminho)

            QMessageBox.information(
                parent, "Sucesso", f"Documento salvo em:\n{novo_caminho}"
            )

            # Atualiza caminho se for PDF
            if formato == "PDF":
                self.atualizar_pdf(novo_caminho)
                return True

        return False

    def atualizar_pdf(self, novo_caminho):
        """Atualiza o PDF atual após salvar"""
        self.caminho_pdf = novo_caminho
        self.doc = fitz.open(novo_caminho)
        self.ordem_paginas = list(range(len(self.doc)))

    # -----------------------------
    # MOSTRAR TEXTO
    # -----------------------------
    def mostrar_texto(self):
        """Retorna o texto extraído do PDF"""
        if not self.doc:
            return ""

        texto_total = ""
        for idx in self.ordem_paginas:
            pagina = self.doc[idx]
            texto_total += f"--- Página {idx+1} ---\n"
            texto_total += pagina.get_text("text") + "\n\n"

        return texto_total.strip()

    # -----------------------------
    # RENDERIZAR PÁGINAS
    # -----------------------------
    def renderizar_paginas(self, zoom=1.0):
        """Retorna uma lista de imagens (pixmaps) das páginas"""
        if not self.doc:
            return []

        imagens = []
        for idx in self.ordem_paginas:
            pagina = self.doc[idx]
            mat = fitz.Matrix(zoom, zoom)
            pix = pagina.get_pixmap(matrix=mat)
            imagens.append(pix)
        return imagens

    # -----------------------------
    # LÓGICA DE PÁGINAS
    # -----------------------------
    def mover_para_cima(self, index):
        if index > 0:
            self.ordem_paginas[index], self.ordem_paginas[index-1] = \
                self.ordem_paginas[index-1], self.ordem_paginas[index]

    def mover_para_baixo(self, index):
        if index < len(self.ordem_paginas) - 1:
            self.ordem_paginas[index], self.ordem_paginas[index+1] = \
                self.ordem_paginas[index+1], self.ordem_paginas[index]

    def excluir_pagina(self, index):
        if 0 <= index < len(self.ordem_paginas):
            self.ordem_paginas.pop(index)

    def adicionar_descricao(self, pagina_num, descricao):
        self.descricao_paginas[pagina_num] = descricao

    def obter_ordem(self):
        return self.ordem_paginas

    def obter_descricao(self, pagina_num):
        return self.descricao_paginas.get(pagina_num, f"Página {pagina_num+1}")
