import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QTextEdit
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import fitz
from logicaPagina import LogicaPagina
from conversor import ConversorArquivo


class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PoDe Fazer café? (PDF)")
        self.setGeometry(100, 100, 1000, 700)

        self.logica = LogicaPagina()
        self.conversor = ConversorArquivo()

        # ------------------------------
        # Painel ESQUERDO
        # ------------------------------
        self.btn_abrir = QPushButton("Abrir Documento")
        self.btn_salvar = QPushButton("Salvar Documento")
        self.btn_extrair = QPushButton("Extrair Texto")
        self.btn_desfazer = QPushButton("Desfazer (Ctrl+Z)")
        self.btn_refazer = QPushButton("Refazer (Ctrl+Alt+Z)")
        self.lista_paginas = QListWidget()
        self.lista_paginas.setFixedWidth(250)
        self.lista_paginas.itemClicked.connect(self.ir_para_pagina)

        layout_esquerda = QVBoxLayout()
        layout_esquerda.addWidget(self.btn_desfazer)
        layout_esquerda.addWidget(self.btn_refazer)
        layout_esquerda.addWidget(self.btn_abrir)
        layout_esquerda.addWidget(self.btn_salvar)
        layout_esquerda.addWidget(self.btn_extrair)
        layout_esquerda.addSpacing(20)
        layout_esquerda.addWidget(QLabel("Arquivos e Páginas"))
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
        self.btn_desfazer.clicked.connect(lambda: self.logica.desfazer(self))
        self.btn_refazer.clicked.connect(lambda: self.logica.refazer(self))

    # ------------------------------
    # Abrir PDF
    # ------------------------------
    def abrir_pdf(self):
        if self.logica.abrir_documento(self):
            self.renderizar_paginas()

    # ------------------------------
    # Renderizar páginas com cabeçalho
    # ------------------------------
    def renderizar_paginas(self, zoom=1.0):
        # Limpa layout anterior
        for i in reversed(range(self.paginas_layout.count())):
            widget = self.paginas_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.lista_paginas.clear()

        for nome_doc, dados in self.logica.documentos.items():
            doc = dados["doc"]
            ordem = dados["ordem_paginas"]

            # --- Cabeçalho do arquivo ---
            header_item = QListWidgetItem(f"📄 {nome_doc}")
            header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # não clicável
            self.lista_paginas.addItem(header_item)

            for index, pagina_idx in enumerate(ordem):
                pix = doc[pagina_idx].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
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
                    btn_up.clicked.connect(lambda _, n=nome_doc, i=index: self.mover_para_cima(n, i))
                    btn_layout.addWidget(btn_up)
                if index < len(ordem) - 1:
                    btn_down = QPushButton("↓")
                    btn_down.clicked.connect(lambda _, n=nome_doc, i=index: self.mover_para_baixo(n, i))
                    btn_layout.addWidget(btn_down)
                btn_del = QPushButton("X")
                btn_del.clicked.connect(lambda _, n=nome_doc, i=index: self.excluir_pagina(n, i))
                btn_layout.addWidget(btn_del)

                page_layout.addLayout(btn_layout)
                self.paginas_layout.addWidget(page_widget)

                # Lista da esquerda (com indentação)
                descricao = dados["descricao_paginas"].get(pagina_idx, f"Página {pagina_idx+1}")
                item = QListWidgetItem(f"   {pagina_idx+1}: {descricao}")  # três espaços antes
                item.setData(1000, (nome_doc, pagina_idx))
                self.lista_paginas.addItem(item)

    # ------------------------------
    # Ações lógicas
    # ------------------------------
    def mover_para_cima(self, nome_doc, index):
        self.logica.mover_para_cima(nome_doc, index)
        self.renderizar_paginas()

    def mover_para_baixo(self, nome_doc, index):
        self.logica.mover_para_baixo(nome_doc, index)
        self.renderizar_paginas()

    def excluir_pagina(self, nome_doc, index):
        self.logica.excluir_pagina(nome_doc, index)
        self.renderizar_paginas()

    # ------------------------------
    # Ir para página clicada
    # ------------------------------
    def ir_para_pagina(self, item):
        data = item.data(1000)
        if not data:
            return
        nome_doc, pagina_idx = data
        # Encontra o widget correspondente
        doc = self.logica.documentos[nome_doc]["doc"]
        ordem = self.logica.documentos[nome_doc]["ordem_paginas"]
        try:
            idx_widget = ordem.index(pagina_idx)
            page_widget = self.paginas_layout.itemAt(idx_widget).widget()
            if page_widget:
                self.scroll_area.ensureWidgetVisible(page_widget)
        except ValueError:
            pass

    # ------------------------------
    # Salvar PDF / exportar
    # ------------------------------
    def salvar_pdf(self):
        for nome_doc in self.logica.documentos:
            self.logica.salvar_documento(self, nome_doc)
        self.renderizar_paginas()

    # ------------------------------
    # Mostrar texto extraído
    # ------------------------------
    def mostrar_texto_pdf(self):
        texto_total = ""
        for nome_doc in self.logica.documentos:
            texto_total += self.logica.mostrar_texto(nome_doc) + "\n\n"

        if not texto_total.strip():
            return

        self.editor_texto = QTextEdit()
        self.editor_texto.setPlainText(texto_total)
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
