import tempfile
import fitz
import os

import copy
from PyQt6.QtGui import QIcon

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal,Qt,QSize
import globais as G 
from conversor import ConversorArquivo as conversor
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox
from conversor import ConversorArquivo as conversor  # importe a classe que você escreveu
from geradorDocumentos import Geradora
from signals import signals as AppSignals

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
            nome_doc_abreviado = f"{abreviar_nome(nome, limite=20)}"
          
            
           
            G.DOCUMENTOS[nome_doc] = {"doc": doc, "paginas": [],"path":caminho}

            print(f"\n[AÇÃO] Documento aberto: { nome_doc_abreviado}") # ⬅️ ADIÇÃO DE PRINT
            
            for i in range(len(doc)):
                
                pid = f"{nome_doc}_p{i+1}"

                pagina=doc.load_page(i)
                # Armazena página de forma independente
                G.PAGINAS[pid] = {
                    "descricao": f"|--{nome_doc_abreviado}-pag-{i+1}",
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
            try:
                AppSignals.documentos_atualizados.emit()
            except Exception:
                pass
            
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
            
            try:
                AppSignals.documentos_atualizados.emit()
            except Exception:
                pass

            self.documentos_atualizados.emit()


    # ------------------------ PDF Lógica ------------------------
    def excluir_documento(self, janela, nome_doc, apagar_sem_pergunta=False):
        if nome_doc not in G.DOCUMENTOS:
            QMessageBox.warning(janela, "Erro", "Documento não encontrado!")
            return

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

        # Remove páginas
        ids_paginas = G.DOCUMENTOS[nome_doc]["paginas"]
        for pid in ids_paginas:
            if pid in G.PAGINAS:
                del G.PAGINAS[pid]
        del G.DOCUMENTOS[nome_doc]

        G.Historico.salvar_estado()
        self.documentos_atualizados.emit()
        print(f"[AÇÃO] Documento '{nome_doc}' excluído com sucesso.")






    # ------------------------ Renderização segura ------------------------
    def renderizar_com_zoom_padrao(self):
        """Atualiza todas as páginas com o zoom atual sem recriar widgets."""
        if getattr(self, "bloquear_render", False):
            return  # evita loop de sinais

        for pid, widget in list(self.paginas_widgets.items()):
            # ⚠️ Protege contra páginas que foram apagadas do banco
            if pid not in G.PAGINAS:
                continue

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
        try:
            AppSignals.documentos_atualizados.emit()
        except Exception:
            pass

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

    def cortar_documento(self, page_above, page_below):
        print("\n\n===================== CORTE DE DOCUMENTO =====================")
        print(f"page_above = {page_above}")
        print(f"page_below = {page_below}")

        # documento de origem
        doc_origem = G.PAGINAS[page_above]["doc_original"]
        print(f"Documento de origem: {doc_origem}")

        paginas = G.DOCUMENTOS[doc_origem]["paginas"]
        doc_fisico_original = G.DOCUMENTOS[doc_origem]["doc"]

        print(f"📄 Páginas atuais do documento: {paginas}")

        # índice do corte
        idx_corte = paginas.index(page_below)
        print(f"📌 Corte no índice: {idx_corte}")
        print(f"   - parte1 = páginas antes do índice")
        print(f"   - parte2 = páginas a partir do índice")

        # páginas da parte 1 e parte 2
        parte1 = paginas[:idx_corte]
        parte2 = paginas[idx_corte:]

        print(f"🟦 Parte 1 ({len(parte1)} páginas): {parte1}")
        print(f"🟩 Parte 2 ({len(parte2)} páginas): {parte2}")

        # ------------------------------------------------------------
        #  🔥 CORTAR DE VERDADE: criar dois PDFs separados de verdade
        # ------------------------------------------------------------

    
        
        # cria PDF para parte1
        novo_pdf_parte1 = fitz.open()
        for pid in parte1:
            idx = G.PAGINAS[pid]["fitz_index"]
            novo_pdf_parte1.insert_pdf(doc_fisico_original, from_page=idx, to_page=idx)

        # cria PDF para parte2
        novo_pdf_parte2 = fitz.open()
        for pid in parte2:
            idx = G.PAGINAS[pid]["fitz_index"]
            novo_pdf_parte2.insert_pdf(doc_fisico_original, from_page=idx, to_page=idx)

        print("\n🗂️ PDFs físicos criados separadamente (parte1 + parte2).")

        # renomeia documento original para parte1
        G.DOCUMENTOS[doc_origem]["paginas"] = parte1
        G.DOCUMENTOS[doc_origem]["doc"] = novo_pdf_parte1

        # cria novo nome
        novo_nome = f"{doc_origem}_parte2"
        i = 1
        while novo_nome in G.DOCUMENTOS:
            novo_nome = f"{doc_origem}_parte2_{i}"
            i += 1

        print(f"📑 Novo documento criado: {novo_nome}")

        # cria novo documento com parte 2 (PDF separado!)
        G.DOCUMENTOS[novo_nome] = {
            "doc": novo_pdf_parte2,
            "paginas": parte2,
            "path": G.DOCUMENTOS[doc_origem]["path"],
        }

        # atualiza doc_original das páginas da parte2
        print("\n🔁 Atualizando doc_original para parte 2:")
        for pid in parte2:
            print(f" • {pid}: '{G.PAGINAS[pid]['doc_original']}' → '{novo_nome}'")
            G.PAGINAS[pid]["doc_original"] = novo_nome

        # re-escreve o índice das páginas do documento 1
        print("\n🔢 Recalculando fitz_index da Parte 1:")
        for novo_idx, pid in enumerate(parte1):
            G.PAGINAS[pid]["fitz_index"] = novo_idx
            print(f" • {pid}: fitz_index → {novo_idx}")

        # re-escreve o índice das páginas do documento 2
        print("\n🔢 Recalculando fitz_index da Parte 2:")
        for novo_idx, pid in enumerate(parte2):
            G.PAGINAS[pid]["fitz_index"] = novo_idx
            print(f" • {pid}: fitz_index → {novo_idx}")

        print("\n📘 RESULTADO FINAL DO CORTE:")
        print(f" - {doc_origem}: {G.DOCUMENTOS[doc_origem]['paginas']}")
        print(f" - {novo_nome}: {G.DOCUMENTOS[novo_nome]['paginas']}")

        print("=================== FIM DO CORTE DE DOCUMENTO ===================\n\n")

        AppSignals.documentos_atualizados.emit()
        self.documentos_atualizados.emit()

    def mesclar_documentos_selecionados(self, lista_caminhos):
        """
        Recebe uma lista de caminhos de arquivos (não G.DOCUMENTOS),
        converte todos para PDF e mescla em um único arquivo temporário.
        Retorna o caminho do PDF final.
        """
        import tempfile
        import os
        import fitz  # PyMuPDF

        print("\n🧩 [DEBUG] Iniciando mesclagem de documentos externos...")
        print(f"📜 Lista de caminhos recebida: {lista_caminhos}")

        conversor_instancia = conversor()  # cria o conversor real
        pdf_temp_files = []

        # Cria caminho temporário de saída
        fd, caminho_saida = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        print(f"📂 Caminho de saída temporário criado: {caminho_saida}")

        # Converter todos os arquivos em PDF
        for caminho in lista_caminhos:
            print(f"🔍 [DEBUG] Processando arquivo: {caminho}")
            if not os.path.exists(caminho):
                print(f"⚠️ Arquivo não encontrado: {caminho}")
                continue

            pdf_path = conversor_instancia.processar_arquivo(caminho)
            if pdf_path:
                print(f"✅ PDF temporário gerado: {pdf_path}")
                pdf_temp_files.append(pdf_path)
            else:
                print(f"❌ Falha ao converter {caminho}")

        if not pdf_temp_files:
            print("❌ Nenhum arquivo convertido para PDF. Abortando mesclagem.")
            return None

        # Mesclar todos os PDFs
        print(f"🧮 Iniciando mesclagem de {len(pdf_temp_files)} PDFs...")
        doc_final = fitz.open()
        for pdf in pdf_temp_files:
            try:
                with fitz.open(pdf) as doc_temp:
                    doc_final.insert_pdf(doc_temp)
            except Exception as e:
                print(f"❌ Falha ao adicionar {pdf}: {e}")

        if doc_final.page_count == 0:
            print("❌ Nenhuma página adicionada ao PDF final. Abortando.")
            return None

        # Salvar PDF final
        try:
            doc_final.save(caminho_saida)
            doc_final.close()
            print(f"✅ PDF mesclado salvo em: {caminho_saida}")
            return caminho_saida
        except Exception as e:
            print(f"❌ Erro ao salvar PDF final: {e}")
            return None
