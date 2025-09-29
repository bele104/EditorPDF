import fitz  # PyMuPDF
import os
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QListWidgetItem
from geradorDocumentos import Geradora
from conversor import ConversorArquivo

class LogicaPagina:
    def __init__(self):
        self.conversor = ConversorArquivo()
        self.historico = []          # histórico de ações para desfazer
        self.refazer_historico = []  # histórico de ações desfeitas para refazer
        self.documentos = {}         # {nome_arquivo: {"caminho":..., "doc":..., "ordem_paginas":..., "descricao_paginas":...}}

    # -----------------------------
    # Abrir documento
    # -----------------------------
    def abrir_documento(self, parent):
        """Abre um diálogo para escolher e carregar QUALQUER documento"""
        arquivo, _ = QFileDialog.getOpenFileName(
            parent,
            "Abrir documento",
            "",
            "Todos os arquivos (*.*);;Documentos (*.pdf *.docx *.txt);;Imagens (*.png *.jpg *.jpeg)"
        )
        if not arquivo:
            return False

        # --- Conversão obrigatória ---
        caminho_pdf = self.conversor.processar_arquivo(arquivo)
        if not caminho_pdf:
            QMessageBox.warning(parent, "Erro", "Não foi possível converter o arquivo.")
            return False

        # Gera nome automático tipo Documento 0, Documento 1, ...
        contador = len(self.documentos)
        nome = f"Documento {contador}"

        # Abre o PDF convertido
        doc = fitz.open(caminho_pdf)
        self.documentos[nome] = {
            "caminho": caminho_pdf,
            "doc": doc,
            "ordem_paginas": list(range(len(doc))),
            "descricao_paginas": {}
        }

        # limpa histórico ao abrir novo documento
        self.historico.clear()
        self.refazer_historico.clear()
        return True

    # -----------------------------
    # Salvar documento
    # -----------------------------
    def salvar_documento(self, parent, nome_arquivo):
        if nome_arquivo not in self.documentos:
            QMessageBox.warning(parent, "Aviso", "Documento não carregado.")
            return False

        dialog = QDialog(parent)
        dialog.setWindowTitle("Escolher formato")
        dialog.setFixedSize(300, 150)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Selecione o formato para salvar:"))

        combo_formatos = QComboBox()
        combo_formatos.addItems(["PDF", "PNG", "JPG", "DOCX", "TXT"])
        layout.addWidget(combo_formatos)

        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.clicked.connect(dialog.accept)
        layout.addWidget(btn_confirmar)

        if dialog.exec():
            formato = combo_formatos.currentText()
            filtro = f"{formato} (*.{formato.lower()})"
            novo_caminho, _ = QFileDialog.getSaveFileName(
                parent, f"Salvar como {formato}", "", filtro
            )
            if not novo_caminho:
                return False

            doc_info = self.documentos[nome_arquivo]
            geradora = Geradora(doc_info["caminho"], doc_info["ordem_paginas"], parent)

            if formato == "PDF":
                geradora.salvar_como_pdf(novo_caminho)
            elif formato in ["PNG", "JPG"]:
                geradora.salvar_como_imagem(novo_caminho, formato)
            elif formato == "DOCX":
                geradora.salvar_como_docx(novo_caminho)
            elif formato == "TXT":
                geradora.salvar_como_txt(novo_caminho)

            QMessageBox.information(parent, "Sucesso", f"Documento salvo em:\n{novo_caminho}")
            if formato == "PDF":
                doc_info["caminho"] = novo_caminho
                doc_info["doc"] = fitz.open(novo_caminho)
                doc_info["ordem_paginas"] = list(range(len(doc_info["doc"])))
            return True
        return False

    # -----------------------------
    # Mostrar texto
    # -----------------------------
    def mostrar_texto(self, nome_arquivo):
        if nome_arquivo not in self.documentos:
            return ""
        doc_info = self.documentos[nome_arquivo]
        texto_total = ""
        for idx in doc_info["ordem_paginas"]:
            pagina = doc_info["doc"][idx]
            texto_total += f"--- Página {idx+1} ---\n{pagina.get_text('text')}\n\n"
        return texto_total.strip()

    # -----------------------------
    # Renderizar páginas
    # -----------------------------
    def renderizar_paginas(self, zoom=1.0, lista_widget=None):
        """
        Retorna dicionário de pixmaps para cada documento.
        Se lista_widget for fornecido, atualiza a QListWidget.
        """
        all_pixmaps = {}
        if lista_widget:
            lista_widget.clear()

        for nome, doc_info in self.documentos.items():
            pixmaps = []
            for idx in doc_info["ordem_paginas"]:
                pagina = doc_info["doc"][idx]
                mat = fitz.Matrix(zoom, zoom)
                pix = pagina.get_pixmap(matrix=mat)
                pixmaps.append(pix)
                if lista_widget:
                    descricao = doc_info["descricao_paginas"].get(idx, f"Página {idx+1}")
                    item_text = f"{nome} - {descricao}"
                    item = QListWidgetItem(item_text)
                    item.setData(1000, (nome, idx))
                    lista_widget.addItem(item)
            all_pixmaps[nome] = pixmaps
        return all_pixmaps

    # -----------------------------
    # Lógica de manipulação de páginas
    # -----------------------------
    def mover_para_cima(self, nome_arquivo, index):
        paginas = self.documentos[nome_arquivo]["ordem_paginas"]
        if index > 0:
            self.salvar_estado(nome_arquivo)
            paginas[index], paginas[index-1] = paginas[index-1], paginas[index]

    def mover_para_baixo(self, nome_arquivo, index):
        paginas = self.documentos[nome_arquivo]["ordem_paginas"]
        if index < len(paginas) - 1:
            self.salvar_estado(nome_arquivo)
            paginas[index], paginas[index+1] = paginas[index+1], paginas[index]

    def excluir_pagina(self, nome_arquivo, index):
        paginas = self.documentos[nome_arquivo]["ordem_paginas"]
        if 0 <= index < len(paginas):
            self.salvar_estado(nome_arquivo)
            paginas.pop(index)

    def adicionar_descricao(self, nome_arquivo, pagina_num, descricao):
        self.salvar_estado(nome_arquivo)
        self.documentos[nome_arquivo]["descricao_paginas"][pagina_num] = descricao

    # -----------------------------
    # Histórico
    # -----------------------------
    def salvar_estado(self, nome_arquivo):
        doc_info = self.documentos[nome_arquivo]
        estado_atual = {
            "nome_arquivo": nome_arquivo,
            "ordem_paginas": doc_info["ordem_paginas"].copy(),
            "descricao_paginas": doc_info["descricao_paginas"].copy()
        }
        self.historico.append(estado_atual)
        self.refazer_historico.clear()

    def desfazer(self, parent=None):
        if not self.historico:
            if parent:
                QMessageBox.information(parent, "Desfazer", "Nada para desfazer")
            return
        estado = self.historico.pop()
        self.refazer_historico.append({
            "nome_arquivo": estado["nome_arquivo"],
            "ordem_paginas": self.documentos[estado["nome_arquivo"]]["ordem_paginas"].copy(),
            "descricao_paginas": self.documentos[estado["nome_arquivo"]]["descricao_paginas"].copy()
        })
        nome = estado["nome_arquivo"]
        self.documentos[nome]["ordem_paginas"] = estado["ordem_paginas"]
        self.documentos[nome]["descricao_paginas"] = estado["descricao_paginas"]
        if parent:
            parent.renderizar_paginas()

    def refazer(self, parent=None):
        if not self.refazer_historico:
            if parent:
                QMessageBox.information(parent, "Refazer", "Nada para refazer")
            return
        estado = self.refazer_historico.pop()
        self.historico.append({
            "nome_arquivo": estado["nome_arquivo"],
            "ordem_paginas": self.documentos[estado["nome_arquivo"]]["ordem_paginas"].copy(),
            "descricao_paginas": self.documentos[estado["nome_arquivo"]]["descricao_paginas"].copy()
        })
        nome = estado["nome_arquivo"]
        self.documentos[nome]["ordem_paginas"] = estado["ordem_paginas"]
        self.documentos[nome]["descricao_paginas"] = estado["descricao_paginas"]
        if parent:
            parent.renderizar_paginas()

    # -----------------------------
    # Lista organizada de arquivos e páginas
    # -----------------------------
    def obter_lista_arquivos_paginas(self):
        lista = []
        for nome, info in self.documentos.items():
            lista.append((nome, None))  # cabeçalho do arquivo
            for idx in info["ordem_paginas"]:
                lista.append((nome, idx))
        return lista

    def obter_descricao(self, nome_arquivo, pagina_num):
        if pagina_num is None:
            return nome_arquivo
        info = self.documentos.get(nome_arquivo, {})
        return info.get("descricao_paginas", {}).get(pagina_num, f"Página {pagina_num+1}")
