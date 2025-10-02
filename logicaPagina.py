import fitz
import os

import copy
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
import globais as G 
from conversor import ConversorArquivo as conversor
class LogicaPagina(QObject):
    documentos_atualizados = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.documentos = {}
        self.paginas = {}
        self.conversor_temporarios=conversor()
        self.future = []
        
    # ------------------------------
    # ABRIR DOCUMENTO
    # ------------------------------

    def abrir_documento(self, janela):
        filtros = "Arquivos suportados (*.pdf *.doc *.docx *.xls *.xlsx *.txt *.html *.jpg *.jpeg *.png)"
        caminho_origem, _ = QFileDialog.getOpenFileName(janela, "Abrir Aquivo", "", filtros)
        if not caminho_origem:
            return False
        

       # ex: "meuarquivo.pdf"
        # Converte o arquivo para PDF temporário, se necessário
        caminho = self.conversor_temporarios.processar_arquivo(caminho_origem)
        if not caminho:
            return False
        try:
            doc = fitz.open(caminho)

     
            nome_doc = os.path.basename(caminho_origem)
            # Exemplo: só para referência
            header_nome = f"📄 {nome_doc}"
            G.DOCUMENTOS[nome_doc] = {"doc": doc, "paginas": [],"header": f"📄 {header_nome}"}

            print(G.DOCUMENTOS[nome_doc])
            
            for i in range(len(doc)):
                
                pid = f"{nome_doc}_p{i+1}"

                pagina=doc.load_page(i)
                pix = pagina.get_pixmap()
                # Armazena página de forma independente
                G.PAGINAS[pid] = {
                    "pixmap": pix,  # opcional, só se for renderizar
                    "descricao": f"{nome_doc}- Página {i+1}",
                    "doc_original": nome_doc,
                    "pagina_num": i,
                    
                }
                # Guarda ID da página no documento
                G.DOCUMENTOS[nome_doc]["paginas"].append(pid)
                
            for pid, info in G.PAGINAS.items():
                print(f"Página ID: {pid}")
                for chave, valor in info.items():
                    if chave != "pixmap":  # opcional: não mostrar pixmap pesado
                        print(f"  {chave}: {valor}")
                print("-" * 40)

            G.Historico.salvar_estado()# apenas aqui, antes de qualquer alteração
            self.documentos_atualizados.emit()
       
            return True
        except Exception as e:
            QMessageBox.critical(janela, "Erro", f"Erro ao abrir PDF: {e}")
            return False

    # ------------------------------
    # OPERAÇÕES EM PÁGINAS
    # ------------------------------

    def mover_para_cima(self, nome_doc, index):
        if index <= 0: return
        self.salvar_estado()
        paginas = self.documentos[nome_doc]["paginas"]
        paginas[index - 1], paginas[index] = paginas[index], paginas[index - 1]
        self.documentos_atualizados.emit()

    def mover_para_baixo(self, nome_doc, index):
        paginas = self.documentos[nome_doc]["paginas"]
        if index >= len(paginas) - 1: return
        self.salvar_estado()
        paginas[index + 1], paginas[index] = paginas[index], paginas[index + 1]
        self.documentos_atualizados.emit()

    def excluir_pagina(self, nome_doc, index):
        paginas = self.documentos[nome_doc]["paginas"]
        if 0 <= index < len(paginas):
            G.Historico.salvar_estado()# apenas aqui, antes de qualquer alteração
            paginas.pop(index)
            self.documentos_atualizados.emit()

    def mover_pagina_para_outro(self, pagina_id, destino):
        origem = self.paginas[pagina_id]["doc_original"]
        if origem == destino:
            return
        G.Historico.salvar_estado()# apenas aqui, antes de qualquer alteração
        self.documentos[origem]["paginas"].remove(pagina_id)
        self.documentos[destino]["paginas"].append(pagina_id)
        self.paginas[pagina_id]["doc_original"] = destino
        self.documentos_atualizados.emit()

    # ------------------------------
    # SALVAR DOCUMENTO
    # ------------------------------

    def salvar_documento(self, janela, nome_doc):
        caminho, _ = QFileDialog.getSaveFileName(janela, f"Salvar {nome_doc}", "", "PDF Files (*.pdf)")
        if not caminho: return
        try:
            novo_doc = fitz.open()
            for pid in self.documentos[nome_doc]["paginas"]:
                pagina_info = self.paginas[pid]
                doc_original = self.documentos[pagina_info["doc_original"]]["doc"]
                pagina = doc_original.load_page(pagina_info["pagina_num"])
                novo_doc.insert_pdf(doc_original, from_page=pagina.number, to_page=pagina.number)
            novo_doc.save(caminho)
        except Exception as e:
            QMessageBox.critical(janela, "Erro", f"Erro ao salvar PDF: {e}")
