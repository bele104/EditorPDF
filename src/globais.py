# globais.py
import copy
import os
# globais.py
# --------------------------------
# Variáveis globais do editor PDF
# --------------------------------


# Caminho da pasta src (onde este arquivo está)
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho da pasta raiz do projeto (um nível acima)
ROOT_DIR = os.path.dirname(SRC_DIR)

# Caminho da pasta de assets/icons
ICONS_PATH = os.path.join(ROOT_DIR, "assets", "icons")
TEMA_PATH = os.path.join(ROOT_DIR, "assets", "tema_escuro.qss")
DOCUMENTOS = {}


PAGINAS = {}

HISTORICO = []
FUTURO = []


ZOOM_PADRAO = 1.0

# ------------------------------
# Classe para desfazer/refazer
# ------------------------------
class Historico:
    @staticmethod
    def salvar_estado():
        estado = {
            "documentos": {nome: {"paginas": dados["paginas"][:]} 
                           for nome, dados in DOCUMENTOS.items()},
            "paginas": {pid: {"descricao": p["descricao"],
                              "doc_original": p["doc_original"],
                              "fitz_index": p["fitz_index"]}
                        for pid, p in PAGINAS.items()}
        }
        HISTORICO.append(estado)
        FUTURO.clear()

    @staticmethod
    def desfazer():
        if not HISTORICO:
            return
        estado_atual = {
            "documentos": {nome: {"paginas": dados["paginas"][:]} 
                           for nome, dados in DOCUMENTOS.items()},
            "paginas": copy.deepcopy(PAGINAS)
        }
        FUTURO.append(estado_atual)

        estado = HISTORICO.pop()
        for nome_doc, dados in DOCUMENTOS.items():
            if nome_doc in estado["documentos"]:
                dados["paginas"] = estado["documentos"][nome_doc]["paginas"]

        PAGINAS.clear()
        PAGINAS.update(copy.deepcopy(estado["paginas"]))

    @staticmethod
    def refazer():
        if not FUTURO:
            return
        estado_atual = {
            "documentos": {nome: {"paginas": dados["paginas"][:]} 
                           for nome, dados in DOCUMENTOS.items()},
            "paginas": copy.deepcopy(PAGINAS)
        }
        HISTORICO.append(estado_atual)

        estado = FUTURO.pop()
        for nome_doc, dados in DOCUMENTOS.items():
            if nome_doc in estado["documentos"]:
                dados["paginas"] = estado["documentos"][nome_doc]["paginas"]

        PAGINAS.clear()
        PAGINAS.update(copy.deepcopy(estado["paginas"]))