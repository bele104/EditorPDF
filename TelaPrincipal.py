import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QTextEdit, QDialog, QComboBox,QSizePolicy,QFrame, QVBoxLayout, QHBoxLayout, QPushButton,  QMessageBox,QFileDialog
)
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QAction
from PyQt6.QtCore import Qt
from logicaPagina import LogicaPagina as logica
import fitz

from pdf_viewer import RenderizadorPaginas

import globais as G


class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PoDe Fazer café? (PDF)")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(True)  # Permite arrastar arquivos para a janela inteira

        # ------------------------------
        # Lógica do editor
        # ------------------------------
        self.logica = logica()

        # ------------------------------
        # Botões de cabeçalho fixo acima do PDF (direita)
        # ------------------------------
        self.cabecalho_widget = QWidget()
        cabecalho_layout = QVBoxLayout(self.cabecalho_widget)
        cabecalho_layout.setContentsMargins(5, 5, 5, 5)
        cabecalho_layout.setSpacing(5)
        
        # Linha 1: Desfazer e Refazer centralizados
        linha_atalhos = QHBoxLayout()
        linha_atalhos.addStretch()
        
        self.btn_desfazer_top = QPushButton("↩︎")
        self.btn_desfazer_top.clicked.connect(self.desfazer_acao)
        linha_atalhos.addWidget(self.btn_desfazer_top)
        
        self.btn_refazer_top = QPushButton("↪︎")
        self.btn_refazer_top.clicked.connect(self.refazer_acao)
        linha_atalhos.addWidget(self.btn_refazer_top)
        
        linha_atalhos.addStretch()
        cabecalho_layout.addLayout(linha_atalhos)
        
        # Linha 2: Botão de extrair texto centralizado
        linha_extrair = QHBoxLayout()
        linha_extrair.addStretch()
        self.btn_extrair_top = QPushButton("✏️")
        self.btn_extrair_top.clicked.connect(self.mostrar_texto_pdf)
        linha_extrair.addWidget(self.btn_extrair_top)
        linha_extrair.addStretch()
        cabecalho_layout.addLayout(linha_extrair)

        # ------------------------------
        # Painel esquerdo
        # ------------------------------
        self.btn_abrir = QPushButton("Abrir Documento")
        self.lista_paginas = QListWidget()
        self.lista_paginas.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)

        layout_esquerda = QVBoxLayout()
        layout_esquerda.addWidget(self.btn_abrir)
        layout_esquerda.addWidget(QLabel("Arquivos e Páginas"))
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
        # Layout principal (horizontal)
        # ------------------------------
        layout_central = QVBoxLayout()
        layout_central.addWidget(self.cabecalho_widget)  # Cabeçalho fixo em cima
        layout_central.addWidget(self.scroll_area)       # PDF com scroll abaixo
        central_widget = QWidget()
        central_widget.setLayout(layout_central)

        layout_principal = QHBoxLayout()
        layout_principal.addLayout(layout_esquerda, 1)
        layout_principal.addWidget(central_widget, 4)

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
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if resposta == QMessageBox.StandardButton.Yes:
                # Salva todos os documentos abertos
                for nome_doc in G.DOCUMENTOS.keys():
                    self.logica.salvar_documento(self, nome_doc)
                event.accept()  # fecha a janela
            elif resposta == QMessageBox.StandardButton.No:
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
            if all(url.toLocalFile().lower().endswith(('.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg', '.xlsx', '.xls','.html')) for url in urls):
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
        for pagina_id, pagina_info in G.PAGINAS.items():
            nome_doc = pagina_info["doc_original"]
            descricao = pagina_info["descricao"]
            try:
                doc = G.DOCUMENTOS[nome_doc]["doc"]
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
        self.atualizar_tamanho_paginas()
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = PDFEditor()
    janela.show()
    sys.exit(app.exec())
