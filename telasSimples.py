from tkinter import *
from tkinter import filedialog, messagebox
from pdf2image import convert_from_path
from PIL import ImageTk, Image
from PyPDF2 import PdfReader, PdfWriter
import tempfile, os

root = Tk()
root.title("Mini iLovePDF - Reordenar Páginas")
root.geometry("1000x600")

# Lista que guarda: (imagem_tk, caminho_temp_da_pagina)
pages = []

# Frame rolável
canvas = Canvas(root)
scrollbar = Scrollbar(root, orient=VERTICAL, command=canvas.yview)
scrollable_frame = Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.pack(side=RIGHT, fill=Y)


def carregar_pdf():
    global pages
    file_path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
    if not file_path:
        return

    # Limpa o frame anterior
    for widget in scrollable_frame.winfo_children():
        widget.destroy()
    pages.clear()

    # Converte páginas para imagens temporárias
    temp_dir = tempfile.mkdtemp()
    images = convert_from_path(file_path, dpi=100, fmt='png', poppler_path=r"C:\poppler-25.07.0\Library\bin")

    for i, img in enumerate(images):
        img_path = os.path.join(temp_dir, f"page_{i}.png")
        img.save(img_path)
        tk_img = ImageTk.PhotoImage(img.resize((200, 280)))
        pages.append((tk_img, img_path))

    render_paginas()


def mover_pagina(indice, direcao):
    novo_indice = indice + direcao
    if 0 <= novo_indice < len(pages):
        pages[indice], pages[novo_indice] = pages[novo_indice], pages[indice]
        render_paginas()


def render_paginas():
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    for i, (tk_img, _) in enumerate(pages):
        frame = Frame(scrollable_frame, bd=2, relief="groove")
        frame.pack(padx=10, pady=10, fill="x")

        lbl = Label(frame, image=tk_img)
        lbl.pack(side=LEFT)

        info = Frame(frame)
        info.pack(side=LEFT, padx=10)
        Label(info, text=f"Página {i+1}").pack()
        Button(info, text="▲", command=lambda i=i: mover_pagina(i, -1)).pack(pady=2)
        Button(info, text="▼", command=lambda i=i: mover_pagina(i, 1)).pack(pady=2)


def salvar_pdf():
    if not pages:
        return

    # Seleciona o PDF original
    file_path = filedialog.askopenfilename(title="Selecione o PDF original", filetypes=[("PDF","*.pdf")])
    if not file_path:
        return

    reader = PdfReader(file_path)
    writer = PdfWriter()

    # Nova ordem
    ordem_indices = [int(os.path.basename(p[1]).split("_")[1].split(".")[0]) for p in pages]
    for idx in ordem_indices:
        writer.add_page(reader.pages[idx])

    out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
    if not out_path:
        return

    with open(out_path, "wb") as f:
        writer.write(f)

    messagebox.showinfo("Sucesso", "PDF salvo com nova ordem!")


# Menu
menu_bar = Menu(root)
root.config(menu=menu_bar)

file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Arquivo", menu=file_menu)
file_menu.add_command(label="Abrir PDF", command=carregar_pdf)
file_menu.add_command(label="Salvar novo PDF", command=salvar_pdf)
file_menu.add_separator()
file_menu.add_command(label="Sair", command=root.quit)

root.mainloop()
