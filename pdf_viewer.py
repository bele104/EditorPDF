"""from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidgetItem, QScrollArea, QSizePolicy, QComboBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
import fitz


class PDFViewer:
    def __init__(self, lista_paginas, logica):
        self.lista_paginas = lista_paginas
        self.logica = logica

        # Área central com scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.paginas_widget = QWidget()
        self.paginas_layout = QVBoxLayout()
        self.paginas_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.paginas_widget.setLayout(self.paginas_layout)
        self.scroll_area.setWidget(self.paginas_widget)

        # Dicionário para guardar widgets das páginas
        self.paginas_widgets = {}

    def renderizar_paginas(self, zoom=1.0):
        # Limpa layout central e lista lateral
        for i in reversed(range(self.paginas_layout.count())):
            widget = self.paginas_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.lista_paginas.clear()
        self.paginas_widgets.clear()

        # Renderiza cada documento
        for nome_doc, dados in self.logica.documentos.items():
            # ------------------------------
            # Cabeçalho lateral do documento
            # ------------------------------
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(2, 2, 2, 2)
            header_layout.setSpacing(5)

            lbl_doc = QLabel(f"📄 {nome_doc}")
            lbl_doc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            header_layout.addWidget(lbl_doc)
            header_layout.addStretch()

            header_item = QListWidgetItem()
            header_item.setSizeHint(header_widget.sizeHint())
            self.lista_paginas.addItem(header_item)
            self.lista_paginas.setItemWidget(header_item, header_widget)
            header_item.setData(Qt.ItemDataRole.UserRole, nome_doc)

            # Clique no documento mostra só ele
            def make_mostrar_doc(nome):
                return lambda _: self.mostrar_documento(nome)
            header_widget.mousePressEvent = make_mostrar_doc(nome_doc)

            # ------------------------------
            # Renderiza cada página
            # ------------------------------
            for idx, pagina_id in enumerate(dados["paginas"]):
                pagina_info = self.logica.paginas[pagina_id]
                doc = self.logica.documentos[nome_doc]["doc"]
                pagina = doc.load_page(pagina_info["pagina_num"])

                pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)

                page_widget = QWidget()
                page_layout = QHBoxLayout(page_widget)
                page_layout.setContentsMargins(5, 5, 5, 5)
                page_layout.setSpacing(5)

                # ------------------------------
                # Imagem da página
                # ------------------------------
                label_pixmap = QLabel()
                label_pixmap.pixmap_original = pixmap
                label_pixmap.setPixmap(pixmap)
                label_pixmap.setScaledContents(False)
                label_pixmap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                page_layout.addWidget(label_pixmap)

                # ------------------------------
                # Botões à direita
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
                btn_del.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.excluir_pagina(d, i))
                btn_layout.addWidget(btn_del)

                btn_layout.addStretch()
                page_layout.addLayout(btn_layout)

                self.paginas_layout.addWidget(page_widget)
                self.paginas_widgets[pagina_id] = page_widget

                # ------------------------------
                # Item lateral da página
                # ------------------------------
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(2, 2, 2, 2)
                item_layout.setSpacing(5)

                lbl_item = QLabel(pagina_info["descricao"])
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
                item_list.setData(Qt.ItemDataRole.UserRole, pagina_id)

    def mostrar_documento(self, nome_doc):
        for pagina_id, widget in self.paginas_widgets.items():
            doc_origem = self.logica.paginas[pagina_id]["doc_original"]
            widget.setVisible(doc_origem == nome_doc)

    def ajustar_tamanho_paginas(self):
        largura_disponivel = min(self.scroll_area.viewport().width() - 80, 900)
        for pagina_id, widget in self.paginas_widgets.items():
            label_pixmap = widget.findChild(QLabel)
            if label_pixmap and hasattr(label_pixmap, "pixmap_original"):
                pix_original = label_pixmap.pixmap_original
                pix_redim = pix_original.scaled(
                    largura_disponivel,
                    int(largura_disponivel * pix_original.height() / pix_original.width()),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label_pixmap.setPixmap(pix_redim)

    def transferir_pagina(self, pagina_id):
        origem = self.logica.paginas[pagina_id]["doc_original"]
        outros_docs = [n for n in self.logica.documentos if n != origem]
        if not outros_docs:
            return

        dialog = QDialog()
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
            self.renderizar_paginas()
"""