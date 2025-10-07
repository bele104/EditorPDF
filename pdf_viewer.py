from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidgetItem, QSizePolicy, QDialog, QComboBox, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import fitz
import globais as G
import os
def abreviar_titulo(nome, limite=20):
    if len(nome) > limite:
        return nome[:limite - 3] + "..."
    return nome

class RenderizadorPaginas:




    def __init__(self,layout_central, lista_lateral,logica, scroll_area):
        self.logica = logica
        self.layout_central = layout_central
        self.lista_lateral = lista_lateral
        self.paginas_widgets = {}        # pagina_id -> widget
        self.pixmaps_originais = {}      # pagina_id -> QPixmap original
        self.lista_lateral.itemClicked.connect(self.ir_para_pagina)
        self.scroll_area = scroll_area  # <- referência à scroll area
        self.logica.documentos_atualizados.connect(self.renderizar_com_zoom_padrao) #fica any mesmo 
    # ------------------------------
    # NOVO MÉTODO (Obrigatório para o sistema de sinais e Undo/Redo)
    # ------------------------------
    def renderizar_com_zoom_padrao(self):
        """Método chamado pelo sinal da lógica e pelas ações de desfazer/refazer para redesenhar a UI."""
        print("oi")
        self.renderizar_todas(G.ZOOM_PADRAO)


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
    # Na classe RenderizadorPaginas

    def limpar_layout(self):
        # 1. Limpa layout central (onde as páginas são exibidas)
        while self.layout_central.count():
            item = self.layout_central.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
                
        # 2. Limpa lista lateral
        self.lista_lateral.clear()
        
        # 3. Limpa caches internos (essencial!)
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
        nome,_=os.path.splitext(nome_doc)
        lbl_doc = QLabel(f"📑{abreviar_titulo(nome,limite=20)}")
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
        # **Guarda informação de que é cabeçalho de documento**
        header_item.setData(1000, {"tipo":"doc", "nome_doc": nome_doc})
        header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

    def _adicionar_pagina(self, nome_doc, idx, pagina_id, zoom):
        pagina_info = G.PAGINAS[pagina_id]
        # ----------------------------------------------------
        # 💥 PRINTS DE DEBUG DA ORDEM E DA ORIGEM
        # ----------------------------------------------------
        if idx == 0:
            print("\n--- INÍCIO DO DOCUMENTO ---")
            print(f"DEBUG: Documento sendo processado (Destino/Lista de Ordem): {nome_doc}")
            print(f"DEBUG: Lista de ordem atual: {G.DOCUMENTOS[nome_doc]['paginas']}")
        
        # 1. Qual é o documento REAL que contém o conteúdo desta página?
        nome_doc_origem = pagina_info["doc_original"]
        
        # 2. Pega o objeto fitz.Document REAL usando o nome da origem.
        doc_real = G.DOCUMENTOS[nome_doc_origem]["doc"]
        
        # 3. Carrega a página usando o objeto doc_real e o índice original.
        pagina_num_origem = pagina_info["fitz_index"]
        pagina = doc_real.load_page(pagina_num_origem)
        
        print(f"--> Carregando '{pagina_id}' (Lista Pág. {idx}): Conteúdo está em '{nome_doc_origem}' na Pág. {pagina_num_origem}")
    
    # ----------------------------------------------------
        
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
             # 💥 CORREÇÃO AQUI: Dê um nome específico para o QLabel que contém a imagem.
            label_pixmap.setObjectName("page_image_label") 
            label_pixmap.setPixmap(pixmap)       # <-- Define a imagem
            label_pixmap.setScaledContents(False)
            label_pixmap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            page_layout.addWidget(label_pixmap)

            # Botões da página
            btn_layout = QVBoxLayout()
            btn_layout.setSpacing(3)

            btn_transferir = QPushButton("🔄")
            btn_transferir.setFixedSize(30,30)
            btn_transferir.clicked.connect(lambda _, pid=pagina_id: self.transferir_pagina(pid))
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
        # 💥 CORREÇÃO: Conecta ao novo método 'transferir_pagina'
        btn_lista_mover.clicked.connect(lambda _, pid=pagina_id: self.transferir_pagina(pid)) 
        item_layout.addWidget(btn_lista_mover)
        

        item_widget.setLayout(item_layout)

        item_list = QListWidgetItem()
        self.lista_lateral.addItem(item_list)
        self.lista_lateral.setItemWidget(item_list, item_widget)
         # **Guarda informação de que é página**
        item_list.setData(1000, {"tipo":"pagina", "pagina_id": pagina_id})

        # No arquivo pdf_viewer.py, dentro da classe RenderizadorPaginas

    

    def transferir_pagina(self, pagina_id):
        """
        Abre um diálogo para o usuário selecionar o documento de destino
        e chama a lógica para mover a página.
        """
        # 💥 CORREÇÃO: Acessa os dados globais G.PAGINAS e G.DOCUMENTOS
        origem = G.PAGINAS[pagina_id]["doc_original"]
        outros_docs = [n for n in G.DOCUMENTOS.keys() if n != origem]
        
        if not outros_docs:
            QMessageBox.information(None, "Transferir Página", "Nenhum outro documento aberto para transferir.")
            return

        # O DIÁLOGO (QDialog)
        # ⚠️ Certifique-se de que a classe RenderizadorPaginas herda de QWidget 
        # ou QObject e tem uma referência à janela principal (self),
        # ou use 'None' para o parent do QDialog.
        dialog = QDialog(self.lista_lateral.window()) # Use a janela principal como parent
        dialog.setWindowTitle("Selecionar documento destino")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Enviar página para:"))

        combo = QComboBox()
        combo.addItems(outros_docs)
        layout.addWidget(combo)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            destino = combo.currentText()
            # 💥 CHAMADA FINAL: Agora a lógica recebe os dois argumentos
            self.logica.moverPagina(pagina_id, destino)
    def ir_para_pagina(self, item):
        data = item.data(1000)
        if data is None:
            return

        if data["tipo"] == "pagina":
            # Scroll direto e mostra apenas o documento desta página
            pagina_id = data["pagina_id"]
            doc_origem = G.PAGINAS[pagina_id]["doc_original"]

            # Oculta todas as páginas que não pertencem ao mesmo documento
            for pid, widget in self.paginas_widgets.items():
                widget.setVisible(G.PAGINAS[pid]["doc_original"] == doc_origem)

            # Scroll até a página
            widget = self.paginas_widgets.get(pagina_id)
            if widget:
                self.scroll_area.ensureWidgetVisible(widget)

        elif data["tipo"] == "doc":
            # Scroll direto para a primeira página do documento e mostra apenas este documento
            nome_doc = data["nome_doc"]

            # Mostra somente páginas deste documento
            for pid, widget in self.paginas_widgets.items():
                widget.setVisible(G.PAGINAS[pid]["doc_original"] == nome_doc)

            # Scroll para a primeira página visível
            for pid, widget in self.paginas_widgets.items():
                if widget.isVisible():
                    self.scroll_area.ensureWidgetVisible(widget)
                    break

    def mostrar_pagina_unica(self, pagina_id):
        """
        Oculta todas as páginas e mostra apenas a página especificada.
        """
        for pid, widget in self.paginas_widgets.items():
            widget.setVisible(pid == pagina_id)
        
        # Scroll para a página
        widget = self.paginas_widgets.get(pagina_id)
        if widget:
            self.scroll_area.ensureWidgetVisible(widget)
    def mostrar_paginas_documento(self, nome_doc):
        """
        Mostra apenas as páginas do documento 'nome_doc' e oculta as demais.
        """
        for pagina_id, widget in self.paginas_widgets.items():
            doc_origem = G.PAGINAS[pagina_id]["doc_original"]
            widget.setVisible(doc_origem == nome_doc)
        
        # Scroll para a primeira página do documento
        for pagina_id, widget in self.paginas_widgets.items():
            if widget.isVisible():
                self.scroll_area.ensureWidgetVisible(widget)
                break
