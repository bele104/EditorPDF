import os
from docx2pdf import convert
import pandas as pd
import matplotlib.pyplot as plt
import pdfkit
from PIL import Image

def identificar_tipo_arquivo(caminho_arquivo):

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
        '.html':'HTML'
    }

    tipo = tipos_suportados.get(extensao, 'Tipo desconhecido')
    print(f"📄 Arquivo: {nome_arquivo}")
    print(f"🔍 Tipo detectado: {tipo}")
    return tipo

def transformarDoc(caminho_arquivo):
    extensao = os.path.splitext(caminho_arquivo)[1].lower()

    if extensao in ['.doc', '.docx']:
        try:
            print(f"🔄 Convertendo {caminho_arquivo} para PDF...")
            convert(caminho_arquivo)

            caminho_pdf=gerar_caminho_pdf(caminho_arquivo)

            print("✅ Conversão concluída com sucesso!")
            return caminho_pdf

        except Exception as e:
            print(f"❌ Erro ao converter: {e}")
            return None
    else:
        print("⚠️ Arquivo não é do tipo Word (.doc ou .docx).")
        return None
    
def transformarExcel(caminho_excel):

    df = pd.read_excel(caminho_excel)
    fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4
    ax.axis('off')#comando desativa os eixos do gráfico (x e y)
    tabela = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(8)
    tabela.scale(1.2, 1.2)
    caminho_pdf=gerar_caminho_pdf(caminho_excel)
    plt.savefig(caminho_pdf, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ PDF gerado: {caminho_pdf}")
    return caminho_pdf

def transformarHtml(caminho_html, caminho_wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'):   
    
    caminho_pdf=gerar_caminho_pdf(caminho_html)
    # Configuração do wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf=caminho_wkhtmltopdf)
    # Converte o HTML para PDF
    pdfkit.from_file(caminho_html, caminho_pdf, configuration=config)
    return caminho_pdf

def tranformaJpeg(caminho_jpeg):
    # Abre a imagem
    imagem = Image.open(caminho_jpeg)
    # Converte para modo RGB (necessário para salvar como PDF)
    if imagem.mode != 'RGB':
        imagem = imagem.convert('RGB')
    caminho_pdf=gerar_caminho_pdf(caminho_jpeg)
    # Salva como PDF
    imagem.save(caminho_pdf, 'PDF', resolution=100.0)

    return caminho_pdf

def verifica(caminho):
    if not os.path.exists(caminho):
        print("❌ Arquivo não encontrado.")
        return False
    return True

def gerar_caminho_pdf(caminho_jpeg):
    """
    Gera o caminho completo do PDF com base no caminho da imagem JPEG.
    """
    nome_pdf = os.path.splitext(os.path.basename(caminho_jpeg))[0] + '.pdf'
    caminho_pdf = os.path.join(os.path.dirname(caminho_jpeg), nome_pdf)
    print(f'Caminho do PDF: {caminho_pdf}')
    return caminho_pdf




if __name__ == "__main__":
    PDF=False
    input="Tarefas-Semanais.xlsx"

    existe = verifica(input)
    try: 
        if existe:
            print("✅ Arquivo encontrado.")
            while PDF==False:
                tipo= identificar_tipo_arquivo(input) 
                if tipo == "PDF":
                    PDF=True
                    print("📄 Processar PDF")
                elif tipo == "Word (DOCX)":
                    input=transformarDoc(input)
                    print("📝 Processar Word")
                elif tipo == "Excel (XLSX)":
                    input=transformarExcel(input)
                    print("📊 Processar Excel")
                elif tipo == "HTML":    
                    input=transformarHtml(input)
                    print("🌐 Processar HTML")
                elif tipo == "Imagem (JPEG)" or "Imagem (JPG)":
                    input=tranformaJpeg(input)
                    print("🖼️ Processar imagem JPEG")
                else:
                    print("❌ Tipo desconhecido")
                    break

        else:
            print("⚠️ Verifique o caminho do arquivo.")
    
    except Exception as e:
            print(f"⚠️ Erro inesperado: {e}")
