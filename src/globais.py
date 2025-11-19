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
# ------------------------------
# Classe para desfazer/refazer
# ------------------------------
class Historico:
    @staticmethod
    def salvar_estado():
        estado = {
            # cópia das estruturas lógicas dos documentos
            "documentos": {
                nome: {
                    "paginas": dados["paginas"][:],
                    "doc": dados["doc"],   # referência original, não copia
                    "path": dados.get("path")
                }
                for nome, dados in DOCUMENTOS.items()
            },

            # cópia profunda das páginas (doc_original, fitz_index, descricao)
            "paginas": copy.deepcopy(PAGINAS)
        }

        HISTORICO.append(estado)
        FUTURO.clear()


    @staticmethod
    def desfazer():
        if not HISTORICO:
            return

        # salva estado atual → futuro
        estado_atual = {
            "documentos": {
                nome: {
                    "paginas": dados["paginas"][:],
                    "doc": dados["doc"],
                    "path": dados.get("path")
                }
                for nome, dados in DOCUMENTOS.items()
            },
            "paginas": copy.deepcopy(PAGINAS)
        }
        FUTURO.append(estado_atual)

        # restaura estado antigo
        estado = HISTORICO.pop()

        # restaura DOCUMENTOS
        DOCUMENTOS.clear()
        for nome, dados in estado["documentos"].items():
            DOCUMENTOS[nome] = {
                "paginas": dados["paginas"][:],
                "doc": dados["doc"],   # usa a mesma referência
                "path": dados.get("path")
            }

        # restaura PAGINAS
        PAGINAS.clear()
        PAGINAS.update(copy.deepcopy(estado["paginas"]))


    @staticmethod
    def refazer():
        if not FUTURO:
            return

        # salva estado atual → histórico
        estado_atual = {
            "documentos": {
                nome: {
                    "paginas": dados["paginas"][:],
                    "doc": dados["doc"],
                    "path": dados.get("path")
                }
                for nome, dados in DOCUMENTOS.items()
            },
            "paginas": copy.deepcopy(PAGINAS)
        }
        HISTORICO.append(estado_atual)

        # restaura estado futuro
        estado = FUTURO.pop()

        DOCUMENTOS.clear()
        for nome, dados in estado["documentos"].items():
            DOCUMENTOS[nome] = {
                "paginas": dados["paginas"][:],
                "doc": dados["doc"],
                "path": dados.get("path")
            }

        PAGINAS.clear()
        PAGINAS.update(copy.deepcopy(estado["paginas"]))

