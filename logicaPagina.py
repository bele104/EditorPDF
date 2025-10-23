import fitz
import os

import copy
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
import globais as G 
from conversor import ConversorArquivo as conversor
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox
from conversor import ConversorArquivo as conversor  # importe a classe que você escreveu
from geradorDocumentos import Geradora

def abreviar_nome(nome, limite=20):
    if len(nome) > limite:
        return nome[:limite - 3] + "..."
    return nome
class LogicaPagina(QObject):
    documentos_atualizados = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.conversor_temporarios=conversor()
        self.future = []
  
    # ------------------------------
    # ABRIR DOCUMENTO
    # ------------------------------

    
    def abrir_documento(self, caminho_origem,janela=None):
        caminho = self.conversor_temporarios.processar_arquivo(caminho_origem)
        if not caminho:
            return False
        try:
            doc = fitz.open(caminho)
            nome_doc = os.path.basename(caminho_origem)
            nome, _ = os.path.splitext(nome_doc)
            # 🔸 Abrevia se for muito longo
            nome_doc_abreviado = f"📄{abreviar_nome(nome, limite=20)}"
   
            
           
            G.DOCUMENTOS[nome_doc] = {"doc": doc, "paginas": [],"path":caminho}

            print(f"\n[AÇÃO] Documento aberto: { nome_doc_abreviado}") # ⬅️ ADIÇÃO DE PRINT
            
            for i in range(len(doc)):
                
                pid = f"{nome_doc}_p{i+1}"

                pagina=doc.load_page(i)
                # Armazena página de forma independente
                G.PAGINAS[pid] = {
                    "descricao": f"{nome_doc_abreviado}- Página {i+1}",
                    "doc_original": nome_doc,
                    # 💥 ESSENCIAL: Este índice PyMuPDF (0-based) é imutável
                    "fitz_index": i, 
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
            if janela:
                QMessageBox.critical(janela, "Erro", f"Erro ao abrir PDF: {e}")
            else:
                QMessageBox.critical(None, "Erro", f"Erro ao abrir PDF: {e}")
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


    def excluir_documento(self, janela, nome_doc, apagar_sem_pergunta=False):
        """
        Exclui o documento da memória e da lista.
        Se apagar_sem_pergunta=False, pergunta ao usuário se quer salvar antes.
        """
        if nome_doc not in G.DOCUMENTOS:
            QMessageBox.warning(janela, "Erro", "Documento não encontrado!")
            return

        # Pergunta apenas se não for apagar depois de salvar
        if not apagar_sem_pergunta:
            resposta = QMessageBox.question(
                janela,
                "Excluir Documento",
                f"Deseja salvar o documento '{nome_doc}' antes de apagar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if resposta == QMessageBox.StandardButton.Cancel:
                return
            elif resposta == QMessageBox.StandardButton.Yes:
                self.salvar_documento_dialog(janela, nome_doc)

        # Remove páginas do documento
        ids_paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        for pid in ids_paginas:
            if pid in G.PAGINAS:
                del G.PAGINAS[pid]

        # Remove o documento
        del G.DOCUMENTOS[nome_doc]

        # Atualiza histórico e sinal
        G.Historico.salvar_estado()
        self.documentos_atualizados.emit()
        print(f"[AÇÃO] Documento '{nome_doc}' excluído com sucesso.")


    def moverPagina(self, pagina_id, destino):
        origem = G.PAGINAS[pagina_id]["doc_original"]
        if origem == destino:
            return

        G.Historico.salvar_estado()

        # 1️⃣ Carrega página original
        pagina_descrição=G.PAGINAS[pagina_id]["descricao"]
        pagina_info = G.PAGINAS[pagina_id]
        doc_origem = G.DOCUMENTOS[origem]["doc"]
        page_index_origem = pagina_info["fitz_index"]

        # 2️⃣ Insere a página original fisicamente no documento destino
        doc_destino = G.DOCUMENTOS[destino]["doc"]
        num_paginas_destino_antes = len(doc_destino)

        doc_destino.insert_pdf(doc_origem, from_page=page_index_origem, to_page=page_index_origem)

        # 3️⃣ Cria um novo ID único para a página no destino
        novo_pid = f"{destino}_p{num_paginas_destino_antes+1}"

        G.PAGINAS[novo_pid] = {
            "descricao": f"{pagina_descrição}-M",
            "doc_original": destino,
            "fitz_index": num_paginas_destino_antes  # novo índice real no destino
        }

        # 4️⃣ Remove do documento de origem e adiciona no destino
        G.DOCUMENTOS[origem]["paginas"].remove(pagina_id)
        G.DOCUMENTOS[destino]["paginas"].append(novo_pid)

        # 5️⃣ Remove o registro antigo para não confundir
        del G.PAGINAS[pagina_id]

        print(f"[AÇÃO] Página movida fisicamente de '{origem}' para '{destino}' como nova página '{novo_pid}'")
        self.documentos_atualizados.emit()
    # ------------------------------
    # SALVAR DOCUMENTO
    # ------------------------------

    # Na classe LogicaPagina
    def salvar_documento_dialog(self, janela, nome_doc):
        """
        Mostra um diálogo para escolher o formato e salvar o documento.
        """
        if nome_doc not in G.DOCUMENTOS:
            QMessageBox.warning(janela, "Erro", "Documento não encontrado!")
            return

        caminho_pdf = G.DOCUMENTOS[nome_doc]["path"]
       # pega os IDs das páginas do documento
        ids_paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        # converte para índices reais dentro do PDF
        ordem_paginas = [G.PAGINAS[pid]["fitz_index"] for pid in ids_paginas]


        dialog = QDialog(janela)
        dialog.setWindowTitle("Salvar Documento")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Escolha o formato para salvar:"))

        combo = QComboBox()
        combo.addItems(["PDF", "Imagem (PNG)", "DOCX"])
        layout.addWidget(combo)

        btn_ok = QPushButton("Salvar")
        layout.addWidget(btn_ok)

        def salvar():
            escolha = combo.currentText()
            geradora = Geradora(caminho_pdf, ordem_paginas, parent=dialog)


            sucesso = False
            if escolha == "PDF":
                caminho, _ = QFileDialog.getSaveFileName(dialog, "Salvar como PDF", "", "PDF Files (*.pdf)")
                if caminho:
                    sucesso = geradora.salvar_como_pdf(caminho)
            elif escolha == "Imagem (PNG)":
                caminho_base, _ = QFileDialog.getSaveFileName(dialog, "Salvar como Imagem", "", "PNG Files (*.png)")
                if caminho_base:
                    sucesso = geradora.salvar_como_imagem(caminho_base, formato="PNG")
            elif escolha == "DOCX":
                caminho, _ = QFileDialog.getSaveFileName(dialog, "Salvar como DOCX", "", "Word Files (*.docx)")
                if caminho:
                    sucesso = geradora.salvar_como_docx(caminho)

            if sucesso:
                QMessageBox.information(dialog, "Sucesso", f"Arquivo salvo com sucesso como {escolha}!")
                self.excluir_documento(janela, nome_doc, apagar_sem_pergunta=True)

            else:
                QMessageBox.critical(dialog, "Erro", f"Falha ao salvar como {escolha}.")

            dialog.accept()

        btn_ok.clicked.connect(salvar)
        dialog.exec()

        