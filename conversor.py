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
            '.txt': 'Texto (TXT)',
            '.html': 'HTML',
            
        }

        tipo = tipos_suportados.get(extensao, 'Tipo desconhecido')
        print(f"📄 Arquivo: {nome_arquivo}")
        print(f"🔍 Tipo detectado: {tipo}")
        return tipo

    def transformarDoc(self, caminho_arquivo):
        """
        Converte arquivos Word (.doc ou .docx) para PDF usando Word via docx2pdf.
        """
        try:
            print(f"🔄 Convertendo Word para PDF: {caminho_arquivo}")

            # Gera caminho de saída para o PDF
            caminho_pdf = self.gerar_caminho_pdf(caminho_arquivo)

            # Converte diretamente para o caminho do PDF desejado
            convert(caminho_arquivo, caminho_pdf)
            print(f"✅ PDF gerado: {caminho_pdf}")
            return caminho_pdf

        except Exception as e:
            print(f"❌ Erro ao converter DOC/DOCX: {e}")
            return None

        finally:
            # Força o fechamento de processos do Word (caso tenham ficado abertos)
            os.system("taskkill /f /im WINWORD.EXE >nul 2>&1")

    
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
        return caminho_pdf_saida





    def transformarTxt(self, caminho_txt, caminho_pdf_saida):
        try: 
            c = canvas.Canvas(caminho_pdf_saida, pagesize=A4)
            largura, altura = A4
            with open(caminho_txt, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            
            y = altura - 50  # margem superior
            for linha in linhas:
                c.drawString(50, y, linha.strip())
                y -= 15  # espaço entre linhas
                if y < 50:  # quebra de página
                    c.showPage()
                    y = altura - 50
            
            c.save()
            print(f"✅ TXT convertido em PDF: {caminho_pdf_saida}")
            return caminho_pdf_saida
        except Exception as e:
            print(f"❌ Erro ao converter TXT para PDF: {e}")
            return None


        
    def gerar_caminho_pdf(self, caminho_arquivo):
        """
        Gera o caminho do PDF com base no arquivo original.
        """
        nome_pdf = os.path.splitext(os.path.basename(caminho_arquivo))[0] + '.pdf'
        caminho_pdf = os.path.join(os.path.dirname(caminho_arquivo), nome_pdf)
        print (caminho_pdf)
        return caminho_pdf

    def processar_arquivo(self, caminho_arquivo):
        """
        Processa o arquivo e converte para PDF se necessário.
        """
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
            return None

        tipo = self.identificar_tipo_arquivo(caminho_arquivo)

        # Cria um arquivo temporário com extensão PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        caminho_pdf_temp = temp_file.name
        temp_file.close()  # fecha o arquivo para poder ser usado pelas funções de conversão

        try:
            if tipo == "PDF":
         
                # apenas copia o PDF original para o temporário
                shutil.copy(caminho_arquivo, caminho_pdf_temp)
            elif tipo in ["Word (DOCX)", "Word (DOC)"]:
                caminho_real = self.transformarDoc(caminho_arquivo)
                shutil.copy(caminho_real, caminho_pdf_temp)
            elif tipo == "HTML":
                caminho_real = self.transformarHtml(caminho_arquivo)
                shutil.copy(caminho_real, caminho_pdf_temp)
            elif tipo in ["Imagem (JPEG)", "Imagem (JPG)", "Imagem (PNG)"]:
                self.transformarImagem(caminho_arquivo, caminho_pdf_temp)
                
            elif tipo == "Texto (TXT)":
                self.transformarTxt(caminho_arquivo,caminho_pdf_temp)
               
            else:
                print(f"❌ Tipo de arquivo não suportado para PDF temporário: {tipo}")
                return None

            print(f"📄 PDF temporário criado em: {caminho_pdf_temp}")
            return caminho_pdf_temp

        except Exception as e:
            print(f"❌ Erro ao gerar PDF temporário: {e}")
            return None
        

