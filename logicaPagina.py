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

            print(f"\n[AÇÃO] Documento aberto: {nome_doc}") # ⬅️ ADIÇÃO DE PRINT
            
            for i in range(len(doc)):
                
                pid = f"{nome_doc}_p{i+1}"

                pagina=doc.load_page(i)
                # Armazena página de forma independente
                G.PAGINAS[pid] = {
                    "descricao": f"{nome_doc}- Página {i+1}",
                    "doc_original": nome_doc,
                    "pagina_num": i,
                }
                # Guarda ID da página no documento
                G.DOCUMENTOS[nome_doc]["paginas"].append(pid)
                
            # O bloco de debug detalhado você já tinha, vou mantê-lo:
            for pid, info in G.PAGINAS.items():
                print(f"Página ID: {pid}")
                for chave, valor in info.items():
                    print(f"   {chave}: {valor}")
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
        G.Historico.salvar_estado()
        paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        paginas[index - 1], paginas[index] = paginas[index], paginas[index - 1]
        
        # 💥 ADIÇÃO DE PRINT COM A NOVA ORDEM
        nova_ordem = [G.PAGINAS[pid]['descricao'] for pid in paginas]
        print(f"\n[AÇÃO] Páginas de '{nome_doc}' movidas para cima.")
        print(f"Nova ordem: {nova_ordem}")
        
        self.documentos_atualizados.emit()

    def mover_para_baixo(self, nome_doc, index):
        paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        if index >= len(paginas) - 1: return
        G.Historico.salvar_estado()
        paginas[index + 1], paginas[index] = paginas[index], paginas[index + 1]
        
        # 💥 ADIÇÃO DE PRINT COM A NOVA ORDEM
        nova_ordem = [G.PAGINAS[pid]['descricao'] for pid in paginas]
        print(f"\n[AÇÃO] Páginas de '{nome_doc}' movidas para baixo.")
        print(f"Nova ordem: {nova_ordem}")

        self.documentos_atualizados.emit()

    def excluir_pagina(self, nome_doc, index):
        paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        if 0 <= index < len(paginas):
            G.Historico.salvar_estado()# apenas aqui, antes de qualquer alteração
            pid_removida = paginas[index] # Captura o ID antes de remover
            paginas.pop(index)
            
            # 💥 ADIÇÃO DE PRINT
            print(f"\n[AÇÃO] Página removida: {G.PAGINAS[pid_removida]['descricao']}")
            print(f"Documento '{nome_doc}' agora tem {len(paginas)} páginas.")
            
            self.documentos_atualizados.emit()

    # No arquivo logicaPagina.py, dentro da classe LogicaPagina

    def mover_pagina_para_outro(self, pagina_id, destino):
        # 💥 CORREÇÃO: Acesso via G
        origem = G.PAGINAS[pagina_id]["doc_original"] 
        
        if origem == destino:
            return
            
        # 💥 CORREÇÃO: Acesso via G.Historico
        G.Historico.salvar_estado() 
        
        # 💥 CORREÇÃO: Acesso via G
        G.DOCUMENTOS[origem]["paginas"].remove(pagina_id)
        G.DOCUMENTOS[destino]["paginas"].append(pagina_id)
        G.PAGINAS[pagina_id]["doc_original"] = destino
        
        self.documentos_atualizados.emit()
    # ------------------------------
    # SALVAR DOCUMENTO
    # ------------------------------

    def salvar_documento(janela, nome_doc):
        caminho, _ = QFileDialog.getSaveFileName(janela, f"Salvar {nome_doc}", "", "PDF Files (*.pdf)")
        if not caminho: return
        try:
            novo_doc = fitz.open()
            for pid in G.DOCUMENTOS[nome_doc]["paginas"]:
                pagina_info = G.PAGINAS[pid]
                doc_original = G.DOCUMENTOS[pagina_info["doc_original"]]["doc"]
                pagina = doc_original.load_page(pagina_info["pagina_num"])
                novo_doc.insert_pdf(doc_original, from_page=pagina.number, to_page=pagina.number)
            novo_doc.save(caminho)
            
            # 💥 ADIÇÃO DE PRINT
            print(f"\n[AÇÃO] Documento '{nome_doc}' salvo com sucesso em: {caminho}")
            
        except Exception as e:
            QMessageBox.critical(janela, "Erro", f"Erro ao salvar PDF: {e}")