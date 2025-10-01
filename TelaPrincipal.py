import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QTextEdit, QDialog, QComboBox,QSizePolicy
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
        self.btn_extrair = QPushButton("Extrair Texto")
        self.btn_desfazer = QPushButton("Desfazer (Ctrl+Z)")
        self.btn_refazer = QPushButton("Refazer (Ctrl+Alt+Z)")

        self.lista_paginas = QListWidget()
        self.lista_paginas.itemClicked.connect(self.ir_para_pagina)
        self.lista_paginas.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)

        # Layout esquerdo
        layout_esquerda = QVBoxLayout()
        layout_esquerda.addWidget(self.btn_desfazer)
        layout_esquerda.addWidget(self.btn_refazer)
        layout_esquerda.addWidget(self.btn_abrir)
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

        # Dicionário para guardar widgets das páginas
        self.paginas_widgets = {}  # **agora garantido que existe**

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
        # Limpa o layout central
        for i in reversed(range(self.paginas_layout.count())):
            widget = self.paginas_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Limpa a lista lateral
        self.lista_paginas.clear()
        self.paginas_widgets.clear()

        # Ajusta largura mínima da lista conforme o maior botão
        max_width = max(
            self.btn_desfazer.sizeHint().width(),
            self.btn_refazer.sizeHint().width(),
            self.btn_abrir.sizeHint().width(),
            self.btn_extrair.sizeHint().width()
        )
        self.lista_paginas.setMinimumWidth(max_width + 20)
        self.lista_paginas.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)

        # Renderiza cada documento
        for nome_doc, dados in self.logica.documentos.items():
            # ------------------------------
            # Cabeçalho lateral com botão salvar
            # ------------------------------
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(2, 2, 2, 2)
            header_layout.setSpacing(5)

            lbl_doc = QLabel(f"📄 {nome_doc}")
            lbl_doc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            header_layout.addWidget(lbl_doc)
            header_layout.addStretch()

            btn_salvar = QPushButton("💾 Salvar")
            btn_salvar.setMaximumWidth(100)
            btn_salvar.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50; 
                    color: white; 
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            btn_salvar.clicked.connect(lambda _, d=nome_doc: self.salvar_pdf_documento(d))
            header_layout.addWidget(btn_salvar)

            header_item = QListWidgetItem()
            header_item.setSizeHint(header_widget.sizeHint())
            self.lista_paginas.addItem(header_item)
            self.lista_paginas.setItemWidget(header_item, header_widget)
            header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            # ------------------------------
            # Renderiza cada página
            # ------------------------------
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
                    page_layout.setContentsMargins(5, 5, 5, 5)
                    page_layout.setSpacing(5)

                    label_pixmap = QLabel()
                    label_pixmap.pixmap_original = pixmap  # salva o pixmap original
                    label_pixmap.setPixmap(pixmap)
                    label_pixmap.setScaledContents(False)  # NÃO usar scaledContents
                    label_pixmap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    page_layout.addWidget(label_pixmap)


                    # ------------------------------
                    # Botões da página (pequenos)
                    # ------------------------------
                    btn_layout = QVBoxLayout()
                    btn_layout.setSpacing(3)

                    btn_transferir = QPushButton("🔄")
                    btn_transferir.setFixedSize(30, 30)
                    btn_transferir.clicked.connect(lambda _, pid=pagina_id: self.transferir_pagina(pid))
                    btn_layout.addWidget(btn_transferir)

                    if idx > 0:
                        btn_up = QPushButton("⬆️")
                        btn_up.setFixedSize(30, 30)
                        btn_up.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.mover_para_cima(d, i))
                        btn_layout.addWidget(btn_up)
                    if idx < len(dados["paginas"]) - 1:
                        btn_down = QPushButton("⬇️")
                        btn_down.setFixedSize(30, 30)
                        btn_down.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.mover_para_baixo(d, i))
                        btn_layout.addWidget(btn_down)

                    btn_del = QPushButton("❌")
                    btn_del.setFixedSize(30, 30)
                    btn_del.setStyleSheet("""
                        QPushButton {
                            background-color: #f44336; 
                            color: white; 
                            font-weight: bold; 
                            border-radius: 5px;
                        }
                        QPushButton:hover {
                            background-color: #da190b;
                        }
                    """)
                    btn_del.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.excluir_pagina(d, i))
                    btn_layout.addWidget(btn_del)

                    btn_layout.addStretch()
                    page_layout.addLayout(btn_layout)

                    self.paginas_layout.addWidget(page_widget)
                    self.paginas_widgets[pagina_id] = page_widget

                    # ------------------------------
                    # Item lateral da página
                    # ------------------------------
                    descricao = pagina_info["descricao"]
                    item_widget = QWidget()
                    item_layout = QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(2, 2, 2, 2)
                    item_layout.setSpacing(5)

                    lbl_item = QLabel(descricao)
                    lbl_item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                    item_layout.addWidget(lbl_item)

                    btn_lista_mover = QPushButton("🔄")
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


    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not hasattr(self, "paginas_widgets"):
            return

        # largura disponível na scroll_area
        largura_disponivel = min(self.scroll_area.viewport().width() - 80, 900)  # 800px máximo

        for pagina_id, widget in self.paginas_widgets.items():
            label_pixmap = widget.findChild(QLabel)
            if label_pixmap and hasattr(label_pixmap, "pixmap_original"):
                pix_original = label_pixmap.pixmap_original
                if pix_original is None:
                    continue

                # Redimensiona mantendo proporção do pixmap
                pix_redim = pix_original.scaled(
                    largura_disponivel,
                    int(largura_disponivel * pix_original.height() / pix_original.width()), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label_pixmap.setPixmap(pix_redim)




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
    def salvar_pdf_documento(self, nome_doc):
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
