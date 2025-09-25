import os
from docx2pdf import convert
import pandas as pd
import matplotlib.pyplot as plt
import pdfkit
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib.pagesizes import A4
import tempfile
import shutil

class ConversorArquivo:
    def __init__(self):
        pass

    def identificar_tipo_arquivo(self, caminho_arquivo):
        nome_arquivo = os.path.basename(caminho_arquivo)
        extensao = os.path.splitext(nome_arquivo)[1].lower()

        tipos_suportados = {
            '.pdf': 'PDF',
            '.docx': 'Word (DOCX)',
            '.doc': 'Word (DOC)',
            '.jpg': 'Imagem (JPG)',
            '.jpeg': 'Imagem (JPEG)',
            '.png': 'Imagem (PNG)',
            '.xls': 'Excel (XLS)',
            '.xlsx': 'Excel (XLSX)',
            '.txt': 'Texto (TXT)',
            '.html': 'HTML',
        }

        tipo = tipos_suportados.get(extensao, 'Tipo desconhecido')
        print(f"📄 Arquivo: {nome_arquivo}")
        print(f"🔍 Tipo detectado: {tipo}")
        return tipo

    def transformarDoc(self, caminho_arquivo, caminho_pdf_saida):
        print(f"🔄 Convertendo Word para PDF: {caminho_arquivo}")
        convert(caminho_arquivo, caminho_pdf_saida)
        print(f"✅ PDF gerado: {caminho_pdf_saida}")
        return caminho_pdf_saida
    def transformarExcel(self, caminho_excel, caminho_pdf_saida):
        print(f"🔄 Convertendo Excel para PDF: {caminho_excel}")
        df = pd.read_excel(caminho_excel)
        fig, ax = plt.subplots(figsize=(8.27, 11.69))  # tamanho A4
        ax.axis('off')
        tabela = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
        tabela.auto_set_font_size(False)
        tabela.set_fontsize(8)
        tabela.scale(1.2, 1.2)
        plt.savefig(caminho_pdf_saida, bbox_inches='tight')
        plt.close(fig)
        print(f"✅ PDF gerado: {caminho_pdf_saida}")
        return caminho_pdf_saida

    def transformarHtml(self, caminho_html, caminho_pdf_saida, caminho_wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'):
        print(f"🔄 Convertendo HTML para PDF: {caminho_html}")
        config = pdfkit.configuration(wkhtmltopdf=caminho_wkhtmltopdf)
        pdfkit.from_file(caminho_html, caminho_pdf_saida, configuration=config)
        print(f"✅ PDF gerado: {caminho_pdf_saida}")
        return caminho_pdf_saida

    def transformarImagem(self, caminho_imagem, caminho_pdf_saida):
        imagem = Image.open(caminho_imagem)

        if imagem.mode in ("RGBA", "LA", "P"):
            fundo = Image.new("RGB", imagem.size, (255, 255, 255))
            if imagem.mode == "RGBA":
                fundo.paste(imagem, mask=imagem.split()[3])
            else:
                fundo.paste(imagem)
            imagem = fundo
        elif imagem.mode != "RGB":
            imagem = imagem.convert("RGB")

        imagem.save(caminho_pdf_saida, "PDF", resolution=100.0)
        print(f"✅ Imagem convertida em PDF: {caminho_pdf_saida}")
        return caminho_pdf_saida

    def transformarTxt(self, caminho_txt, caminho_pdf_saida):
        try: 
            c = canvas.Canvas(caminho_pdf_saida, pagesize=A4)
            largura, altura = A4
            with open(caminho_txt, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            
            y = altura - 50
            for linha in linhas:
                c.drawString(50, y, linha.strip())
                y -= 15
                if y < 50:
                    c.showPage()
                    y = altura - 50
            
            c.save()
            print(f"✅ TXT convertido em PDF: {caminho_pdf_saida}")
            return caminho_pdf_saida
        except Exception as e:
            print(f"❌ Erro ao converter TXT para PDF: {e}")
            return None

    def processar_arquivo(self, caminho_arquivo):
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
            return None

        tipo = self.identificar_tipo_arquivo(caminho_arquivo)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        caminho_pdf_temp = temp_file.name
        temp_file.close()

        try:
            if tipo == "PDF":
                shutil.copy(caminho_arquivo, caminho_pdf_temp)
            elif tipo in ["Word (DOCX)", "Word (DOC)"]:
                self.transformarDoc(caminho_arquivo, caminho_pdf_temp)
            elif tipo in ["Excel (XLSX)", "Excel (XLS)"]:
                self.transformarExcel(caminho_arquivo, caminho_pdf_temp)
            elif tipo == "HTML":
                self.transformarHtml(caminho_arquivo, caminho_pdf_temp)
            elif tipo in ["Imagem (JPEG)", "Imagem (JPG)", "Imagem (PNG)"]:
                self.transformarImagem(caminho_arquivo, caminho_pdf_temp)
            elif tipo == "Texto (TXT)":
                self.transformarTxt(caminho_arquivo, caminho_pdf_temp)
            else:
                print(f"❌ Tipo de arquivo não suportado para PDF temporário: {tipo}")
                return None

            print(f"📄 PDF temporário criado em: {caminho_pdf_temp}")
            return caminho_pdf_temp

        except Exception as e:
            print(f"❌ Erro ao gerar PDF temporário: {e}")
            return None
