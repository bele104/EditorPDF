import sys
import os
import fitz  # PyMuPDF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget,
    QPushButton, QListWidget, QHBoxLayout, QMessageBox, QListWidgetItem,
    QLabel, QScrollArea, QTextEdit
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from conversor import ConversorArquivo
from geradorDocumentos import Geradora

class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conversor = ConversorArquivo()
        self.setWindowTitle("PDFaça café")
        self.setGeometry(100, 100, 1000, 700)

        # Variáveis de controle
        self.caminho_pdf = None
        self.ordem_paginas = []
        self.descricao_paginas = {}

        # ------------------------------
        # Painel ESQUERDO (botões + lista)
        # ------------------------------
        self.btn_abrir = QPushButton("Abrir Documento")
        self.btn_salvar = QPushButton("Salvar Documento")
        self.btn_extrair = QPushButton("Extrair Texto")
        self.btn_excluir = QPushButton("Excluir Página")

        self.lista_paginas = QListWidget()
        self.lista_paginas.setFixedWidth(200)
        self.lista_paginas.itemClicked.connect(self.ir_para_pagina)

        layout_esquerda = QVBoxLayout()
        layout_esquerda.addWidget(self.btn_abrir)
        layout_esquerda.addWidget(self.btn_salvar)
        layout_esquerda.addWidget(self.btn_extrair)
        layout_esquerda.addWidget(self.btn_excluir)
        layout_esquerda.addSpacing(20)
        layout_esquerda.addWidget(QLabel("Páginas"))
        layout_esquerda.addWidget(self.lista_paginas)
        layout_esquerda.addStretch()

        # ------------------------------
        # Centro (scroll das páginas)
        # ------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.paginas_widget = QWidget()
        self.paginas_layout = QVBoxLayout()
        self.paginas_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.paginas_widget.setLayout(self.paginas_layout)

        self.scroll_area.setWidget(self.paginas_widget)

        # ------------------------------
        # Layout principal
        # ------------------------------
        layout_principal = QHBoxLayout()
        layout_principal.addLayout(layout_esquerda, 1)
        layout_principal.addWidget(self.scroll_area, 4)

        container = QWidget()
        container.setLayout(layout_principal)
        self.setCentralWidget(container)

        # ------------------------------
        # Conectar botões principais
        # ------------------------------
        self.btn_abrir.clicked.connect(self.abrir_pdf)
        self.btn_salvar.clicked.connect(self.salvar_pdf)
        self.btn_extrair.clicked.connect(self.mostrar_texto_pdf)
        self.btn_excluir.clicked.connect(self.excluir_pagina_selecionada)

    # ------------------------------
    # Abrir PDF
    # ------------------------------
    def abrir_pdf(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Arquivos PDF (*.pdf)")
        if not caminho:
            return

        resul = self.conversor.processar_arquivo(caminho)
        processado = resul
        if not processado or not os.path.exists(processado):
            QMessageBox.critical(self, "Erro", "Não foi possível abrir ou converter o arquivo.")
            return

        self.caminho_pdf = processado
        doc = fitz.open(processado)
        self.ordem_paginas = list(range(len(doc)))
        doc.close()

        self.renderizar_paginas()

    # ------------------------------
    # Renderizar páginas
    # ------------------------------
    def renderizar_paginas(self):
        # Limpa layout
        for i in reversed(range(self.paginas_layout.count())):
            widget = self.paginas_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.lista_paginas.clear()

        doc = fitz.open(self.caminho_pdf)
        for index, pagina_num in enumerate(self.ordem_paginas):
            pagina = doc[pagina_num]

            # Renderiza imagem
            pix = pagina.get_pixmap(matrix=fitz.Matrix(1, 1))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            # Widget da página
            page_widget = QWidget()
            page_layout = QHBoxLayout(page_widget)

            label_pixmap = QLabel()
            label_pixmap.setPixmap(pixmap)
            page_layout.addWidget(label_pixmap)

            # Botões de mover à direita
            btn_layout = QVBoxLayout()
            if index > 0:
                btn_up = QPushButton("↑")
                btn_up.clicked.connect(lambda _, i=index: self.mover_para_cima(i))
                btn_layout.addWidget(btn_up)
            if index < len(self.ordem_paginas) - 1:
                btn_down = QPushButton("↓")
                btn_down.clicked.connect(lambda _, i=index: self.mover_para_baixo(i))
                btn_layout.addWidget(btn_down)
            page_layout.addLayout(btn_layout)

            self.paginas_layout.addWidget(page_widget)

            # Lista de páginas à esquerda
            descricao = self.descricao_paginas.get(pagina_num, f"Página {pagina_num+1}")
            item = QListWidgetItem(f"{pagina_num+1}: {descricao}")
            item.setData(1000, index)
            self.lista_paginas.addItem(item)
        doc.close()

    # ------------------------------
    # Mover páginas
    # ------------------------------
    def mover_para_cima(self, index):
        if index > 0:
            self.ordem_paginas[index], self.ordem_paginas[index-1] = \
                self.ordem_paginas[index-1], self.ordem_paginas[index]
            self.renderizar_paginas()

    def mover_para_baixo(self, index):
        if index < len(self.ordem_paginas) - 1:
            self.ordem_paginas[index], self.ordem_paginas[index+1] = \
                self.ordem_paginas[index+1], self.ordem_paginas[index]
            self.renderizar_paginas()

    # ------------------------------
    # Excluir página selecionada
    # ------------------------------
    def excluir_pagina_selecionada(self):
        item = self.lista_paginas.currentItem()
        if not item:
            return
        index = item.data(1000)
        self.ordem_paginas.pop(index)
        self.renderizar_paginas()

    # ------------------------------
    # Ir para página clicada
    # ------------------------------
    def ir_para_pagina(self, item):
        index = item.data(1000)
        if index is None:
            return
        page_widget = self.paginas_layout.itemAt(index).widget()
        if page_widget:
            self.scroll_area.ensureWidgetVisible(page_widget)

    # ------------------------------
    # Salvar PDF/Imagem
    # ------------------------------
    def salvar_pdf(self):
        if not self.caminho_pdf:
            QMessageBox.warning(self, "Aviso", "Nenhum documento carregado.")
            return

        from PyQt6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLabel, QPushButton, QFileDialog
        dialog = QDialog(self)
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

            QMessageBox.information(self, "Sucesso", f"Documento salvo em:\n{novo_caminho}")
            if formato == "PDF":
                self.caminho_pdf = novo_caminho
                self.renderizar_paginas()

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

        # Oculta visualização de páginas
        self.scroll_area.hide()

        self.centralWidget().layout().addWidget(self.editor_texto)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = PDFEditor()
    janela.show()
    sys.exit(app.exec())
