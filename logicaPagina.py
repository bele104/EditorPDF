import fitz
import copy
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal


class LogicaPagina(QObject):
    documentos_atualizados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.documentos = {}  # nome_doc -> {"doc": fitz.Document, "paginas": [pagina_ids]}
        self.paginas = {}     # pagina_id -> {"descricao", "doc_original", "pagina_num"}
        self.historico = []
        self.future = []

    # ------------------------------
    # Estado (Desfazer / Refazer)
    # ------------------------------
    def salvar_estado(self):
        estado = {
            "documentos": copy.deepcopy({
                nome: {"paginas": dados["paginas"][:]}
                for nome, dados in self.documentos.items()
            }),
            "paginas": copy.deepcopy({
                pid: {
                    "descricao": p["descricao"],
                    "doc_original": p["doc_original"],
                    "pagina_num": p["pagina_num"],
                }
                for pid, p in self.paginas.items()
            }),
        }
        self.historico.append(estado)
        self.future.clear()

    def desfazer(self):
        if not self.historico:
            return
        estado = self.historico.pop()
        self.future.append({
            "documentos": copy.deepcopy({
                nome: {"paginas": dados["paginas"][:]}
                for nome, dados in self.documentos.items()
            }),
            "paginas": copy.deepcopy(self.paginas),
        })
        self._restaurar_estado(estado)
        self.documentos_atualizados.emit()

    def refazer(self):
        if not self.future:
            return
        estado = self.future.pop()
        self.historico.append({
            "documentos": copy.deepcopy({
                nome: {"paginas": dados["paginas"][:]}
                for nome, dados in self.documentos.items()
            }),
            "paginas": copy.deepcopy(self.paginas),
        })
        self._restaurar_estado(estado)
        self.documentos_atualizados.emit()

    def _restaurar_estado(self, estado):
        for nome_doc, dados in self.documentos.items():
            # mantém os fitz.Document abertos
            if nome_doc in estado["documentos"]:
                dados["paginas"] = estado["documentos"][nome_doc]["paginas"]

        self.paginas = estado["paginas"]

    # ------------------------------
    # Abrir Documento
    # ------------------------------
    def abrir_documento(self, janela):
        caminho, _ = QFileDialog.getOpenFileName(janela, "Abrir PDF", "", "PDF Files (*.pdf)")
        if not caminho:
            return False
        try:
            doc = fitz.open(caminho)
            nome_doc = caminho.split("/")[-1]
            self.documentos[nome_doc] = {"doc": doc, "paginas": []}

            for i in range(len(doc)):
                pid = f"{nome_doc}_p{i}"
                self.paginas[pid] = {
                    "descricao": f"{nome_doc} - Página {i+1}",
                    "doc_original": nome_doc,
                    "pagina_num": i
                }
                self.documentos[nome_doc]["paginas"].append(pid)

            self.salvar_estado()
            self.documentos_atualizados.emit()
            return True
        except Exception as e:
            QMessageBox.critical(janela, "Erro", f"Erro ao abrir PDF: {e}")
            return False

    # ------------------------------
    # Operações em páginas
    # ------------------------------
    def mover_para_cima(self, nome_doc, index):
        if index > 0:
            paginas = self.documentos[nome_doc]["paginas"]
            paginas[index - 1], paginas[index] = paginas[index], paginas[index - 1]
            self.salvar_estado()
            self.documentos_atualizados.emit()

    def mover_para_baixo(self, nome_doc, index):
        paginas = self.documentos[nome_doc]["paginas"]
        if index < len(paginas) - 1:
            paginas[index + 1], paginas[index] = paginas[index], paginas[index + 1]
            self.salvar_estado()
            self.documentos_atualizados.emit()

    def excluir_pagina(self, nome_doc, index):
        paginas = self.documentos[nome_doc]["paginas"]
        if 0 <= index < len(paginas):
            paginas.pop(index)
            self.salvar_estado()
            self.documentos_atualizados.emit()

    def mover_pagina_para_outro(self, pagina_id, destino):
        origem = self.paginas[pagina_id]["doc_original"]
        if origem == destino:
            return
        self.documentos[origem]["paginas"].remove(pagina_id)
        self.documentos[destino]["paginas"].append(pagina_id)
        self.paginas[pagina_id]["doc_original"] = destino
        self.salvar_estado()
        self.documentos_atualizados.emit()

    # ------------------------------
    # Salvar Documento
    # ------------------------------
    def salvar_documento(self, janela, nome_doc):
        caminho, _ = QFileDialog.getSaveFileName(janela, f"Salvar {nome_doc}", "", "PDF Files (*.pdf)")
        if not caminho:
            return
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
