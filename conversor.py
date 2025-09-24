import os
from docx2pdf import convert
import pandas as pd
import matplotlib.pyplot as plt
import pdfkit
from PIL import Image

class ConversorArquivo:
    def __init__(self):
        pass

    def identificar_tipo_arquivo(self, caminho_arquivo):
        """
        Identifica o tipo do arquivo pelo sufixo.
        """
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
            '.html': 'HTML'
        }

        tipo = tipos_suportados.get(extensao, 'Tipo desconhecido')
        print(f"📄 Arquivo: {nome_arquivo}")
        print(f"🔍 Tipo detectado: {tipo}")
        return tipo

    def transformarDoc(self, caminho_arquivo):
        """
        Converte arquivos Word (.doc ou .docx) para PDF.
        """
        print(f"🔄 Convertendo Word para PDF: {caminho_arquivo}")
        convert(caminho_arquivo)
        caminho_pdf = self.gerar_caminho_pdf(caminho_arquivo)
        print(f"✅ PDF gerado: {caminho_pdf}")
        return caminho_pdf

    def transformarExcel(self, caminho_excel):
        """
        Converte planilhas Excel para PDF, transformando em uma tabela visual.
        """
        print(f"🔄 Convertendo Excel para PDF: {caminho_excel}")
        df = pd.read_excel(caminho_excel)
        fig, ax = plt.subplots(figsize=(8.27, 11.69))  # tamanho A4
        ax.axis('off')  # desativa eixos
        tabela = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
        tabela.auto_set_font_size(False)
        tabela.set_fontsize(8)
        tabela.scale(1.2, 1.2)
        caminho_pdf = self.gerar_caminho_pdf(caminho_excel)
        plt.savefig(caminho_pdf, bbox_inches='tight')
        plt.close(fig)
        print(f"✅ PDF gerado: {caminho_pdf}")
        return caminho_pdf

    def transformarHtml(self, caminho_html, caminho_wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'):
        """
        Converte arquivos HTML para PDF usando wkhtmltopdf.
        """
        print(f"🔄 Convertendo HTML para PDF: {caminho_html}")
        caminho_pdf = self.gerar_caminho_pdf(caminho_html)
        config = pdfkit.configuration(wkhtmltopdf=caminho_wkhtmltopdf)
        pdfkit.from_file(caminho_html, caminho_pdf, configuration=config)
        print(f"✅ PDF gerado: {caminho_pdf}")
        return caminho_pdf

    def transformarImagem(self, caminho_imagem):
        """
        Converte imagens (JPG, JPEG, PNG) para PDF.
        """
        print(f"🔄 Convertendo imagem para PDF: {caminho_imagem}")
        imagem = Image.open(caminho_imagem)
        if imagem.mode != 'RGB':
            imagem = imagem.convert('RGB')
        caminho_pdf = self.gerar_caminho_pdf(caminho_imagem)
        imagem.save(caminho_pdf, 'PDF', resolution=100.0)
        print(f"✅ PDF gerado: {caminho_pdf}")
        return caminho_pdf

    def gerar_caminho_pdf(self, caminho_arquivo):
        """
        Gera o caminho do PDF com base no arquivo original.
        """
        nome_pdf = os.path.splitext(os.path.basename(caminho_arquivo))[0] + '.pdf'
        caminho_pdf = os.path.join(os.path.dirname(caminho_arquivo), nome_pdf)
        return caminho_pdf

    def processar_arquivo(self, caminho_arquivo):
        """
        Processa o arquivo e converte para PDF se necessário.
        """
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
            return None

        tipo = self.identificar_tipo_arquivo(caminho_arquivo)

        # Verifica o tipo e chama a função correspondente
        if tipo == "PDF":
            print("📄 Arquivo já é PDF, nenhum processamento necessário.")
            return caminho_arquivo
        elif tipo in ["Word (DOCX)", "Word (DOC)"]:
            return self.transformarDoc(caminho_arquivo)
        elif tipo in ["Excel (XLSX)", "Excel (XLS)"]:
            return self.transformarExcel(caminho_arquivo)
        elif tipo == "HTML":
            return self.transformarHtml(caminho_arquivo)
        elif tipo in ["Imagem (JPEG)", "Imagem (JPG)", "Imagem (PNG)"]:
            return self.transformarImagem(caminho_arquivo)
        else:
            print(f"❌ Tipo desconhecido: {tipo}")
            return None
        
        
