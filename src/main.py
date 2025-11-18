# ...existing code...
import sys, os
sys.path.append(os.path.dirname(__file__))
import ctypes

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QTextEdit, QDialog, QComboBox, QSizePolicy, QFrame, 
    QMessageBox, QFileDialog, QSplitter, QTreeWidget, QTreeWidgetItem, QInputDialog
)
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QAction, QIcon
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from logicaPagina import LogicaPagina as logica
import fitz

from pdf_viewer import RenderizadorPaginas
import globais as G
from pdf_viewer import ArrastarScrollFilter as arrastar
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer

import warnings

# conecta sinais globais (importa o singleton 'signals' do módulo signals.py)
from signals import signals as AppSignals

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
import os

class PainelMesclar(QWidget):
    fechar_sinal = pyqtSignal()
    mesclagem_concluida = pyqtSignal(str) 
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: #222;
            border-radius: 12px;
        """)

        self.logica = logica()
        
        self.arquivos = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Cabeçalho
        cab = QHBoxLayout()
        lbl = QLabel("Mesclar Documentos")
        lbl.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        cab.addWidget(lbl)
        cab.addStretch()

        btnX = QPushButton("✖")
        btnX.setFixedSize(24, 24)
        btnX.setStyleSheet("color: white; background: transparent;")
        btnX.clicked.connect(self.fechar_sinal)
        cab.addWidget(btnX)
        layout.addLayout(cab)

        # Lista de arquivos
        self.lista = QListWidget()
        self.lista.setSpacing(10)
        self.lista.setStyleSheet("""
            QListWidget { background-color: #333; border: none; padding: 4px; }
            QListWidget::item:selected { background-color: #0078d7; }
        """)
        self.lista.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        layout.addWidget(self.lista)

        # Área inferior com botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)

        self.btn_adicionar = QPushButton("Adicionar documentos…")
        self.btn_adicionar.setStyleSheet("padding: 6px; background-color: #0078d7; color: white;")
        self.btn_adicionar.clicked.connect(self.selecionar_arquivos)
        botoes_layout.addWidget(self.btn_adicionar)

        self.btn_mesclar = QPushButton("Mesclar documentos")
        self.btn_mesclar.setStyleSheet("padding: 6px; background-color: #28a745; color: white;")
        self.btn_mesclar.clicked.connect(self.mesclar_documentos)
        botoes_layout.addWidget(self.btn_mesclar)

        layout.addLayout(botoes_layout)

        QTimer.singleShot(50, self.selecionar_arquivos)

    # Seleção de arquivos
    def selecionar_arquivos(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar documentos para mesclar",
            "",
            "PDF Files (*.pdf)"
        )
        if not arquivos:
            return

        for caminho in arquivos:
            if caminho not in self.arquivos:
                self.arquivos.append(caminho)
                self._adicionar_item(caminho)

    # Adiciona item visual
    def _adicionar_item(self, caminho):
        nome = os.path.basename(caminho)
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, caminho)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        label = QLabel(nome)
        label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(label)
        layout.addStretch()

        btn_remover = QPushButton("✖")
        btn_remover.setFixedSize(20, 20)
        btn_remover.setStyleSheet("color: white; background: transparent;")
        btn_remover.clicked.connect(lambda _, it=item: self._remover_item(it))
        layout.addWidget(btn_remover)

        widget.setMinimumHeight(50)
        widget.setStyleSheet("background-color: #444; border-radius: 8px;")

        item.setSizeHint(widget.sizeHint())
        self.lista.addItem(item)
        self.lista.setItemWidget(item, widget)
        widget.show()

    def _remover_item(self, item):
        caminho = item.data(Qt.ItemDataRole.UserRole)
        if caminho in self.arquivos:
            self.arquivos.remove(caminho)
        self.lista.takeItem(self.lista.row(item))

    def obter_ordem(self):
        arquivos = []
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            arquivos.append(item.data(Qt.ItemDataRole.UserRole))
        return arquivos

    # Mesclar documentos
    def mesclar_documentos(self):
        ordem = self.obter_ordem()
        if len(ordem) < 2:
            QMessageBox.warning(self, "Erro", "Selecione pelo menos 2 documentos.")
            return

        # Chama a lógica que mescla PDFs
        pdf_final = self.logica.mesclar_documentos_selecionados(ordem)
        if not pdf_final or not os.path.exists(pdf_final):
            QMessageBox.critical(self, "Erro", "Falha ao gerar o PDF mesclado.")
            return


        # Abre PDF com fitz para obter páginas
        doc = fitz.open(pdf_final)
        nome_doc = "Mesclado.pdf"
        nome_doc_abreviado = "Mesclado"

        # Cria estrutura igual ao abrir_documento()
        G.DOCUMENTOS[nome_doc] = {"doc": doc, "paginas": [], "path": pdf_final}

        for i in range(len(doc)):
            pid = f"{nome_doc}_p{i+1}"
            G.PAGINAS[pid] = {
                "descricao": f"|--{nome_doc_abreviado}-pag-{i+1}",
                "doc_original": nome_doc,
                "fitz_index": i,
            }
            G.DOCUMENTOS[nome_doc]["paginas"].append(pid)

        print(f"[AÇÃO] Documento mesclado registrado no G.DOCUMENTOS como '{nome_doc}'")

        # Salva estado e emite atualização de layout
        G.Historico.salvar_estado()
        # Aqui, quem tiver o RenderizadorPaginas deve atualizar a interface:
        # ex: tela_principal.gerar.renderizar_com_zoom_padrao()

        QMessageBox.information(self, "Sucesso", f"Documento mesclado criado: Mesclado")
        self.mesclagem_concluida.emit(pdf_final)
        self.fechar_sinal.emit()
        AppSignals.documentos_atualizados.emit()



class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()        # ...existing code...
        # Caminho base dos ícones
        ICONS_PATH = G.ICONS_PATH if hasattr(G, "ICONS_PATH") else "icons"
        # icone da janela (fallback protegido)
        try:
            self.setWindowIcon(QIcon(f"{ICONS_PATH}/logo.ico"))
        except Exception:
            pass

        # Carrega tema com proteção
        try:
            print(ICONS_PATH)
            
            with open(G.TEMA_PATH, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        except Exception:
            # fallback: sem stylesheet
            print("⚠️ Aviso: falha ao carregar tema escuro, usando padrão do sistema.")
            pass

        self.setWindowTitle("Serena LOVE PDF")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(True)  # Permite arrastar arquivos para a janela inteira

        # ------------------------------
        # Lógica do editor
        # ------------------------------
        self.logica = logica()

        # ------------------------------
        # Estado padrão / auxílio
        # ------------------------------
        self.zoom_factor = getattr(G, "ZOOM_PADRAO", 1.0)
        # Vars para painel recolhível (inicializa com valores sensatos)
        self.tamanho_padrao = 200
        self.painel_widget = None
        self.icone_painel = None

        # ------------------------------
        # Botões de cabeçalho fixo acima do PDF
        # ------------------------------
        self.cabecalho_widget = QWidget()
        cabecalho_layout = QVBoxLayout(self.cabecalho_widget)
        cabecalho_layout.setContentsMargins(5, 5, 5, 5)
        cabecalho_layout.setSpacing(5)

        # Linha 1: Desfazer e Refazer (esquerda)
        linha_atalhos = QHBoxLayout()
        # --- Botão Desfazer ---
        self.btn_desfazer_top = QPushButton()  # sem texto aqui
        self.btn_desfazer_top.setIcon(QIcon(f"{ICONS_PATH}/undo-dot.svg"))
        self.btn_desfazer_top.setIconSize(QSize(24, 24))
        self.btn_desfazer_top.setFixedSize(40, 36)
        self.btn_desfazer_top.clicked.connect(self.desfazer_acao)

        # --- Botão Refazer ---
        self.btn_refazer_top = QPushButton()
        self.btn_refazer_top.setIcon(QIcon(f"{ICONS_PATH}/redo-2.svg"))
        self.btn_refazer_top.setIconSize(QSize(24, 24))
        self.btn_refazer_top.setFixedSize(40, 36)
        self.btn_refazer_top.clicked.connect(self.refazer_acao)

        linha_atalhos.addWidget(self.btn_desfazer_top)
        linha_atalhos.addWidget(self.btn_refazer_top)
        linha_atalhos.addStretch()  # empurra para a esquerda
        cabecalho_layout.addLayout(linha_atalhos)

        # Linha de Zoom
        linha_zoom = QHBoxLayout()
        linha_zoom.addStretch()

        # Botões de zoom
        self.btn_zoom_menos = QPushButton()
        self.btn_zoom_menos.setIcon(QIcon(f"{ICONS_PATH}/zoom-out.svg"))
        self.btn_zoom_mais = QPushButton()
        self.btn_zoom_mais.setIcon(QIcon(f"{ICONS_PATH}/zoom-in.svg"))
        self.btn_zoom_reset = QPushButton()
        self.btn_zoom_reset.setIcon(QIcon(f"{ICONS_PATH}/expand.svg"))

        for btn in [self.btn_zoom_menos, self.btn_zoom_mais, self.btn_zoom_reset]:
            btn.setIconSize(QSize(20, 20))
            btn.setFixedSize(30, 30)

        # Delegar zoom ao renderizador (se existir)
        self.btn_zoom_menos.clicked.connect(lambda: self.gerar.ajustar_zoom(-0.1) if hasattr(self, "gerar") else None)
        self.btn_zoom_mais.clicked.connect(lambda: self.gerar.ajustar_zoom(+0.1) if hasattr(self, "gerar") else None)
        self.btn_zoom_reset.clicked.connect(lambda: self.gerar.definir_zoom(1.0) if hasattr(self, "gerar") else None)

        linha_zoom.addWidget(self.btn_zoom_menos)
        linha_zoom.addWidget(self.btn_zoom_reset)
        linha_zoom.addWidget(self.btn_zoom_mais)
        linha_zoom.addStretch()

        cabecalho_layout.addLayout(linha_zoom)

        # ------------------------------        
        # Painel de Mesclar Documentos
        self.painel_mesclar = PainelMesclar()
        self.painel_mesclar.mesclagem_concluida.connect(self.carregar_pdf_mesclado)
        self.painel_mesclar.fechar_sinal.connect(self.fechar_overlay)



        # ------------------------------
        # Linha de Modos de Edição (Editar / Separar)
        # ------------------------------
        linha_modos = QHBoxLayout()
        linha_modos.setAlignment(Qt.AlignmentFlag.AlignLeft)
        linha_modos.setSpacing(30)

        modos = [
            (f"{ICONS_PATH}/file-stack.svg", "Mesclar Documentos"),
            (f"{ICONS_PATH}/book-marked.svg", "Glossário")
        ]

        self.botoes_modos = []

        for svg_path, nome in modos:
            vbox = QVBoxLayout()
            vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(60, 60)
            btn.setIcon(QIcon(svg_path))
            btn.setIconSize(QSize(32, 32))

            btn.setProperty("modo", nome)   #  <<----- AQUI!!!

            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 30px;
                    background-color: #444;
                }
                QPushButton:checked {
                    background-color: #0078d7;
                }
            """)
            btn.clicked.connect(self.selecionar_unico_modo)


            label = QLabel(nome)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: white; font-size: 12px;")

            vbox.addWidget(btn)
            vbox.addWidget(label)
            linha_modos.addLayout(vbox)
            self.botoes_modos.append(btn)

        cabecalho_layout.addLayout(linha_modos)


        # ------------------------------
        # Painel esquerdo
        # ------------------------------
        self.btn_abrir = QPushButton(" Abrir Doc")
        self.btn_abrir.setIcon(QIcon(f"{ICONS_PATH}/folder-plus.svg"))
        # --- Lista lateral moderna com subpastas e renomear ---
        self.lista_paginas = QTreeWidget()
        self.lista_paginas.setHeaderHidden(True)
        self.lista_paginas.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        self.lista_paginas.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.lista_paginas.setDragEnabled(True)
        self.lista_paginas.setAcceptDrops(True)
        self.lista_paginas.setDropIndicatorShown(True)
        self.lista_paginas.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lista_paginas.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.lista_paginas.setIndentation(15)
        self.lista_paginas.setAnimated(True)
        self.lista_paginas.setStyleSheet("""
            QTreeWidget::item {
                padding: 6px;
            }
            QTreeWidget::item:selected {
                background-color: #0078D7;
                color: white;
                border-radius: 5px;
            }
        """)
        # guarda estados de expansão dos top-level items (será preenchido antes de re-render)
        self._expanded_states = {}

        # --- Impede páginas de virarem filhas de outras e documents dentro de documents ---
        def _drop_event_personalizado(event):
            try:
                pos = event.position().toPoint()
                index = self.lista_paginas.indexAt(pos)

                # Se não há índice válido no ponto do drop, cancela (drop fora de item)
                if not index.isValid():
                    print("Drop cancelado: fora de qualquer item (index inválido).")
                    event.ignore()
                    return

                # Obtém item de forma robusta (usa itemFromIndex)
                item_destino = self.lista_paginas.itemFromIndex(index)
                if item_destino is None:
                    print("Drop cancelado: destino não encontrado (itemFromIndex retornou None).")
                    event.ignore()
                    return

                print("DEBUG drop: pos=", pos, " item_destino=", bool(item_destino))

                # Bloqueia se o destino for uma página (tem pai)
                if item_destino.parent():
                    print("Drop bloqueado: destino é página.")
                    event.ignore()
                    return

                # item sendo movido (pode ser None) -> captura estado ANTES do drop
                item_arrastado = self.lista_paginas.currentItem()
                if item_arrastado is None:
                    sels = self.lista_paginas.selectedItems()
                    item_arrastado = sels[0] if sels else None

                texto_arrastado = item_arrastado.text(0) if item_arrastado is not None else None
                era_top_level = (item_arrastado is not None and item_arrastado.parent() is None)

                # snapshot dos top-level names antes do drop (para restauração)
                top_before = [self.lista_paginas.topLevelItem(i).text(0) for i in range(self.lista_paginas.topLevelItemCount())]

                # Impede mover documento dentro de outro documento (caso detectado antes do drop)
                if (item_destino and not item_destino.parent() and 
                    item_arrastado and not item_arrastado.parent() and item_destino != item_arrastado):
                    print("Drop bloqueado: documento dentro de outro documento.")
                    event.ignore()
                    return

                # Chama o comportamento padrão de drop
                QTreeWidget.dropEvent(self.lista_paginas, event)

                # --- Pós-drop: validações de integridade ---
                def _encontra_item_por_texto(txt):
                    for i in range(self.lista_paginas.topLevelItemCount()):
                        top = self.lista_paginas.topLevelItem(i)
                        if top.text(0) == txt:
                            return top
                        for j in range(top.childCount()):
                            if top.child(j).text(0) == txt:
                                return top.child(j)
                    return None

                # Se o item arrastado era top-level, garante que ele não virou filho
                if texto_arrastado and era_top_level:
                    encontrado = _encontra_item_por_texto(texto_arrastado)
                    if encontrado is None:
                        print("Aviso: documento top-level desapareceu após drop — restaurando lista pela lógica.")
                        if hasattr(self, "gerar"):
                            self.gerar.renderizar_com_zoom_padrao()
                        event.accept()
                        return
                    if encontrado.parent() is not None:
                        print("Aviso: documento top-level tornou-se filho — restaurando lista pela lógica.")
                        if hasattr(self, "gerar"):
                            self.gerar.renderizar_com_zoom_padrao()
                        event.accept()
                        return

                # Se o número/nomes dos top-level mudaram de forma inesperada, restaura
                top_after = [self.lista_paginas.topLevelItem(i).text(0) for i in range(self.lista_paginas.topLevelItemCount())]
                # permite reordenação (mesmos nomes, ordem pode mudar) — só restaura se um nome sumiu
                if set(top_before) != set(top_after):
                    print("Aviso: top-level diferente após drop — restaurando pela lógica.")
                    if hasattr(self, "gerar"):
                        self.gerar.renderizar_com_zoom_padrao()
                    event.accept()
                    return

                # Atualiza a ordem lógica
                if hasattr(self, "_atualizar_ordem_paginas"):
                    self._atualizar_ordem_paginas()

                event.accept()
                print("→ Drop finalizado com sucesso.")

            except Exception as e:
                print(f"[ERROR] drop_event_personalizado falhou: {e}")
                event.ignore()


    # Substitui o método padrão do QTreeWidget pela função personalizada
        self.lista_paginas.dropEvent = _drop_event_personalizado


        # --- Permite renomear documentos ---
        self.lista_paginas.itemDoubleClicked.connect(self._renomear_item)

        layout_esquerda = QVBoxLayout()
        layout_esquerda.addWidget(self.btn_abrir)

        # Cria um label com ícone e texto lado a lado
        titulo_widget = QWidget()
        titulo_layout = QHBoxLayout(titulo_widget)
        titulo_layout.setContentsMargins(0, 0, 0, 0)
        titulo_layout.setSpacing(5)  # espaço entre ícone e texto

        # Ícone
        icon_label = QLabel()
        pixmap = QPixmap(f"{ICONS_PATH}/folder-tree.svg").scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(20, 20)  # garante tamanho consistente

        # Texto
        text_label = QLabel("Arquivos e Páginas:")

        # Adiciona ao layout horizontal
        titulo_layout.addWidget(icon_label)
        titulo_layout.addWidget(text_label)
        titulo_layout.addStretch()

        # Adiciona ao layout esquerdo
        layout_esquerda.addWidget(titulo_widget)
        layout_esquerda.addWidget(self.lista_paginas)
        layout_esquerda.addStretch()

        self.btn_abrir.clicked.connect(self.abrir_pdf)

        # ------------------------------
        # Área central com scroll (PDF)
        # ------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.paginas_widget = QWidget()
        self.paginas_layout = QVBoxLayout()
        self.paginas_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.paginas_widget.setLayout(self.paginas_layout)
        self.scroll_area.setWidget(self.paginas_widget)

        # Dicionário para guardar widgets das páginas
        self.paginas_widgets = {}

        # Renderizador das páginas
        self.gerar = RenderizadorPaginas(self.paginas_layout, self.lista_paginas, self.logica, self.scroll_area)

        # conecta sinais globais para atualizar UI quando solicitado (protegido)
        try:
            AppSignals.documentos_atualizados.connect(lambda: self.gerar.renderizar_com_zoom_padrao() if hasattr(self, "gerar") else None)
            AppSignals.layout_update_requested.connect(lambda: self.atualizar_tamanho_paginas())
            AppSignals.layout_update_requested.connect(self._restaurar_expansoes)
        except Exception:
            pass

        # ------------------------------
        # Filtro de arrastar
        # ------------------------------
        self.filtro_arrastar = arrastar(self.scroll_area)
        self.scroll_area.viewport().installEventFilter(self.filtro_arrastar)

        # ------------------------------
        # Layout principal (horizontal)
        # ------------------------------
        layout_central = QVBoxLayout()
        layout_central.addWidget(self.cabecalho_widget)  # Cabeçalho fixo em cima
        layout_central.addWidget(self.scroll_area)       # PDF com scroll abaixo
        central_widget = QWidget()
        central_widget.setLayout(layout_central)

        # ------------------------------
        # Layout da lateral esquerda (já criado antes)
        # ------------------------------
        lado_esquerdo = QWidget()
        lado_esquerdo.setLayout(layout_esquerda)
        # guarda referência para painel
        self.painel_widget = lado_esquerdo

        # ------------------------------
        # Splitter horizontal (arrastar para esconder a lista lateral)
        # ------------------------------
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(lado_esquerdo)
        self.splitter.addWidget(central_widget)
        # Define o tamanho relativo inicial
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        # ------------------------------
        # Container principal
        # ------------------------------
        layout_principal = QVBoxLayout()
        layout_principal.addWidget(self.splitter)

        container = QWidget()
        container.setLayout(layout_principal)
        self.setCentralWidget(container)

        # ------------------------------
        # Atalhos de teclado (funcionam na janela inteira)
        # ------------------------------
        desfazer_acao = QAction(self)
        desfazer_acao.setShortcut(QKeySequence("Ctrl+Z"))
        desfazer_acao.triggered.connect(self.desfazer_acao)
        self.addAction(desfazer_acao)

        refazer_acao = QAction(self)
        refazer_acao.setShortcut(QKeySequence("Ctrl+Alt+Z"))
        refazer_acao.triggered.connect(self.refazer_acao)
        self.addAction(refazer_acao)

        # ------------------------------
        # Botão "mostrar painel" (fica visível quando o painel lateral é fechado)
        # ------------------------------
        self.btn_mostrar_painel = QPushButton()
        self.btn_mostrar_painel.setIcon(QIcon(f"{ICONS_PATH}/folder-tree.svg"))
        self.btn_mostrar_painel.setFixedSize(20, 100)
        self.btn_mostrar_painel.setIconSize(QSize(20, 20))
        self.btn_mostrar_painel.setVisible(False)
        # referencia como icone_painel para métodos que usam esse nome
        self.icone_painel = self.btn_mostrar_painel

        self.btn_mostrar_painel.clicked.connect(lambda: self.splitter.setSizes([self.tamanho_padrao, self.width() - self.tamanho_padrao]))

        # Adiciona o botão sobre o container principal
        self.btn_mostrar_painel.setParent(container)
        # usa função de reposicionamento para posicionar corretamente
        self._reposicionar_botao = lambda: self.btn_mostrar_painel.move(10, max(10, self.height() - 120))
        self._reposicionar_botao()
        self.btn_mostrar_painel.raise_()  # garante que ele fique visível por cima

        # ------------------------------
        # Timer para detectar se o painel foi escondido
        # ------------------------------
        def verificar_painel_escondido():
            tamanhos = self.splitter.sizes()
            self.btn_mostrar_painel.setVisible(tamanhos[0] < 30)

        self.timer_splitter = QTimer()
        self.timer_splitter.timeout.connect(verificar_painel_escondido)
        self.timer_splitter.start(200)

        # Para permitir arrastar o conteúdo
        self._arrastando = False
        self._pos_inicial = None
        self.scroll_area.viewport().setMouseTracking(True)

    def _finalizar_mover_e_atualizar(self, pagina_id, novo_idx):
        """
        Atualiza a posição de uma página na árvore lateral após arrastar.
        pagina_id: ID da página que foi movida
        novo_idx: novo índice de posição dentro do documento
        """
        def _extrair_id(user_data):
            # user_data pode ser o id direto ou um dict {'tipo': 'pagina', 'pagina_id': id}
            if isinstance(user_data, dict):
                return user_data.get("pagina_id")
            return user_data

        # Percorre todos os documentos (top-level items)
        for i in range(self.lista_paginas.topLevelItemCount()):
            doc_item = self.lista_paginas.topLevelItem(i)
            # Procura a página pelo UserRole
            for j in range(doc_item.childCount()):
                pagina_item = doc_item.child(j)
                stored = pagina_item.data(0, Qt.ItemDataRole.UserRole)
                pid = _extrair_id(stored)
                if pid == pagina_id:
                    # Remove o item da posição antiga
                    doc_item.takeChild(j)
                    # Insere na nova posição
                    doc_item.insertChild(novo_idx, pagina_item)
                    break

        # Atualiza a ordem lógica das páginas
        self._atualizar_ordem_paginas()

    def _renomear_item(self, item, column):
        """Permite renomear um documento ao dar duplo clique."""
        texto_atual = item.text(0)
        novo_nome, ok = QInputDialog.getText(self, "Renomear", "Novo nome:", text=texto_atual)
        if ok and novo_nome.strip():
            item.setText(0, novo_nome.strip())

    def _atualizar_ordem_paginas(self):
        """Atualiza a ordem lógica das páginas conforme a nova hierarquia da árvore."""
        def _extrair_id(user_data):
            if isinstance(user_data, dict):
                return user_data.get("pagina_id")
            return user_data

        nova_ordem_docs = {}
        # guarda estado expanded atual
        expanded = {}
        for i in range(self.lista_paginas.topLevelItemCount()):
            doc_item = self.lista_paginas.topLevelItem(i)
            nome_doc = doc_item.text(0)
            expanded[nome_doc] = doc_item.isExpanded()

            paginas = []
            for j in range(doc_item.childCount()):
                pagina_item = doc_item.child(j)
                raw = pagina_item.data(0, Qt.ItemDataRole.UserRole)
                pagina_id = _extrair_id(raw)
                if pagina_id is not None:
                    paginas.append(pagina_id)

            nova_ordem_docs[nome_doc] = paginas

        # Atualiza os dados globais
        for nome_doc, paginas in nova_ordem_docs.items():
            if nome_doc in G.DOCUMENTOS:
                G.DOCUMENTOS[nome_doc]["paginas"] = paginas

        # salva para restaurar após render
        self._expanded_states = expanded

        # Emite sinal para atualizar a UI em vez de chamar direto
        try:
            AppSignals.documentos_atualizados.emit()
        except Exception:
            # fallback: tenta renderizar diretamente se sinal falhar
            if hasattr(self, "gerar"):
                self.gerar.renderizar_com_zoom_padrao()

    def _restaurar_expansoes(self):
        """Restaura o estado de expansão dos top-level items salvo em self._expanded_states."""
        if not hasattr(self, "_expanded_states") or not self._expanded_states:
            return
        for i in range(self.lista_paginas.topLevelItemCount()):
            doc_item = self.lista_paginas.topLevelItem(i)
            nome_doc = doc_item.text(0)
            if nome_doc in self._expanded_states:
                try:
                    doc_item.setExpanded(bool(self._expanded_states[nome_doc]))
                except Exception:
                    pass


    def selecionar_unico_modo(self):
            botao = self.sender()

            # desmarca os outros
            for b in self.botoes_modos:
                if b != botao:
                    b.setChecked(False)

            # usa property("modo") (você já configurou isso ao criar os botões)
            modo = botao.property("modo")
            print("Modo clicado:", modo)

            # se desmarcou, só fecha qualquer overlay aberto
            if not botao.isChecked():
                if hasattr(self, "overlay") and self.overlay:
                    self.fechar_overlay()
                return

            # abre o painel apropriado
            if modo == "Mesclar Documentos":
                painel = PainelMesclar()
                # quando o painel emitir fechar, desmarca o botão e fecha overlay
                painel.fechar_sinal.connect(lambda: (botao.setChecked(False), self.fechar_overlay()))
                self.mostrar_painel_flotante(painel)

            elif modo == "Glossário":
                # exemplo: você pode criar outro painel PainelGlossario()
                painel = QLabel("Painel Glossário (implemente aqui)")
                painel.setStyleSheet("color: white; padding: 12px;")
                # conectar fechar se o painel tiver sinal; aqui usamos um botão fictício:
                self.mostrar_painel_flotante(painel)

    def atualizar_renderizador(self):
        # Se você tiver um renderizador de PDFs
        if hasattr(self, "renderizador") and self.renderizador:
            # Exemplo: renderizar a primeira página do novo documento
            self.renderizador.renderizar_com_zoom_padrao()

    def mostrar_painel_flotante(self, widget):
            """
            Mostra `widget` como um painel flutuante centralizado sobre a janela.
            `widget` deve ser um QWidget (ex: PainelMesclar).
            """
            # Fecha overlay anterior se houver
            if hasattr(self, "overlay") and self.overlay:
                self.fechar_overlay()

            # overlay ocupa toda a janela (fundo semi-transparente)
            self.overlay = QFrame(self)
            self.overlay.setObjectName("overlay")
            self.overlay.setGeometry(self.rect())
            self.overlay.setStyleSheet("QFrame#overlay { background: rgba(0,0,0,120); }")
            self.overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

            # caixa central (container) — widget ficará dentro dela
            caixa = QFrame(self.overlay)
            caixa.setStyleSheet("background: #2b2b2b; border-radius: 10px;")
            # tamanho adaptável: 60% da largura, 60% da altura (ajuste à vontade)
            w = max(400, int(self.width() * 0.6))
            h = max(260, int(self.height() * 0.6))
            caixa.setFixedSize(w, h)
            caixa.move((self.width() - w) // 2, (self.height() - h) // 2)

            # layout para caixa e adicionar o widget passado
            layout_caixa = QVBoxLayout(caixa)
            layout_caixa.setContentsMargins(10, 10, 10, 10)
            layout_caixa.setSpacing(8)

            # se for um widget custom (PainelMesclar), queremos que ele preencha a caixa
            widget.setParent(caixa)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            layout_caixa.addWidget(widget)

            # mostra tudo por cima
            self.overlay.show()
            # garante que fica acima de tudo
            self.overlay.raise_()
            caixa.raise_()
            widget.raise_()

            # guarda referência para uso posterior (fechar)
            self.painel_flutuante = widget

    def fechar_overlay(self):
        """Fecha overlay/painel flutuante atual com segurança."""
        try:
            if hasattr(self, "painel_flutuante") and self.painel_flutuante:
                # desconecta sinais para evitar chamadas pendentes
                try:
                    self.painel_flutuante.fechar_sinal.disconnect()
                except Exception:
                    pass
                self.painel_flutuante.setParent(None)
                self.painel_flutuante = None
        finally:
            if hasattr(self, "overlay") and self.overlay:
                try:
                    self.overlay.setParent(None)
                except Exception:
                    pass
                self.overlay = None


    def abrir_painel_mesclar(self, botao):
        # Fecha anterior se houver
        if hasattr(self, "Mesclar Documentos") and self.painel_flutuante:
            self.painel_flutuante.setParent(None)

        def ao_fechar():
            botao.setChecked(False)
            self.painel_flutuante = None

        # Criar painel de mesclar
        self.painel_flutuante = PainelMesclar(
            self, 
            titulo="Mesclar Documentos",
            fechar_callback=ao_fechar
    )

    def carregar_pdf_mesclado(self, caminho_pdf):
        """Recebe o caminho do PDF gerado pelo painel e renderiza no editor."""
        print(f"[DEBUG] PDF mesclado recebido: {caminho_pdf}")

        try:
            # Adiciona o PDF na lógica
            self.logica.abrir_documento(caminho_origem=caminho_pdf)

            # Atualiza a lista lateral e renderiza
            if hasattr(self, "gerar"):
                self.gerar.renderizar_todas(getattr(G, "ZOOM_PADRAO", 1.0))
            self.atualizar_tamanho_paginas()

            # Mostra uma confirmação
            QMessageBox.information(self, "Sucesso", f"Documento mesclado carregado:\n{caminho_pdf}")

        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar", f"Falha ao abrir PDF mesclado:\n{e}")


    # Dentro da classe PDFEditor
    def closeEvent(self, event):
        """
        Evento chamado quando o usuário tenta fechar a janela.
        Pergunta se quer salvar os documentos antes de fechar.
        """
        # Verifica se existem documentos abertos
        if G.DOCUMENTOS:
            resposta = QMessageBox.question(
                self,
                "Fechar Editor",
                "Deseja salvar os documentos antes de sair?",
                 QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if resposta == QMessageBox.StandardButton.No:
                event.accept()  # fecha a janela sem salvar
            else:
                event.ignore()  # cancela o fechamento
        else:
            event.accept()  # não há documentos, fecha normalmente

    # Quando o usuário arrasta algo para a janela
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Só aceita arquivos com extensões suportadas
            urls = event.mimeData().urls()
            if all(url.toLocalFile().lower().endswith(('.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg', '.html', '.xls', '.xlsx')) for url in urls):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    # Quando o usuário solta os arquivos na janela
    def drop_event_personalizado(self, event):
        item_destino = self.lista_paginas.itemAt(event.position().toPoint())

        # Impede que páginas se tornem filhas de outras
        if item_destino and item_destino.parent():
            event.ignore()
            return

        item_arrastado = self.lista_paginas.currentItem()
        if item_destino and not item_destino.parent() and not item_arrastado.parent() and item_destino != item_arrastado:
            event.ignore()
            return

        # Executa o drop padrão
        QTreeWidget.dropEvent(self.lista_paginas, event)

        # Atualiza a lógica
        self._atualizar_ordem_paginas()

    # ------------------------------
    # Abrir PDF
    # ------------------------------
    def abrir_pdf(self):
        # Chamado apenas pelo botão
        caminho_origem, _ = QFileDialog.getOpenFileName(
            self, "Abrir Documento", "",
            "Arquivos suportados (*.pdf *.doc *.docx *.xls *.xlsx *.txt *.html *.jpg *.jpeg *.png)"
        )
        if caminho_origem:  # só continua se o usuário escolheu um arquivo
            self.logica.abrir_documento(caminho_origem=caminho_origem)
            if hasattr(self, "gerar"):
                self.gerar.renderizar_todas(getattr(G, "ZOOM_PADRAO", 1.0))
            self.atualizar_tamanho_paginas()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # reposiciona botão (se função existir)
        if hasattr(self, "_reposicionar_botao"):
            try:
                self._reposicionar_botao()
            except Exception:
                pass
        self.atualizar_tamanho_paginas()

    def atualizar_tamanho_paginas(self):
        largura_disponivel = min(self.scroll_area.viewport().width() - 80, 900)

        # usa pixmaps do renderizador (se disponível)
        if hasattr(self.gerar, "paginas_widgets") and hasattr(self.gerar, "pixmaps_originais"):
            paginas_widgets = self.gerar.paginas_widgets
            pixmaps_originais = self.gerar.pixmaps_originais
        else:
            paginas_widgets = getattr(self, "paginas_widgets", {})
            pixmaps_originais = getattr(self, "pixmaps_originais", {})

        for pagina_id, widget in paginas_widgets.items():
            label_pixmap = widget.findChild(QLabel, "page_image_label")
            pix_original = pixmaps_originais.get(pagina_id)
            if label_pixmap is None or pix_original is None:
                continue

            pix_redim = pix_original.scaled(
                largura_disponivel,
                int(largura_disponivel * pix_original.height() / pix_original.width()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label_pixmap.setPixmap(pix_redim)
            label_pixmap.update()
            widget.update()

        self.paginas_layout.update()
        self.paginas_widget.update()

    # ------------------------------
    # Transferir página
    # ------------------------------
    def transferir_pagina(self, pagina_id):
        origem = G.PAGINAS[pagina_id]["doc_original"]
        outros_docs = [n for n in G.DOCUMENTOS if n != origem]
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
            self.logica.moverPagina(pagina_id, destino)

    # ------------------------------
    # Salvar documentos
    # ------------------------------
    def salvar_pdf_documento(self, nome_doc):
        self.logica.salvar_documento(self, nome_doc)
        self.atualizar_tamanho_paginas()

    # ------------------------------
    # Ações de Desfazer/Refazer
    # ------------------------------
    def desfazer_acao(self):
        # 1. Executa a lógica de desfazer (muda G.DOCUMENTOS)
        G.Historico.desfazer()
        # 2. Força o redesenho da tela lendo os novos dados de G.DOCUMENTOS
        if hasattr(self, "gerar"):
            self.gerar.renderizar_com_zoom_padrao()
        self.atualizar_tamanho_paginas()
        print("🡄 Última ação desfeita!")

    def refazer_acao(self):
        # 1. Executa a lógica de refazer (muda G.DOCUMENTOS)
        G.Historico.refazer()
        # 2. Força o redesenho da tela lendo os novos dados de G.DOCUMENTOS
        if hasattr(self, "gerar"):
            self.gerar.renderizar_com_zoom_padrao()
        self.atualizar_tamanho_paginas()
        print("🡄 Última ação refeita!")

    # ---------------- Zoom ----------------
    def ajustar_zoom(self, delta):
        # delega ao renderizador se disponível
        if hasattr(self, "gerar") and hasattr(self.gerar, "ajustar_zoom"):
            self.gerar.ajustar_zoom(delta)
            return
        novo_zoom = getattr(self, "zoom_factor", 1.0) + delta
        if 0.3 <= novo_zoom <= 3.0:
            self.zoom_factor = novo_zoom
            if hasattr(self, "renderizar_paginas"):
                self.renderizar_paginas()

    def definir_zoom(self, valor):
        if hasattr(self, "gerar") and hasattr(self.gerar, "definir_zoom"):
            self.gerar.definir_zoom(valor)
            return
        self.zoom_factor = valor
        if hasattr(self, "renderizar_paginas"):
            self.renderizar_paginas()

    # ---------------- Painel recolhível ----------------
    def verificar_painel(self):
        tamanhos = self.splitter.sizes()
        if tamanhos[0] < 40:
            if self.painel_widget is not None:
                self.painel_widget.setVisible(False)
            if self.icone_painel is not None:
                self.icone_painel.setVisible(True)
            self.splitter.setSizes([0, self.width()])
        else:
            if self.painel_widget is not None:
                self.painel_widget.setVisible(True)
            if self.icone_painel is not None:
                self.icone_painel.setVisible(False)

    def restaurar_painel(self):
        if self.painel_widget is not None:
            self.painel_widget.setVisible(True)
        if self.icone_painel is not None:
            self.icone_painel.setVisible(False)
        self.splitter.setSizes([self.tamanho_padrao, self.width() - self.tamanho_padrao])


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    app = QApplication(sys.argv)
    try:
        app.setWindowIcon(QIcon("icone.ico"))
    except Exception:
        pass

    janela = PDFEditor()
    # Força o ícone do processo no Windows

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MeuPrograma.1")
    janela.show()
    sys.exit(app.exec())