import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QTextEdit, QDialog, QComboBox,QSizePolicy,QFrame, 
    QVBoxLayout, QHBoxLayout, QPushButton,  QMessageBox,QFileDialog,QSplitter
)
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QAction, QIcon
from PyQt6.QtCore import Qt,QTimer
from logicaPagina import LogicaPagina as logica
import fitz
from PyQt6.QtCore import QSize


from pdf_viewer import RenderizadorPaginas

import globais as G

from pdf_viewer import ArrastarScrollFilter as arrastar
import warnings



class PDFEditor(QMainWindow):
    def __init__(self):
        
        super().__init__()
        #Caminho base dos ícones
        ICONS_PATH= G.ICONS_PATH
        self.setWindowIcon(QIcon(f"{G.ICONS_PATH}/logo.ico"))


        with open("tema_escuro.qss", "r") as f:
            self.setStyleSheet(f.read())
        self.setWindowTitle("Serena LOVE PDF")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(True)  # Permite arrastar arquivos para a janela inteira

        # ------------------------------
        # Lógica do editor
        # ------------------------------
        self.logica = logica()

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

        self.btn_zoom_menos.clicked.connect(lambda: self.gerar.ajustar_zoom(-0.1))
        self.btn_zoom_mais.clicked.connect(lambda: self.gerar.ajustar_zoom(+0.1))
        self.btn_zoom_reset.clicked.connect(lambda: self.gerar.definir_zoom(1.0))

        linha_zoom.addWidget(self.btn_zoom_menos)
        linha_zoom.addWidget(self.btn_zoom_reset)
        linha_zoom.addWidget(self.btn_zoom_mais)
        linha_zoom.addStretch()

        cabecalho_layout.addLayout(linha_zoom)


        # ------------------------------
        # Linha de Modos de Edição (Editar / Separar)
        linha_modos = QHBoxLayout()
        linha_modos.setAlignment(Qt.AlignmentFlag.AlignLeft)
        linha_modos.setSpacing(30)

        modos = [
            ("🖊️", "Ordenar ou mudar"),
            ("✂️", "Dividir ou Juntar")
        ]

        self.botoes_modos = []

        for emoji, nome in modos:
            vbox = QVBoxLayout()
            vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton(emoji)
            btn.setCheckable(True)
            btn.setFixedSize(60, 60)
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 30px;
                    background-color: #444;
                    font-size: 28px;
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
        self.lista_paginas = QListWidget()
        self.lista_paginas.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        self.lista_paginas.setDragEnabled(True)
        self.lista_paginas.setAcceptDrops(True)
        self.lista_paginas.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.lista_paginas.setDefaultDropAction(Qt.DropAction.MoveAction)

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
        # ------------------------------
        # Splitter horizontal (arrastar para esconder a lista lateral)
        # ------------------------------
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(lado_esquerdo)
        self.splitter.addWidget(central_widget)
        # Define o tamanho relativo inicial
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


        self.btn_mostrar_painel.clicked.connect(lambda: self.splitter.setSizes([200, 800]))

        # Adiciona o botão sobre o container principal
        self.btn_mostrar_painel.setParent(container)
        self.btn_mostrar_painel.move(10, self.height() - 600)
        self.btn_mostrar_painel.raise_()  # garante que ele fique visível por cima

        # ------------------------------
        # Reposiciona o botão se a janela for redimensionada
        # ------------------------------
        def reposicionar_botao():
            self.btn_mostrar_painel.move(10, self.height() - 600)

        def resizeEvent(event):
            reposicionar_botao()
            return super(PDFEditor, self).resizeEvent(event)

        self.resizeEvent = resizeEvent

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
      


   
    def selecionar_unico_modo(self):
        for btn in self.botoes_modos:
            if btn != self.sender():
                btn.setChecked(False)
        # Aqui você pode chamar a função real do modo selecionado
        modo = self.sender().text()
        print(f"Modo selecionado: {modo}")



       

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
            # Só aceita arquivos PDF
            urls = event.mimeData().urls()
            if all(url.toLocalFile().lower().endswith(('.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg','.html')) for url in urls):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    # Quando o usuário solta os arquivos na janela
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            caminho_arquivo = url.toLocalFile()
            # aqui passamos direto, nenhum diálogo será aberto
            self.logica.abrir_documento(caminho_origem=caminho_arquivo)
            self.gerar.renderizar_todas(G.ZOOM_PADRAO)
            self.atualizar_tamanho_paginas()

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
            self.gerar.renderizar_todas(G.ZOOM_PADRAO)
            self.atualizar_tamanho_paginas()


    #DEIXA A IMAGEM NO TAMANHO CERTO

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.atualizar_tamanho_paginas()


    def atualizar_tamanho_paginas(self):
        largura_disponivel = min(self.scroll_area.viewport().width() - 80, 900)

        for pagina_id, widget in self.gerar.paginas_widgets.items(): 
            label_pixmap = widget.findChild(QLabel, "page_image_label") 
            pix_original = self.gerar.pixmaps_originais.get(pagina_id)
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
        self.atualizar_tamanho_paginas


    # ------------------------------
    # Ações de Desfazer/Refazer
    # ------------------------------
    def desfazer_acao(self):
        # 1. Executa a lógica de desfazer (muda G.DOCUMENTOS)
        G.Historico.desfazer()
        # 2. 💥 Força o redesenho da tela lendo os novos dados de G.DOCUMENTOS
        self.gerar.renderizar_com_zoom_padrao() 
        self.atualizar_tamanho_paginas()
        print("🡄 Última ação desfeita!")
    def refazer_acao(self):
        # 1. Executa a lógica de refazer (muda G.DOCUMENTOS)
        G.Historico.refazer()
        # 2. 💥 Força o redesenho da tela lendo os novos dados de G.DOCUMENTOS
        self.gerar.renderizar_com_zoom_padrao() 
        self.atualizar_tamanho_paginas()
        print("🡄 Última ação refeita!")



 # ---------------- Zoom ----------------
    def ajustar_zoom(self, delta):
        novo_zoom = self.zoom_factor + delta
        if 0.3 <= novo_zoom <= 3.0:
            self.zoom_factor = novo_zoom
            self.renderizar_paginas()

    def definir_zoom(self, valor):
        self.zoom_factor = valor
        self.renderizar_paginas()

    
    # ---------------- Painel recolhível ----------------
    def verificar_painel(self):
        tamanhos = self.splitter.sizes()
        if tamanhos[0] < 40:
            self.painel_widget.setVisible(False)
            self.icone_painel.setVisible(True)
            self.splitter.setSizes([0, self.width()])
        else:
            self.painel_widget.setVisible(True)
            self.icone_painel.setVisible(False)

    def restaurar_painel(self):
        self.painel_widget.setVisible(True)
        self.icone_painel.setVisible(False)
        self.splitter.setSizes([self.tamanho_padrao, self.width() - self.tamanho_padrao])




if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icons\logo.ico"))

    janela = PDFEditor()
    janela.show()
    sys.exit(app.exec())
