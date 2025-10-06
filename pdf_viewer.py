from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidgetItem, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import fitz
import globais as G

from logicaPagina import LogicaPagina as logica

class RenderizadorPaginas:




    def __init__(self,layout_central, lista_lateral):
        self.logica = logica()
        self.layout_central = layout_central
        self.lista_lateral = lista_lateral
        self.paginas_widgets = {}        # pagina_id -> widget
        self.pixmaps_originais = {}      # pagina_id -> QPixmap original

    def renderizar_todas(self, zoom=1.0):
        self.limpar_layout()
        self.ajustar_largura_lista()
        for nome_doc, dados in G.DOCUMENTOS.items():
            self._adicionar_cabecalho_doc(nome_doc)
            for idx, pagina_id in enumerate(dados["paginas"]):
                self._adicionar_pagina(nome_doc, idx, pagina_id, zoom)

    # ------------------------------
    # Funções internas
    # ------------------------------
    def limpar_layout(self):
        # Limpa layout central
        for i in reversed(range(self.layout_central.count())):
            widget = self.layout_central.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # Limpa lista lateral
        self.lista_lateral.clear()
        self.paginas_widgets.clear()
        self.pixmaps_originais.clear()

    def ajustar_largura_lista(self):
        # Ajusta largura mínima da lista conforme o maior botão
        max_width = 100  # pode parametrizar se quiser
        self.lista_lateral.setMinimumWidth(max_width + 20)
        self.lista_lateral.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)

    def _adicionar_cabecalho_doc(self, nome_doc):
        from PyQt6.QtWidgets import QHBoxLayout, QWidget
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(2,2,2,2)
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
        btn_salvar.clicked.connect(lambda _, d=nome_doc: self.logica.salvar_documento(d))
        header_layout.addWidget(btn_salvar)

        header_item = QListWidgetItem()
        header_item.setSizeHint(header_widget.sizeHint())
        self.lista_lateral.addItem(header_item)
        self.lista_lateral.setItemWidget(header_item, header_widget)
        header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

    def _adicionar_pagina(self, nome_doc, idx, pagina_id, zoom):
        pagina_info = G.PAGINAS[pagina_id]
        print(f"DEBUG: nome_doc = {nome_doc}")
        print(f"DEBUG: Chaves em G.DOCUMENTOS = {G.DOCUMENTOS.keys()}")
        doc = G.DOCUMENTOS[nome_doc]["doc"]  
        print(pagina_info["pagina_num"]) # <- aqui você pega o objeto fitz.Document
        pagina = doc.load_page(pagina_info["pagina_num"])
        
        try:
            pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            # Widget da página
            page_widget = QWidget()
            page_layout = QHBoxLayout(page_widget)
            page_layout.setContentsMargins(5,5,5,5)
            page_layout.setSpacing(5)

            label_pixmap = QLabel()
            label_pixmap.pixmap_original = pixmap
            label_pixmap.setPixmap(pixmap)
            label_pixmap.setScaledContents(False)
            label_pixmap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            page_layout.addWidget(label_pixmap)

            # Botões da página
            btn_layout = QVBoxLayout()
            btn_layout.setSpacing(3)

            btn_transferir = QPushButton("🔄")
            btn_transferir.setFixedSize(30,30)
            btn_transferir.clicked.connect(lambda _, pid=pagina_id: self.logica.mover_pagina_para_outro(pid))
            btn_layout.addWidget(btn_transferir)

            if idx > 0:
                btn_up = QPushButton("⬆️")
                btn_up.setFixedSize(30,30)
                btn_up.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.mover_para_cima(d, i))
                btn_layout.addWidget(btn_up)
            if idx < len(G.DOCUMENTOS[nome_doc]["paginas"])-1:
                btn_down = QPushButton("⬇️")
                btn_down.setFixedSize(30,30)
                btn_down.clicked.connect(lambda _, d=nome_doc, i=idx: self.logica.mover_para_baixo(d, i))
                btn_layout.addWidget(btn_down)

            btn_del = QPushButton("❌")
            btn_del.setFixedSize(30,30)
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

            # Adiciona widget ao layout central
            self.layout_central.addWidget(page_widget)
            self.paginas_widgets[pagina_id] = page_widget
            self.pixmaps_originais[pagina_id] = pixmap

            # Item lateral
            self._adicionar_item_lateral(pagina_id, pagina_info["descricao"])

        except Exception as e:
            print(f"Erro ao renderizar página {pagina_id}: {e}")

    def _adicionar_item_lateral(self, pagina_id, descricao):
        from PyQt6.QtWidgets import QHBoxLayout, QWidget, QComboBox
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(2,2,2,2)
        item_layout.setSpacing(5)

        lbl_item = QLabel(descricao)
        lbl_item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_item.setWordWrap(True)
        item_layout.addWidget(lbl_item)

        btn_lista_mover = QPushButton("🔄")
        btn_lista_mover.setMaximumWidth(30)
        btn_lista_mover.clicked.connect(lambda _, pid=pagina_id: self.logica.mover_pagina_para_outro(pid,descricao))
        item_layout.addWidget(btn_lista_mover)

        item_widget.setLayout(item_layout)

        item_list = QListWidgetItem()
        self.lista_lateral.addItem(item_list)
        self.lista_lateral.setItemWidget(item_list, item_widget)
        item_list.setData(1000, pagina_id)
