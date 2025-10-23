from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidgetItem, QSizePolicy, QDialog, QComboBox, QMessageBox,
    QScrollArea, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, QSize

import fitz  # PyMuPDF
import os
import globais as G

def abreviar_titulo(nome, limite=22):
    if len(nome) > limite:
        return nome[:limite - 3] + "..."
    return nome



from PyQt6.QtCore import QObject, Qt, QEvent

class ArrastarScrollFilter(QObject):
    def __init__(self, scroll_area):
        super().__init__()
        self.scroll_area = scroll_area
        self._arrastando = False
        self._pos_inicial = None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._arrastando = True
                self._pos_inicial = event.pos()
                return True

        elif event.type() == QEvent.Type.MouseMove:
            if self._arrastando and self._pos_inicial:
                delta = event.pos() - self._pos_inicial
                self.scroll_area.verticalScrollBar().setValue(
                    self.scroll_area.verticalScrollBar().value() - delta.y()
                )
                self.scroll_area.horizontalScrollBar().setValue(
                    self.scroll_area.horizontalScrollBar().value() - delta.x()
                )
                self._pos_inicial = event.pos()
                return True

        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                self._arrastando = False
                self._pos_inicial = None
                return True

        return False

class RenderizadorPaginas:
    def __init__(self, layout_central, lista_lateral, logica, scroll_area):
        self.bloquear_render = False

        super().__init__()

        # ---------------- Atributos principais ----------------
        self.layout_central = layout_central          # QVBoxLayout onde ficam as páginas
        self.lista_lateral = lista_lateral            # QListWidget da lateral
        self.logica = logica                          # Lógica de manipulação de documentos
        self.scroll_area = scroll_area

        # Zoom padrão
        self.zoom_por_doc = {}
        self.zoom_por_pagina = {}
        self.pixmaps_originais = {}
        self.paginas_widgets = {}
        self.zoom_factor = getattr(G, "ZOOM_PADRAO", 1.0)

        # Callback para atualizar lista lateral (pode ser definido externamente)
        self.atualizar_lista_callback = None

        # Conecta clique na lista lateral
        self.lista_lateral.itemClicked.connect(self.ir_para_pagina)

        # Sinal da lógica para atualizar quando documentos mudarem
        if hasattr(self.logica, "documentos_atualizados"):
            self.logica.documentos_atualizados.connect(self.renderizar_com_zoom_padrao)


            
    # ------------------------------
    # NOVO MÉTODO (Obrigatório para o sistema de sinais e Undo/Redo)
    # ------------------------------
    def renderizar_com_zoom_padrao(self):
        """Atualiza todas as páginas com o zoom atual sem recriar widgets."""
        if getattr(self, "bloquear_render", False):
            return  # evita loop de sinais

        for pid, widget in self.paginas_widgets.items():
            pixmap_original = self.pixmaps_originais.get(pid)
            if not pixmap_original:
                continue

            doc_origem = G.PAGINAS[pid]["doc_original"]
            zoom = self.zoom_por_doc.get(doc_origem, G.ZOOM_PADRAO)

            nova_largura = int(pixmap_original.width() * zoom)
            nova_altura = int(pixmap_original.height() * zoom)
            pixmap_redimensionado = pixmap_original.scaled(
                nova_largura, nova_altura,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            label = widget.findChild(QLabel, "page_image_label")
            if label:
                label.setPixmap(pixmap_redimensionado)






    def renderizar_todas(self, zoom=None):
        if zoom is None:
            zoom = self.zoom_factor

        self.limpar_layout()
        self.ajustar_largura_lista()
        self.criar_barra_zoom() 
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

        nome,_ = os.path.splitext(nome_doc)
        lbl_doc = QLabel(f"📑{abreviar_titulo(nome, limite=22)}")
        lbl_doc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(lbl_doc)
        header_layout.addStretch()

        # Botão Salvar
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
        btn_salvar.clicked.connect(lambda _, d=nome_doc: self.logica.salvar_documento_dialog(self.lista_lateral.window(), d))
        header_layout.addWidget(btn_salvar)

        # Botão Apagar
        btn_apagar = QPushButton("🗑️ Apagar")
        btn_apagar.setMaximumWidth(100)
        btn_apagar.setStyleSheet("""
            QPushButton {
                background-color: #f44336; 
                color: white; 
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        btn_apagar.clicked.connect(lambda _, d=nome_doc: self.logica.excluir_documento(self.lista_lateral.window(), d))
        header_layout.addWidget(btn_apagar)

        # Adiciona à lista lateral
        header_item = QListWidgetItem()
        header_item.setSizeHint(header_widget.sizeHint())
        self.lista_lateral.addItem(header_item)
        self.lista_lateral.setItemWidget(header_item, header_widget)
        header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        # Guarda informação de que é cabeçalho de documento
        header_item.setData(1000, {"tipo":"doc", "nome_doc": nome_doc})


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
            page_widget.setStyleSheet("background-color: #222; border-radius: 6px;")  # estilo visual
            page_layout = QHBoxLayout(page_widget)
            page_layout.setContentsMargins(10, 10, 10, 10)
            page_layout.setSpacing(0)

            # Label da imagem
            label_pixmap = QLabel()
            label_pixmap.setObjectName("page_image_label")
            label_pixmap.setPixmap(pixmap)
            label_pixmap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_pixmap.setScaledContents(False)
            label_pixmap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # Contêiner que vai alinhar imagem e botões
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(label_pixmap)

            # Botões fixos no lado direito da página
            btn_container = QWidget()
            btn_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
            btn_layout = QVBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(5)
            btn_layout.addStretch()

            btn_transferir = QPushButton("🔄")
            btn_transferir.setFixedSize(30, 30)
            btn_transferir.clicked.connect(lambda _, pid=pagina_id: self.transferir_pagina(pid))
            btn_layout.addWidget(btn_transferir, alignment=Qt.AlignmentFlag.AlignHCenter)

            if idx > 0:
                btn_up = QPushButton("⬆️")
                btn_up.setFixedSize(30, 30)
                btn_up.clicked.connect(lambda _, d=nome_doc, i=idx: self._mover_e_atualizar(d, i, "cima"))
                btn_layout.addWidget(btn_up, alignment=Qt.AlignmentFlag.AlignHCenter)
            if idx < len(G.DOCUMENTOS[nome_doc]["paginas"]) - 1:
                btn_down = QPushButton("⬇️")
                btn_down.setFixedSize(30, 30)
                btn_down.clicked.connect(lambda _, d=nome_doc, i=idx: self._mover_e_atualizar(d, i, "baixo"))
                btn_layout.addWidget(btn_down, alignment=Qt.AlignmentFlag.AlignHCenter)

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
            btn_del.clicked.connect(lambda _, d=nome_doc, i=idx: self._excluir_e_atualizar(d, i))
            btn_layout.addWidget(btn_del, alignment=Qt.AlignmentFlag.AlignHCenter)
            btn_layout.addStretch()

            # Os botões ficam sempre "grudados" à direita da imagem
            container_layout.addWidget(btn_container, alignment=Qt.AlignmentFlag.AlignVCenter)
            page_layout.addWidget(container)

            # Permitir zoom com scroll do mouse
            label_pixmap.wheelEvent = lambda event, pid=pagina_id: self._zoom_documento(pid, event.angleDelta().y(), event)



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
            self.logica.moverPagina(pagina_id, destino)
            self.renderizar_com_zoom_padrao()
            self.lista_lateral.window().atualizar_tamanho_paginas()
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

    # ---------------------------------------------------------------
    # 🔄 ANIMAÇÃO DE TROCA DE PÁGINA
    # ---------------------------------------------------------------
    def _animar_troca_pagina(self, nome_doc, idx, direcao, callback):
        """Anima a troca de posição entre páginas antes de atualizar a lógica."""
        paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        novo_idx = idx + direcao

        if not (0 <= novo_idx < len(paginas)):
            return  # fora dos limites

        pid_atual = paginas[idx]
        pid_destino = paginas[novo_idx]

        w_atual = self.paginas_widgets[pid_atual]
        w_destino = self.paginas_widgets[pid_destino]

        # Movimento vertical entre as posições
        deslocamento = w_destino.geometry().top() - w_atual.geometry().top()

        anim = QPropertyAnimation(w_atual, b"pos")
        anim.setDuration(500)
        anim.setStartValue(w_atual.pos())
        anim.setEndValue(w_atual.pos() + QPoint(0, deslocamento))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Efeito de leve "fade" na página destino
        fade_dest = QGraphicsOpacityEffect(w_destino)
        w_destino.setGraphicsEffect(fade_dest)

        fade = QPropertyAnimation(fade_dest, b"opacity")
        fade.setDuration(400)
        fade.setStartValue(1)
        fade.setEndValue(0.4)
        fade.setEasingCurve(QEasingCurve.Type.InOutQuad)

        fade_back = QPropertyAnimation(fade_dest, b"opacity")
        fade_back.setDuration(400)
        fade_back.setStartValue(0.4)
        fade_back.setEndValue(1)
        fade_back.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Quando a animação terminar → executa o callback lógico
        def finalizar():
            w_destino.setGraphicsEffect(None)
            callback()  # executa a lógica real (mover e atualizar)

        anim.finished.connect(lambda: fade_back.start())
        fade_back.finished.connect(finalizar)

        fade.start()
        anim.start()

        # Guarda referências pra evitar garbage collection
        self.anim_troca = [anim, fade, fade_back]

    # ---------------------------------------------------------------
    # ❌ ANIMAÇÃO DE REMOÇÃO DE PÁGINA
    # ---------------------------------------------------------------
    def _animar_remocao_pagina(self, nome_doc, idx, callback):
        """Anima a remoção da página e depois executa a lógica."""
        paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        if not (0 <= idx < len(paginas)):
            return

        pid = paginas[idx]
        w = self.paginas_widgets[pid]

        efeito = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(efeito)

        # Fade out
        fade = QPropertyAnimation(efeito, b"opacity")
        fade.setDuration(600)
        fade.setStartValue(1)
        fade.setEndValue(0)
        fade.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Shrink
        shrink = QPropertyAnimation(w, b"geometry")
        shrink.setDuration(600)
        geom = w.geometry()
        final_geom = QRect(
            geom.center().x() - geom.width() // 4,
            geom.center().y() - geom.height() // 4,
            geom.width() // 2,
            geom.height() // 2
        )
        shrink.setStartValue(geom)
        shrink.setEndValue(final_geom)
        shrink.setEasingCurve(QEasingCurve.Type.InBack)

        # Quando terminar → executa callback
        shrink.finished.connect(callback)

        fade.start()
        shrink.start()

        self.anim_remocao = [fade, shrink]

    # ---------------------------------------------------------------
    # 🔧 INTEGRAÇÃO COM SUAS FUNÇÕES EXISTENTES
    # ---------------------------------------------------------------

    def _mover_e_atualizar(self, nome_doc, idx, direcao):
        """Executa a animação e depois a lógica de troca."""
        self._animar_troca_pagina(
            nome_doc, idx,
            -1 if direcao == "cima" else +1,
            lambda: self._finalizar_mover_e_atualizar(nome_doc, idx, direcao)
        )

    def _finalizar_mover_e_atualizar(self, nome_doc, idx, direcao):
        """Executado após a animação de troca terminar."""
        if direcao == "cima":
            self.logica.mover_para_cima(nome_doc, idx)
        else:
            self.logica.mover_para_baixo(nome_doc, idx)

        self.renderizar_com_zoom_padrao()

        self.lista_lateral.window().atualizar_tamanho_paginas()

    # ---------------------------------------------------------------
    def _excluir_e_atualizar(self, nome_doc, idx):
        """Executa a animação de exclusão e só depois a lógica."""
        self._animar_remocao_pagina(
            nome_doc, idx,
            lambda: self._finalizar_excluir_e_atualizar(nome_doc, idx)
        )

    def _finalizar_excluir_e_atualizar(self, nome_doc, idx):
        """Executado após a animação de exclusão terminar."""
        self.logica.excluir_pagina(nome_doc, idx)
        self.renderizar_com_zoom_padrao()
        self.lista_lateral.window().atualizar_tamanho_paginas()





      # ---------------- Barra de zoom ----------------
    def criar_barra_zoom(self):
        

        self.btn_zoom_out = QPushButton("➖")
        self.btn_zoom_in = QPushButton("➕")
        self.btn_zoom_reset = QPushButton("100%")
        for b in (self.btn_zoom_out, self.btn_zoom_in, self.btn_zoom_reset):
            b.setFixedSize(50, 28)
            b.setStyleSheet("""
                QPushButton {
                    font-size: 13px;
                    border: 1px solid #777;
                    border-radius: 5px;
                    background-color: #f5f5f5;
                }
                QPushButton:hover { background-color: #ddd; }
            """)
            
        # conecta aos métodos (verifique nomes)
        self.btn_zoom_out.clicked.connect(lambda: self.ajustar_zoom(-0.1))
        self.btn_zoom_in.clicked.connect(lambda: self.ajustar_zoom(0.1))
        self.btn_zoom_reset.clicked.connect(lambda: self.definir_zoom(1.0))

        # ADIÇÃO CORRETA: insere o widget de zoom no layout central onde as páginas serão adicionadas
        # (limpar_layout() limpa self.layout_central antes, por isso recriamos a barra a cada renderização)


    def _zoom_documento(self, pagina_id, delta_y, event=None):
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt

        if event:
            modifiers = QApplication.keyboardModifiers()
            if not (modifiers & Qt.KeyboardModifier.ControlModifier):
                # Propaga o scroll normalmente
                event.ignore()
                return

        # Determina qual documento está sendo zoomado
        nome_doc = G.PAGINAS[pagina_id]["doc_original"]
        zoom_atual = self.zoom_por_doc.get(nome_doc, 1.0)
        fator_zoom = 1.1 if delta_y > 0 else 0.9
        novo_zoom = max(0.3, min(3.0, zoom_atual * fator_zoom))
        self.zoom_por_doc[nome_doc] = novo_zoom

        # Atualiza todas as páginas deste documento
        for pid, widget in self.paginas_widgets.items():
            if G.PAGINAS[pid]["doc_original"] != nome_doc:
                continue
            pixmap_original = self.pixmaps_originais[pid]
            nova_largura = int(pixmap_original.width() * novo_zoom)
            nova_altura = int(pixmap_original.height() * novo_zoom)
            pixmap_redimensionado = pixmap_original.scaled(
                nova_largura, nova_altura,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label = widget.findChild(QLabel, "page_image_label")
            if label:
                label.setPixmap(pixmap_redimensionado)


    def ajustar_zoom(self, delta):
        if self.bloquear_render:
            return
        self.bloquear_render = True  # trava atualização via sinal

        documentos_visiveis = set(G.PAGINAS[pid]["doc_original"]
                                for pid, w in self.paginas_widgets.items() if w.isVisible())
        for doc in documentos_visiveis:
            novo_zoom = max(0.3, min(3.0, self.zoom_por_doc.get(doc, 1.0) + delta))
            self.zoom_por_doc[doc] = novo_zoom

        # Re-renderiza localmente as páginas visíveis
        for pid, widget in self.paginas_widgets.items():
            if G.PAGINAS[pid]["doc_original"] in documentos_visiveis:
                pixmap_original = self.pixmaps_originais[pid]
                novo_zoom = self.zoom_por_doc[G.PAGINAS[pid]["doc_original"]]
                nova_largura = int(pixmap_original.width() * novo_zoom)
                nova_altura = int(pixmap_original.height() * novo_zoom)
                pixmap_redimensionado = pixmap_original.scaled(
                    nova_largura, nova_altura,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label = widget.findChild(QLabel, "page_image_label")
                if label:
                    label.setPixmap(pixmap_redimensionado)

        self.bloquear_render = False  # destrava após o zoom


    def definir_zoom(self, valor):
        # Aplica a todas as páginas visíveis
        documentos_visiveis = set(G.PAGINAS[pid]["doc_original"] 
                                for pid, w in self.paginas_widgets.items() if w.isVisible())
        for doc in documentos_visiveis:
            self.zoom_por_doc[doc] = valor

        # Atualiza a interface
        self.ajustar_zoom(0)





