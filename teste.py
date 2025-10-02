import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QTextEdit, QDialog, QComboBox
)
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QAction
from PyQt6.QtCore import Qt
from logicaPagina import LogicaPagina
import fitz


class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PoDe Fazer café? (PDF)")
        self.setGeometry(100, 100, 1000, 700)

        # ------------------------------
        # Lógica
        # ------------------------------
        self.logica = LogicaPagina()
        self.logica.documentos_atualizados.connect(self.renderizar_paginas)

        # ------------------------------
        # Painel esquerdo
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
        self.paginas_widgets = {}  # pagina_id -> widget
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
        self.btn_desfazer.clicked.connect(self.logica.desfazer)
        self.btn_refazer.clicked.connect(self.logica.refazer)

        # ------------------------------
        # Atalhos de teclado
        # ------------------------------
        desfazer_acao = QAction(self)
        desfazer_acao.setShortcut(QKeySequence("Ctrl+Z"))
        desfazer_acao.triggered.connect(self.logica.desfazer)
        self.addAction(desfazer_acao)

        refazer_acao = QAction(self)
        refazer_acao.setShortcut(QKeySequence("Ctrl+Alt+Z"))
        refazer_acao.triggered.connect(self.logica.refazer)
        self.addAction(refazer_acao)

    # ------------------------------
    # Abrir PDF
    # ------------------------------
    def abrir_pdf(self):
        self.logica.abrir_documento(self)

    # ------------------------------
    # Renderizar páginas
    # ------------------------------
    def renderizar_paginas(self, zoom=1.0):
        for i in reversed(range(self.paginas_layout.count())):
            widget = self.paginas_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.lista_paginas.clear()
        self.paginas_widgets.clear()

        for nome_doc, dados in self.logica.documentos.items():
            header_item = QListWidgetItem(f"📄 {nome_doc}")
            header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.lista_paginas.addItem(header_item)

            for idx, pagina_id in enumerate(dados["paginas"]):
                pagina_info = self.logica.paginas[pagina_id]
                doc = self.logica.documentos[nome_doc]["doc"]
                pagina = doc.load_page(pagina_info["pagina_num"])

                try:
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(img)

                    page_widget = QWidget()
                    page_layout = QHBoxLayout(page_widget)

                    label_pixmap = QLabel()
                    label_pixmap.setPixmap(pixmap)
                    page_layout.addWidget(label_pixmap)

                    btn_layout = QVBoxLayout()
                    btn_transferir = QPushButton("⇄")
                    btn_transferir.clicked.connect(lambda _, pid=pagina_id: self.transferir_pagina(pid))
                    btn_layout.addWidget(btn_transferir)

                    if idx > 0:
                        btn_up = QPushButton("↑")
                        btn_up.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.mover_para_cima(d, i))
                        btn_layout.addWidget(btn_up)
                    if idx < len(dados["paginas"]) - 1:
                        btn_down = QPushButton("↓")
                        btn_down.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.mover_para_baixo(d, i))
                        btn_layout.addWidget(btn_down)

                    btn_del = QPushButton("X")
                    btn_del.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.excluir_pagina(d, i))
                    btn_layout.addWidget(btn_del)

                    page_layout.addLayout(btn_layout)
                    self.paginas_layout.addWidget(page_widget)
                    self.paginas_widgets[pagina_id] = page_widget

                    # Lista lateral
                    descricao = pagina_info["descricao"]
                    item_widget = QWidget()
                    item_layout = QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(0, 0, 0, 0)
                    lbl_item = QLabel(descricao)
                    item_layout.addWidget(lbl_item)
                    btn_lista_mover = QPushButton("⇄")
                    btn_lista_mover.setMaximumWidth(30)
                    btn_lista_mover.clicked.connect(lambda _, pid=pagina_id: self.transferir_pagina(pid))
                    item_layout.addWidget(btn_lista_mover)
                    item_widget.setLayout(item_layout)
                    item_list = QListWidgetItem()
                    self.lista_paginas.addItem(item_list)
                    self.lista_paginas.setItemWidget(item_list, item_widget)
                    item_list.setData(1000, pagina_id)

                except Exception as e:
                    print(f"Erro ao renderizar página {pagina_id} de {nome_doc}: {e}")

    # ------------------------------
    # Transferir página
    # ------------------------------
    def transferir_pagina(self, pagina_id):
        origem = self.logica.paginas[pagina_id]["doc_original"]
        outros_docs = [n for n in self.logica.documentos if n != origem]
        if not outros_docs:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar documento destino")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Enviar página para:"))

        combo = QComboBox()
        combo.addItems(outros_docs)
        layout.addWidget(combo)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)

        if dialog.exec():
            destino = combo.currentText()
            self.logica.mover_pagina_para_outro(pagina_id, destino)

    # ------------------------------
    # Ir para página
    # ------------------------------
    def ir_para_pagina(self, item):
        pagina_id = item.data(1000)
        if pagina_id is None:
            return
        widget = self.paginas_widgets.get(pagina_id)
        if widget:
            self.scroll_area.ensureWidgetVisible(widget)

    # ------------------------------
    # Salvar documentos
    # ------------------------------
    def salvar_pdf(self):
        for nome_doc in self.logica.documentos:
            self.logica.salvar_documento(self, nome_doc)

    # ------------------------------
    # Extrair texto
    # ------------------------------
    def mostrar_texto_pdf(self):
        if getattr(self, "editor_texto", None):
            self.editor_texto.setParent(None)
            self.editor_texto.deleteLater()
        if getattr(self, "btn_voltar", None):
            self.btn_voltar.setParent(None)
            self.btn_voltar.deleteLater()

        texto_total = ""
        for pagina_id, pagina_info in self.logica.paginas.items():
            nome_doc = pagina_info["doc_original"]
            descricao = pagina_info["descricao"]
            try:
                doc = self.logica.documentos[nome_doc]["doc"]
                pagina = doc.load_page(pagina_info["pagina_num"])
                texto = pagina.get_text("text")
            except Exception as e:
                texto = f"[Erro ao extrair texto: {e}]"
            texto_total += f"--- {nome_doc} - {descricao} ---\n{texto}\n\n"

        if not texto_total.strip():
            return

        self.editor_texto = QTextEdit()
        self.editor_texto.setPlainText(texto_total)
        self.editor_texto.setReadOnly(True)

        self.scroll_area.hide()
        self.centralWidget().layout().addWidget(self.editor_texto)

        self.btn_voltar = QPushButton("Voltar para PDF")
        self.btn_voltar.clicked.connect(self.voltar_para_pdf)
        self.centralWidget().layout().addWidget(self.btn_voltar)

    def voltar_para_pdf(self):
        if getattr(self, "editor_texto", None):
            self.editor_texto.setParent(None)
            self.editor_texto.deleteLater()
            self.editor_texto = None
        if getattr(self, "btn_voltar", None):
            self.btn_voltar.setParent(None)
            self.btn_voltar.deleteLater()
            self.btn_voltar = None
        self.scroll_area.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = PDFEditor()
    janela.show()
    sys.exit(app.exec())