# ...existing code...
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QDialog, QComboBox, QMessageBox, QScrollArea, QFrame, QGraphicsOpacityEffect,
    QTreeWidget, QTreeWidgetItem, QInputDialog, QApplication
)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QDrag, QMouseEvent
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, QSize, QByteArray,
    QMimeData, QObject, QEvent
)
import fitz  # PyMuPDF
import os
import globais as G
from signals import signals as AppSignals
from PyQt6 import sip


def abreviar_titulo(nome, limite=22):
    if len(nome) > limite:
        return nome[:limite - 3] + "..."
    return nome

class ArrastarScrollFilter(QObject):
    def __init__(self, scroll_area):
        super().__init__()
        self.scroll = scroll_area
        self.arrastando = False
        self.ultimo_ponto = None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.RightButton:
            self.arrastando = True
            self.ultimo_ponto = event.pos()
            return True
        elif event.type() == QEvent.Type.MouseMove and self.arrastando:
            delta = event.pos() - self.ultimo_ponto
            self.scroll.horizontalScrollBar().setValue(self.scroll.horizontalScrollBar().value() - delta.x())
            self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().value() - delta.y())
            self.ultimo_ponto = event.pos()
            return True
        elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.RightButton:
            self.arrastando = False
            return True
        return False

class DraggableLabel(QLabel):
    def __init__(self, pagina_id, parent=None):
        super().__init__(parent)
        self.pagina_id = pagina_id

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not hasattr(self, "_drag_start_pos"):
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(str(self.pagina_id))
        drag.setMimeData(mime)
        if isinstance(self.pixmap(), QPixmap):
            drag.setPixmap(self.pixmap().scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        drag.exec(Qt.DropAction.MoveAction)

class RenderizadorPaginas:
    def __init__(self, layout_central, lista_lateral, logica, scroll_area):
        self.bloquear_render = False
        ICONS_PATH = getattr(G, "ICONS_PATH", "icons")
        super().__init__()

        # principais
        self.layout_central = layout_central
        self.lista_lateral = lista_lateral
        self.logica = logica
        self.scroll_area = scroll_area

        self.separadores = []  # lista para todos os separadores


        self.doc_selecionado = None  # nome do documento atualmente selecionado
        self.pagina_foco = None      # id da página atualmente selecionada



        self.zoom_por_doc = {}
        self.pixmaps_originais = {}
        self.paginas_widgets = {}
        self.zoom_factor = getattr(G, "ZOOM_PADRAO", 1.0)
        self.atualizar_lista_callback = None

        # conectar seleção na árvore
        self.lista_lateral.itemClicked.connect(self.ir_para_pagina)

        # conecta sinal da própria lógica (se houver) e o sinal global
        if hasattr(self.logica, "documentos_atualizados"):
            try:
                self.logica.documentos_atualizados.connect(self.renderizar_com_zoom_padrao)
            except Exception:
                pass
        try:
            AppSignals.documentos_atualizados.connect(self.renderizar_com_zoom_padrao)
        except Exception:
            pass

        parent_w = self.layout_central.parentWidget()
        if parent_w is not None:
            parent_w.setAcceptDrops(True)
            parent_w.dragEnterEvent = self._drag_enter_event
            parent_w.dropEvent = self._drop_event

    def renderizar_com_zoom_padrao(self):
        """
        Atualiza toda a interface com o zoom atual,
        recriando widgets e a lista lateral, respeitando a ordem em G.DOCUMENTOS.
        Também garante que o último documento/página selecionada continue visível
        e atualiza os separadores.
        """
        if getattr(self, "bloquear_render", False):
            return

        # captura estados de expansão atuais da árvore lateral para restaurar depois
        expanded_states = {}
        try:
            for i in range(self.lista_lateral.topLevelItemCount()):
                item = self.lista_lateral.topLevelItem(i)
                if item is not None:
                    expanded_states[item.text(0)] = item.isExpanded()
        except Exception:
            expanded_states = {}

        # limpa layout e widgets antigos
        self.limpar_layout()

        for nome_doc, dados in G.DOCUMENTOS.items():
            self._adicionar_cabecalho_doc(nome_doc)
            for idx, pagina_id in enumerate(dados["paginas"]):
                zoom = self.zoom_por_doc.get(nome_doc, getattr(G, "ZOOM_PADRAO", 1.0))
                self._adicionar_pagina(nome_doc, idx, pagina_id, zoom)

        # --------- Lógica para restaurar último documento/página ---------
        doc = getattr(self, "doc_selecionado", None)
        pagina = getattr(self, "pagina_foco", None)

        if doc:
            # aplica visibilidade apenas ao documento selecionado
            for pid, widget in self.paginas_widgets.items():
                widget.setVisible(G.PAGINAS[pid]["doc_original"] == doc)

            # determina página de foco
            pagina_focus = None
            if pagina and G.PAGINAS.get(pagina, {}).get("doc_original") == doc:
                pagina_focus = pagina
            else:
                # pega a primeira página visível do documento
                for pid, widget in self.paginas_widgets.items():
                    if widget.isVisible():
                        pagina_focus = pid
                        break

            if pagina_focus:
                self.pagina_foco = pagina_focus
                widget = self.paginas_widgets.get(pagina_focus)
                if widget:
                    self.scroll_area.ensureWidgetVisible(widget)

        # --------- Atualiza separadores ---------
        self._atualizar_separadores()

        # Atualiza tamanho das páginas na janela principal (se existir)
        win = self.lista_lateral.window()
        if hasattr(win, "atualizar_tamanho_paginas"):
            try:
                win.atualizar_tamanho_paginas()
            except Exception:
                pass

        # grava os estados de expansão no objeto janela (TelaPrincipal) para que ela restaure
        try:
            if win is not None and isinstance(expanded_states, dict):
                setattr(win, "_expanded_states", expanded_states)
        except Exception:
            pass

        # garante que quem quiser escute essa mudança
        try:
            AppSignals.layout_update_requested.emit()
        except Exception:
            pass


    def _drag_enter_event(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def _drop_event(self, event):
        pagina_id = event.mimeData().text()
        # coleta widgets válidos
        widgets = []
        for i in range(self.layout_central.count()):
            it = self.layout_central.itemAt(i)
            if not it:
                continue
            w = it.widget()
            if w is None:
                continue
            widgets.append(w)
        pos_y = event.position().y()
        destino_idx = len(widgets)
        for idx, w in enumerate(widgets):
            if pos_y < w.y() + w.height() // 2:
                destino_idx = idx
                break
        self._reordenar_pagina(pagina_id, destino_idx)
        event.acceptProposedAction()

    def _reordenar_pagina(self, pagina_id, destino_idx):
        if pagina_id not in self.paginas_widgets:
            return
        w = self.paginas_widgets[pagina_id]
        self.layout_central.removeWidget(w)
        self.layout_central.insertWidget(destino_idx, w)
        doc = G.PAGINAS[pagina_id]["doc_original"]
        if pagina_id in G.DOCUMENTOS[doc]["paginas"]:
            G.DOCUMENTOS[doc]["paginas"].remove(pagina_id)
        G.DOCUMENTOS[doc]["paginas"].insert(destino_idx, pagina_id)
        self.renderizar_com_zoom_padrao()

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

    # no topo do arquivo (já existente)


    # substitua sua função limpar_layout pela versão abaixo
    def limpar_layout(self):
        """
        Limpa todo o layout central removendo widgets e layouts recursivamente.
        Também desconecta sinais de QPushButton para evitar referências pendentes.
        """
        layout = self.layout_central

        # esvazia o layout principal
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue

            w = item.widget()
            if w:
                self._limpar_widget(w)
            else:
                sub = item.layout()
                if sub:
                    self._limpar_sub_layout(sub)

        # limpa estruturas internas
        try:
            self.lista_lateral.clear()
        except Exception:
            pass

        self.paginas_widgets.clear()
        self.pixmaps_originais.clear()

        # garante atualização da UI
        try:
            QApplication.processEvents()
            if hasattr(self, "scroll_area") and self.scroll_area:
                self.scroll_area.viewport().update()
        except Exception:
            pass


    def _limpar_widget(self, w):
        """Desconecta sinais e deleta um widget e seus filhos."""
        try:
            # desconecta clicked de botões (evita lambdas mantendo referências)
            for btn in w.findChildren(QPushButton):
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass

            # desconecta sinais custom (tenta generico)
            for obj in w.findChildren(QObject):
                try:
                    # se tiver atributo 'disconnect', tenta desconectar (silencioso)
                    sigs = getattr(obj, "signals", None)
                except Exception:
                    pass
        except Exception:
            pass

        # remove do pai e agenda para deleção
        try:
            w.setParent(None)
        except Exception:
            pass
        try:
            w.deleteLater()
        except Exception:
            pass


    def _limpar_sub_layout(self, layout):
        """Limpa recursivamente um layout e depois o deleta com sip."""
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w:
                self._limpar_widget(w)
            else:
                sub = item.layout()
                if sub:
                    self._limpar_sub_layout(sub)

        # tenta deletar o próprio layout (sip.delete) para liberar C++ side
        try:
            sip.delete(layout)
        except Exception:
            # fallback: nada, layout será coletado depois
            pass



    def ajustar_largura_lista(self):
        max_width = 100
        self.lista_lateral.setMinimumWidth(max_width + 20)
        self.lista_lateral.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
    def adicionar_botao_linha(self, pagina_widget, icone_path):
        """
        Adiciona um botão estilo linha abaixo de uma página.
        - pagina_widget: QWidget da página
        - icone_path: caminho do ícone centralizado
        """
        # Cria o botão que será a "linha"
        botao = QPushButton()
        botao.setFixedHeight(20)  # altura da linha
        botao.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # estica horizontalmente
        botao.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;  /* cor da linha */
                border: none;
            }
            QPushButton:hover {
                background-color: #005EA6;
            }
        """)

        # Coloca o ícone no centro do botão usando QLabel
        if icone_path:
            icone_label = QLabel(botao)
            icone_label.setPixmap(QIcon(icone_path).pixmap(QSize(16, 16)))
            icone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icone_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # não bloqueia clique
            icone_label.setGeometry(botao.rect())  # ocupa todo o botão
            icone_label.setScaledContents(True)

        # Adiciona o botão ao layout vertical da página
        layout = pagina_widget.layout()
        if isinstance(layout, QVBoxLayout) or isinstance(layout, QHBoxLayout):
            layout.addWidget(botao)


            
    def _adicionar_cabecalho_doc(self, nome_doc):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(2, 2, 2, 2)
        header_layout.setSpacing(5)

        icone = QLabel()
        pixmap = QPixmap(f"{getattr(G, 'ICONS_PATH', 'icons')}/file.svg").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icone.setPixmap(pixmap)
        header_layout.addWidget(icone)

        nome, _ = os.path.splitext(nome_doc)
        lbl_doc = QLabel(f"{abreviar_titulo(nome, limite=22)}")
        lbl_doc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(lbl_doc)

        btn_salvar = QPushButton()
        btn_salvar.setIcon(QIcon(f"{getattr(G, 'ICONS_PATH', 'icons')}/save-all.svg"))
        btn_salvar.setMaximumWidth(100)
        btn_salvar.clicked.connect(lambda _, d=nome_doc: self.logica.salvar_documento_dialog(self.lista_lateral.window(), d))
        header_layout.addWidget(btn_salvar)

        btn_apagar = QPushButton()
        btn_apagar.setIcon(QIcon(f"{getattr(G, 'ICONS_PATH', 'icons')}/file-x.svg"))
        btn_apagar.setMaximumWidth(100)
        btn_apagar.clicked.connect(lambda _, d=nome_doc: self.logica.excluir_documento(self.lista_lateral.window(), d))
        header_layout.addWidget(btn_apagar)

        # adiciona item de topo na árvore
        doc_item = QTreeWidgetItem([nome_doc])
        doc_item.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "doc", "nome_doc": nome_doc})
        self.lista_lateral.addTopLevelItem(doc_item)
        self.lista_lateral.setItemWidget(doc_item, 0, header_widget)

    def _adicionar_pagina(self, nome_doc, idx, pagina_id, zoom):
        pagina_info = G.PAGINAS[pagina_id]
        nome_doc_origem = pagina_info["doc_original"]
        doc_real = G.DOCUMENTOS[nome_doc_origem]["doc"]
        pagina_num_origem = pagina_info["fitz_index"]
        pagina = doc_real.load_page(pagina_num_origem)
        try:
            # Renderiza página
            pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.pixmaps_originais[pagina_id] = pixmap

            # Widget da página (VLayout principal)
            page_widget = QWidget()
            page_widget.setStyleSheet("background-color: #222; border-radius: 6px;")
            page_layout = QVBoxLayout(page_widget)
            page_layout.setContentsMargins(10, 10, 10, 10)
            page_layout.setSpacing(5)

            # Container horizontal da página e botões laterais
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)

            # Label da página
            label_pixmap = DraggableLabel(pagina_id)
            label_pixmap.setObjectName("page_image_label")
            label_pixmap.setPixmap(pixmap)
            label_pixmap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_pixmap.setScaledContents(False)
            label_pixmap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            container_layout.addWidget(label_pixmap)

            # Container lateral de botões
            btn_container = QWidget()
            btn_layout = QVBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(5)
            btn_layout.addStretch()

            # Botões (Transferir, cima, baixo, excluir)
            btn_transferir = QPushButton()
            btn_transferir.setIcon(QIcon(f"{getattr(G, 'ICONS_PATH', 'icons')}/git-compare-arrows.svg"))
            btn_transferir.setFixedSize(30, 30)
            btn_transferir.clicked.connect(lambda _, pid=pagina_id: self.transferir_pagina(pid))
            btn_layout.addWidget(btn_transferir, alignment=Qt.AlignmentFlag.AlignHCenter)

            if idx > 0:
                btn_up = QPushButton()
                btn_up.setIcon(QIcon(f"{getattr(G, 'ICONS_PATH', 'icons')}/move-up.svg"))
                btn_up.setFixedSize(30, 30)
                btn_up.clicked.connect(lambda _, d=nome_doc, i=idx: self._mover_e_atualizar(d, i, "cima"))
                btn_layout.addWidget(btn_up, alignment=Qt.AlignmentFlag.AlignHCenter)

            if idx < len(G.DOCUMENTOS[nome_doc]["paginas"]) - 1:
                btn_down = QPushButton()
                btn_down.setIcon(QIcon(f"{getattr(G, 'ICONS_PATH', 'icons')}/move-down.svg"))
                btn_down.setFixedSize(30, 30)
                btn_down.clicked.connect(lambda _, d=nome_doc, i=idx: self._mover_e_atualizar(d, i, "baixo"))
                btn_layout.addWidget(btn_down, alignment=Qt.AlignmentFlag.AlignHCenter)

            btn_del = QPushButton()
            btn_del.setIcon(QIcon(f"{getattr(G, 'ICONS_PATH', 'icons')}/delete.svg"))
            btn_del.setFixedSize(30, 30)
            btn_del.clicked.connect(lambda _, d=nome_doc, i=idx: self._excluir_e_atualizar(d, i))
            btn_layout.addWidget(btn_del, alignment=Qt.AlignmentFlag.AlignHCenter)

            btn_layout.addStretch()
            container_layout.addWidget(btn_container, alignment=Qt.AlignmentFlag.AlignTop)
            page_layout.addWidget(container)

            # Zoom da página com scroll
            label_pixmap.wheelEvent = lambda event, pid=pagina_id: self._zoom_documento(pid, event.angleDelta().y(), event)



            # --- depois de adicionar o widget da página ao layout e registrar em self.paginas_widgets ---
            self.layout_central.addWidget(page_widget)
            self.paginas_widgets[pagina_id] = page_widget


        

            # --- CRIA APENAS SEPARADORES VÁLIDOS (fora do page_widget) ---
            lista_paginas = G.DOCUMENTOS[nome_doc]["paginas"]

            # Só cria separador se existe realmente uma página abaixo no mesmo documento
            if len(lista_paginas) > 1 and idx < len(lista_paginas) - 1:
                page_above = pagina_id
                page_below = lista_paginas[idx + 1]

                # cria separador já com IDs
                separador = self.criar_separador("icons/table-rows-split.svg", page_above, page_below)

                # conecta clique
                separador.clicked.connect(lambda _, a=page_above, b=page_below: self.separador_clicado(a, b))

                # adiciona ao layout
                self.layout_central.addWidget(separador)

                # guarda na lista de separadores
                self.separadores.append(separador)

                # atualiza visibilidade imediatamente
                self._atualizar_separadores()



            # Adiciona à árvore lateral
            doc_item = self._buscar_item_documento(nome_doc)
            if doc_item:
                self._adicionar_item_lateral(pagina_id, pagina_info.get("descricao", ""), doc_item)

        except Exception as e:
            print(f"Erro ao renderizar página {pagina_id}: {e}")




    # ...existing code...
    def criar_separador(self, icone_path=None, page_above=None, page_below=None):
        separador = QPushButton()
        separador.setFixedHeight(20)
        separador.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        separador.setStyleSheet("background-color: red;")
        separador.setCursor(Qt.CursorShape.SplitVCursor)
        separador.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # IDs das páginas que ele separa
        separador.page_above = page_above
        separador.page_below = page_below

        # adiciona ícone se fornecido
        if icone_path:
            separador.setIcon(QIcon(icone_path))
            separador.setIconSize(QSize(16, 16))
            separador.setStyleSheet(separador.styleSheet() + "QPushButton { text-align: center; }")

        return separador

# ...existing code...

    def _atualizar_separadores(self):
        """
        Atualiza todos os separadores da lista de forma segura,
        ignorando objetos que já foram deletados.
        """
        # cria uma nova lista removendo separadores deletados
        self.separadores = [sep for sep in self.separadores if not sip.isdeleted(sep)]

        for sep in self.separadores:
            a = self.paginas_widgets.get(getattr(sep, "page_above", None))
            b = self.paginas_widgets.get(getattr(sep, "page_below", None))

            if not a or not b:
                sep.hide()
            else:
                sep.setVisible(a.isVisible() and b.isVisible())




    def separador_clicado(self, page_above, page_below):
        # DEBUG no terminal
        print("Clique no separador!")
        print("Acima:", page_above)
        print("Abaixo:", page_below)

        # Chama a lógica que corta (você já implementou cortar_documento)
        try:
            self.logica.cortar_documento(page_above, page_below)
        except Exception as e:
            print("Erro ao chamar cortar_documento:", e)




    def _buscar_item_documento(self, nome_doc):
        for i in range(self.lista_lateral.topLevelItemCount()):
            item = self.lista_lateral.topLevelItem(i)
            dados = item.data(0, Qt.ItemDataRole.UserRole)
            if dados and dados.get("nome_doc") == nome_doc:
                return item
        return None


    def _adicionar_item_lateral(self, pagina_id, descricao, doc_item: QTreeWidgetItem):
        pagina_item = QTreeWidgetItem(doc_item)
        pagina_item.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "pagina", "pagina_id": pagina_id})

        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(2, 2, 2, 2)
        item_layout.setSpacing(5)

        lbl_item = QLabel(descricao)
        lbl_item.setWordWrap(True)
        lbl_item.setStyleSheet("color: white;")
        item_layout.addWidget(lbl_item)

        btn_transferir = QPushButton()
        btn_transferir.setIcon(QIcon(f"{getattr(G, 'ICONS_PATH', 'icons')}/git-compare-arrows.svg"))
        btn_transferir.setMaximumWidth(30)
        

        
        
        def abrir_dialog_transferencia():
            dialog = QDialog(self.lista_lateral.window())
            dialog.setWindowTitle("Escolha o documento destino")
            layout = QVBoxLayout(dialog)
            combo = QComboBox()
            doc_atual = G.PAGINAS[pagina_id]["doc_original"]
            destinos = [nome for nome in G.DOCUMENTOS.keys() if nome != doc_atual]
            combo.addItems(destinos)
            layout.addWidget(combo)
            btn_ok = QPushButton("Mover")
            layout.addWidget(btn_ok)
            def mover():
                destino = combo.currentText()
                if destino:
                    self.logica.moverPagina(pagina_id, destino)
                    dialog.accept()
            btn_ok.clicked.connect(mover)
            dialog.exec()

        btn_transferir.clicked.connect(abrir_dialog_transferencia)
        item_layout.addWidget(btn_transferir)
        item_widget.setLayout(item_layout)
        self.lista_lateral.setItemWidget(pagina_item, 0, item_widget)
        return pagina_item

    def atualizar_item_lateral(self, pagina_id, nova_descricao=None):
        for i in range(self.lista_lateral.topLevelItemCount()):
            doc_item = self.lista_lateral.topLevelItem(i)
            for j in range(doc_item.childCount()):
                pagina_item = doc_item.child(j)
                data = pagina_item.data(0, Qt.ItemDataRole.UserRole)
                if data and data.get("tipo") == "pagina" and data.get("pagina_id") == pagina_id:
                    if nova_descricao:
                        widget = self.lista_lateral.itemWidget(pagina_item, 0)
                        if widget:
                            lbls = widget.findChildren(QLabel)
                            if lbls:
                                lbls[0].setText(nova_descricao)
                    return

    def mover_item_lateral(self, pagina_id, destino_idx):
        for i in range(self.lista_lateral.topLevelItemCount()):
            doc_item = self.lista_lateral.topLevelItem(i)
            for j in range(doc_item.childCount()):
                pagina_item = doc_item.child(j)
                data = pagina_item.data(0, Qt.ItemDataRole.UserRole)
                if data and data.get("tipo") == "pagina" and data.get("pagina_id") == pagina_id:
                    doc_item.takeChild(j)
                    doc_item.insertChild(destino_idx, pagina_item)
                    return

    def transferir_pagina(self, pagina_id):
        origem = G.PAGINAS[pagina_id]["doc_original"]
        outros_docs = [n for n in G.DOCUMENTOS.keys() if n != origem]
        if not outros_docs:
            QMessageBox.information(None, "Transferir Página", "Nenhum outro documento aberto para transferir.")
            return
        dialog = QDialog(self.lista_lateral.window())
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
            win = self.lista_lateral.window()
            if hasattr(win, "atualizar_tamanho_paginas"):
                win.atualizar_tamanho_paginas()

    def ir_para_pagina(self, item, column=0):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        tipo = data.get("tipo")

        if tipo == "pagina":
            pagina_id = data["pagina_id"]
            nome_doc = G.PAGINAS[pagina_id]["doc_original"]
            self._mostrar_paginas_por_documento(nome_doc, pagina_focus=pagina_id)
            self._atualizar_separadores()
        elif tipo == "doc":
            nome_doc = data["nome_doc"]
            self._mostrar_paginas_por_documento(nome_doc)
            self._atualizar_separadores()


    def mostrar_pagina_unica(self, pagina_id):
        self.pagina_foco = pagina_id
        for pid, widget in self.paginas_widgets.items():
            widget.setVisible(pid == pagina_id)

        widget = self.paginas_widgets.get(pagina_id)
        if widget:
            self.scroll_area.ensureWidgetVisible(widget)

        self._atualizar_separadores()



    def mostrar_paginas_documento(self, nome_doc):
        self._mostrar_paginas_por_documento(nome_doc)
        self._atualizar_separadores()


    def _mostrar_paginas_por_documento(self, nome_doc, pagina_focus=None):
        # guarda o documento selecionado
        self.doc_selecionado = nome_doc

        # Mostrar apenas páginas do documento
        for pid, widget in self.paginas_widgets.items():
            widget.setVisible(G.PAGINAS[pid]["doc_original"] == nome_doc)

        # Escolher página para focar
        if pagina_focus is None:
            # tenta usar a última página focada se pertence ao documento
            if self.pagina_foco and G.PAGINAS[self.pagina_foco]["doc_original"] == nome_doc:
                pagina_focus = self.pagina_foco
            else:
                # senão pega a primeira página visível do documento
                for pid, widget in self.paginas_widgets.items():
                    if widget.isVisible():
                        pagina_focus = pid
                        break

        if pagina_focus:
            self.pagina_foco = pagina_focus  # guarda a página atual
            widget = self.paginas_widgets.get(pagina_focus)
            if widget:
                self.scroll_area.ensureWidgetVisible(widget)



    def _animar_troca_pagina(self, nome_doc, idx, direcao, callback):
        paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        novo_idx = idx + direcao
        if not (0 <= novo_idx < len(paginas)):
            return
        pid_atual = paginas[idx]
        pid_destino = paginas[novo_idx]
        w_atual = self.paginas_widgets[pid_atual]
        w_destino = self.paginas_widgets[pid_destino]
        deslocamento = w_destino.geometry().top() - w_atual.geometry().top()
        anim = QPropertyAnimation(w_atual, b"pos")
        anim.setDuration(500)
        anim.setStartValue(w_atual.pos())
        anim.setEndValue(w_atual.pos() + QPoint(0, deslocamento))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
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
        def finalizar():
            w_destino.setGraphicsEffect(None)
            callback()
        anim.finished.connect(lambda: fade_back.start())
        fade_back.finished.connect(finalizar)
        fade.start()
        anim.start()
        self.anim_troca = [anim, fade, fade_back]

    def _animar_remocao_pagina(self, nome_doc, idx, callback):
        paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        if not (0 <= idx < len(paginas)):
            return
        pid = paginas[idx]
        w = self.paginas_widgets.get(pid)
        if w is None:
            callback()
            return
        efeito = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(efeito)
        fade = QPropertyAnimation(efeito, b"opacity")
        fade.setDuration(600)
        fade.setStartValue(1)
        fade.setEndValue(0)
        fade.setEasingCurve(QEasingCurve.Type.InOutCubic)
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
        shrink.finished.connect(callback)
        fade.start()
        shrink.start()
        self.anim_remocao = [fade, shrink]

    def _mover_e_atualizar(self, nome_doc, idx, direcao):
        self._animar_troca_pagina(
            nome_doc, idx,
            -1 if direcao == "cima" else +1,
            lambda: self._finalizar_mover_e_atualizar(nome_doc, idx, direcao)
        )

    def _finalizar_mover_e_atualizar(self, nome_doc, idx, direcao):
        if direcao == "cima":
            self.logica.mover_para_cima(nome_doc, idx)
            novo_idx = idx - 1
        else:
            self.logica.mover_para_baixo(nome_doc, idx)
            novo_idx = idx + 1

        # Re-renderiza apenas a parte lateral (sem refazer tudo)
        self._atualizar_lista_documento(nome_doc)
        
    def _atualizar_lista_documento(self, nome_doc):
        """Recria os itens da lista lateral de um documento após alterações."""
        # Procura o item de documento
        doc_item = self._buscar_item_documento(nome_doc)
        if not doc_item:
            return

        # Remove todos os filhos antigos (páginas)
        while doc_item.childCount():
            doc_item.removeChild(doc_item.child(0))

        # Recria as páginas na nova ordem
        for pagina_id in G.DOCUMENTOS[nome_doc]["paginas"]:
            descricao = G.PAGINAS[pagina_id].get("descricao", "")
            self._adicionar_item_lateral(pagina_id, descricao, doc_item)


    def _excluir_e_atualizar(self, nome_doc, idx):
        self._animar_remocao_pagina(
            nome_doc, idx,
            lambda: self._finalizar_excluir_e_atualizar(nome_doc, idx)
        )

    def _finalizar_excluir_e_atualizar(self, nome_doc, idx):
        self.logica.excluir_pagina(nome_doc, idx)
        self.renderizar_com_zoom_padrao()
        win = self.lista_lateral.window()
        if hasattr(win, "atualizar_tamanho_paginas"):
            win.atualizar_tamanho_paginas()
        if hasattr(self.logica, "documentos_atualizados"):
            self.logica.documentos_atualizados.emit()

    def criar_barra_zoom(self):
        self.btn_zoom_out = QPushButton("➖")
        self.btn_zoom_in = QPushButton("➕")
        self.btn_zoom_reset = QPushButton("100%")
        for b in (self.btn_zoom_out, self.btn_zoom_in, self.btn_zoom_reset):
            b.setFixedSize(50, 28)
            b.setStyleSheet("""
                QPushButton { font-size: 13px; border: 1px solid #777; border-radius: 5px; background-color: #f5f5f5; }
                QPushButton:hover { background-color: #ddd; }
            """)
        self.btn_zoom_out.clicked.connect(lambda: self.ajustar_zoom(-0.1))
        self.btn_zoom_in.clicked.connect(lambda: self.ajustar_zoom(0.1))
        self.btn_zoom_reset.clicked.connect(lambda: self.definir_zoom(1.0))

    def _zoom_documento(self, pagina_id, delta_y, event=None):
        if event:
            modifiers = QApplication.keyboardModifiers()
            if not (modifiers & Qt.KeyboardModifier.ControlModifier):
                event.ignore()
                return
        nome_doc = G.PAGINAS[pagina_id]["doc_original"]
        zoom_atual = self.zoom_por_doc.get(nome_doc, 1.0)
        fator_zoom = 1.1 if delta_y > 0 else 0.9
        novo_zoom = max(0.3, min(3.0, zoom_atual * fator_zoom))
        self.zoom_por_doc[nome_doc] = novo_zoom
        for pid, widget in self.paginas_widgets.items():
            if G.PAGINAS[pid]["doc_original"] != nome_doc:
                continue
            pixmap_original = self.pixmaps_originais.get(pid)
            if pixmap_original is None:
                continue
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
        self.bloquear_render = True
        documentos_visiveis = set(
            G.PAGINAS[pid]["doc_original"]
            for pid, w in self.paginas_widgets.items() if w.isVisible()
        )
        for doc in documentos_visiveis:
            novo_zoom = max(0.3, min(3.0, self.zoom_por_doc.get(doc, 1.0) + delta))
            self.zoom_por_doc[doc] = novo_zoom
        for pid, widget in self.paginas_widgets.items():
            if G.PAGINAS[pid]["doc_original"] in documentos_visiveis:
                pixmap_original = self.pixmaps_originais.get(pid)
                if pixmap_original is None:
                    continue
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
        self.bloquear_render = False

    def definir_zoom(self, valor):
        documentos_visiveis = set(
            G.PAGINAS[pid]["doc_original"]
            for pid, w in self.paginas_widgets.items() if w.isVisible()
        )
        for doc in documentos_visiveis:
            self.zoom_por_doc[doc] = valor
        self.ajustar_zoom(0)