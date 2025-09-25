import sys
import os
import tempfile
import fitz  # PyMuPDF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout,
    QWidget, QPushButton, QListWidget, QHBoxLayout, QMessageBox,
    QListWidgetItem, QLabel, QComboBox, QDialog, QTextEdit
)
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument
from conversor import ConversorArquivo
from geradorDocumentos import Geradora


class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDFaça café")
        self.setGeometry(100, 100, 1000, 700)

        # Visualizador PDF
        self.pdf_view = QPdfView(self)
        self.pdf_doc = QPdfDocument(self)
        self.pdf_view.setDocument(self.pdf_doc)

        # Lista lateral de páginas
        self.lista_paginas = QListWidget()
        self.lista_paginas.setFixedWidth(250)

        # Botões
        self.btn_abrir = QPushButton("Abrir Documento")
        self.btn_abrir.clicked.connect(self.abrir_pdf)

        self.btn_salvar = QPushButton("Salvar Documento")
        self.btn_salvar.clicked.connect(self.salvar_pdf)

        self.texto = QPushButton("Extrair Texto")
        self.texto.clicked.connect(self.mostrar_texto_pdf)

        # Layout lateral
        layout_esquerda = QVBoxLayout()
        layout_esquerda.addWidget(self.btn_abrir)
        layout_esquerda.addWidget(self.lista_paginas)
        layout_esquerda.addWidget(self.btn_salvar)
        layout_esquerda.addWidget(self.texto)

        # Layout principal
        layout_principal = QHBoxLayout()
        layout_principal.addLayout(layout_esquerda)
        layout_principal.addWidget(self.pdf_view)
        self.layout_principal = layout_principal

        container = QWidget()
        container.setLayout(layout_principal)
        self.setCentralWidget(container)

        # Variáveis de controle
        self.caminho_pdf = None
        self.ordem_paginas = []
        self.conversor = ConversorArquivo()  # instancia do conversor

    # ------------------------------
    # Abrir PDF
    # ------------------------------
    def abrir_pdf(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", None)
        if not caminho:
            return

        processado = self.conversor.processar_arquivo(caminho)
        if not processado or not os.path.exists(processado):
            QMessageBox.critical(self, "Erro", "Não foi possível abrir ou converter o arquivo.")
            return

        self.caminho_pdf = processado
        self.pdf_doc.load(processado)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomFactor(1.0)

        doc = fitz.open(processado)
        self.ordem_paginas = list(range(len(doc)))
        self.atualizar_lista()
        doc.close()

    # ------------------------------
    # Lista de páginas
    # ------------------------------
    def adicionar_item_lista(self, index, numero_pagina):
        item_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        label = QLabel(f"Página {numero_pagina + 1}")
        layout.addWidget(label)

        # Botão ↑
        if index > 0:
            btn_up = QPushButton("↑")
            btn_up.setFixedWidth(30)
            btn_up.clicked.connect(lambda _, i=index: self.mover_para_cima_indice(i))
            layout.addWidget(btn_up)

        # Botão ↓
        if index < len(self.ordem_paginas) - 1:
            btn_down = QPushButton("↓")
            btn_down.setFixedWidth(30)
            btn_down.clicked.connect(lambda _, i=index: self.mover_para_baixo_indice(i))
            layout.addWidget(btn_down)

        item_widget.setLayout(layout)

        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())
        self.lista_paginas.addItem(item)
        self.lista_paginas.setItemWidget(item, item_widget)

    def atualizar_lista(self):
        self.lista_paginas.clear()
        for index, pagina in enumerate(self.ordem_paginas):
            self.adicionar_item_lista(index, pagina)

    def mover_para_cima_indice(self, index):
        if index > 0:
            self.ordem_paginas[index], self.ordem_paginas[index - 1] = self.ordem_paginas[index - 1], self.ordem_paginas[index]
            self.atualizar_lista()
            self.atualizar_visualizacao_pdf()

    def mover_para_baixo_indice(self, index):
        if index < len(self.ordem_paginas) - 1:
            self.ordem_paginas[index], self.ordem_paginas[index + 1] = self.ordem_paginas[index + 1], self.ordem_paginas[index]
            self.atualizar_lista()
            self.atualizar_visualizacao_pdf()

    # ------------------------------
    # Atualizar visualização
    # ------------------------------
    def atualizar_visualizacao_pdf(self):
        if not self.caminho_pdf:
            return

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name

        doc_original = fitz.open(self.caminho_pdf)
        novo_doc = fitz.open()

        for i in self.ordem_paginas:
            novo_doc.insert_pdf(doc_original, from_page=i, to_page=i)

        novo_doc.save(temp_path)
        novo_doc.close()
        doc_original.close()

        self.pdf_doc.load(temp_path)
        self.pdf_view.setDocument(self.pdf_doc)

    # ------------------------------
    # Salvar PDF/Imagem
    # ------------------------------
    def salvar_pdf(self):
        if not self.caminho_pdf:
            QMessageBox.warning(self, "Aviso", "Nenhum documento carregado.")
            return

        # Janela de diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Escolher formato")
        dialog.setFixedSize(300, 150)

        layout = QVBoxLayout()
        label = QLabel("Selecione o formato para salvar:")
        layout.addWidget(label)

        combo_formatos = QComboBox()
        combo_formatos.addItems(["PDF", "PNG", "JPG", "DOCX", "TXT"])
        layout.addWidget(combo_formatos)

        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.clicked.connect(dialog.accept)
        layout.addWidget(btn_confirmar)

        dialog.setLayout(layout)

        if dialog.exec():
            formato = combo_formatos.currentText()
            filtro = f"{formato} (*.{formato.lower()})"
            novo_caminho, _ = QFileDialog.getSaveFileName(self, f"Salvar como {formato}", "", filtro)
            if not novo_caminho:
                return

            geradora = Geradora(self.caminho_pdf, self.ordem_paginas, self)

            if formato == "PDF":
                geradora.salvar_como_pdf(novo_caminho)
            elif formato in ["PNG", "JPG"]:
                geradora.salvar_como_imagem(novo_caminho, formato)
            elif formato == "DOCX":
                 geradora.salvar_como_docx(novo_caminho)
            elif formato == "TXT":
                geradora.salvar_como_txt(novo_caminho)

        QMessageBox.information(self,f"Documento salvo em{formato}",f"Documento salvo no {novo_caminho}")
        self.pdf_doc.load(None)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomFactor(1.0)
        doc = fitz.open(None)
        self.ordem_paginas = list(range(len(doc)))
        self.atualizar_lista()
        doc.close()
    # ------------------------------
    # Mostrar texto extraído
    # ------------------------------
    def mostrar_texto_pdf(self):
        if not self.caminho_pdf:
            QMessageBox.warning(self, "Aviso", "Nenhum documento carregado.")
            return
        doc = fitz.open(self.caminho_pdf)
        texto = ""
        for pagina in doc:
            texto += pagina.get_text() + "\n\n"
        doc.close()

        self.editor_texto = QTextEdit()
        self.editor_texto.setPlainText(texto)
        self.editor_texto.setReadOnly(True)

        # Oculta o visualizador PDF e mostra o texto
        self.pdf_view.hide()
        self.layout_principal.addWidget(self.editor_texto)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = PDFEditor()
    janela.show()
    sys.exit(app.exec())
