import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QTextEdit
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import fitz
from conversor import ConversorArquivo
from logicaPagina import LogicaPagina  # nossa lógica central
from geradorDocumentos import Geradora


class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Po De Faça café? (PDF)")
        self.setGeometry(100, 100, 1000, 700)

        # Lógica central do PDF
        self.logica = LogicaPagina()
        self.conversor = ConversorArquivo()

        # ------------------------------
        # Painel ESQUERDO
        # ------------------------------
        self.btn_abrir = QPushButton("Abrir Documento")
        self.btn_salvar = QPushButton("Salvar Documento")
        self.btn_extrair = QPushButton("Extrair Texto")

        self.lista_paginas = QListWidget()
        self.lista_paginas.setFixedWidth(200)
        self.lista_paginas.itemClicked.connect(self.ir_para_pagina)

        layout_esquerda = QVBoxLayout()
        layout_esquerda.addWidget(self.btn_abrir)
        layout_esquerda.addWidget(self.btn_salvar)
        layout_esquerda.addWidget(self.btn_extrair)
        layout_esquerda.addSpacing(20)
        layout_esquerda.addWidget(QLabel("Páginas"))
        layout_esquerda.addWidget(self.lista_paginas)
        layout_esquerda.addStretch()

        # ------------------------------
        # Área central com scroll
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
        # Conecta botões
        # ------------------------------
        self.btn_abrir.clicked.connect(self.abrir_pdf)
        self.btn_salvar.clicked.connect(self.salvar_pdf)
        self.btn_extrair.clicked.connect(self.mostrar_texto_pdf)

    # ------------------------------
    # Abrir PDF
    # ------------------------------
    def abrir_pdf(self):
        if self.logica.abrir_documento(self):
            self.renderizar_paginas()

    # ------------------------------
    # Renderizar páginas
    # ------------------------------
    def renderizar_paginas(self):
        # Limpa layout anterior
        for i in reversed(range(self.paginas_layout.count())):
            widget = self.paginas_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.lista_paginas.clear()

        ordem = self.logica.obter_ordem()
        pixmaps = self.logica.renderizar_paginas(zoom=1.0)

        for index, pix in enumerate(pixmaps):
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            page_widget = QWidget()
            page_layout = QHBoxLayout(page_widget)

            label_pixmap = QLabel()
            label_pixmap.setPixmap(pixmap)
            page_layout.addWidget(label_pixmap)

            # Botões de ação
            btn_layout = QVBoxLayout()
            if index > 0:
                btn_up = QPushButton("↑")
                btn_up.clicked.connect(lambda _, i=index: self.mover_para_cima(i))
                btn_layout.addWidget(btn_up)
            if index < len(ordem) - 1:
                btn_down = QPushButton("↓")
                btn_down.clicked.connect(lambda _, i=index: self.mover_para_baixo(i))
                btn_layout.addWidget(btn_down)
            btn_del = QPushButton("X")
            btn_del.clicked.connect(lambda _, i=index: self.excluir_pagina(i))
            btn_layout.addWidget(btn_del)

            page_layout.addLayout(btn_layout)
            self.paginas_layout.addWidget(page_widget)

            descricao = self.logica.obter_descricao(ordem[index])
            item = QListWidgetItem(f"{ordem[index]+1}: {descricao}")
            item.setData(1000, index)
            self.lista_paginas.addItem(item)

    # ------------------------------
    # Ações lógicas
    # ------------------------------
    def mover_para_cima(self, index):
        self.logica.mover_para_cima(index)
        self.renderizar_paginas()

    def mover_para_baixo(self, index):
        self.logica.mover_para_baixo(index)
        self.renderizar_paginas()

    def excluir_pagina(self, index):
        self.logica.excluir_pagina(index)
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
    # Salvar PDF / exportar
    # ------------------------------
    def salvar_pdf(self):
        if self.logica.salvar_documento(self):
            self.renderizar_paginas()

    # ------------------------------
    # Mostrar texto extraído
    # ------------------------------
    def mostrar_texto_pdf(self):
        texto = self.logica.mostrar_texto()
        if not texto:
            return

        self.editor_texto = QTextEdit()
        self.editor_texto.setPlainText(texto)
        self.editor_texto.setReadOnly(True)

        self.scroll_area.hide()
        self.centralWidget().layout().addWidget(self.editor_texto)

        btn_voltar = QPushButton("Voltar para PDF")
        btn_voltar.clicked.connect(self.voltar_para_pdf)
        self.centralWidget().layout().addWidget(btn_voltar)

    def voltar_para_pdf(self):
        if hasattr(self, "editor_texto"):
            self.editor_texto.deleteLater()
        for i in reversed(range(self.centralWidget().layout().count())):
            widget = self.centralWidget().layout().itemAt(i).widget()
            if isinstance(widget, QPushButton) and widget.text() == "Voltar para PDF":
                widget.deleteLater()
        self.scroll_area.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = PDFEditor()
    janela.show()
    sys.exit(app.exec())
