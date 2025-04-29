import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
from PIL import Image, ImageTk
from deepface import DeepFace
import cv2

modelo = DeepFace.build_model("ArcFace")

def selecionar_pasta():
    pasta = filedialog.askdirectory(title='Selecione a pasta com as fotos')
    return pasta

def criar_pasta_saida(pasta_base):
    pasta_saida = os.path.join(pasta_base, "Faces_Agrupadas")
    os.makedirs(pasta_saida, exist_ok=True)
    falha_pasta = os.path.join(pasta_saida, "Falha_na_Identificacao")
    os.makedirs(falha_pasta, exist_ok=True)
    return pasta_saida, falha_pasta

def perguntar_usuario(img1_path, img2_path):
    resposta = {'resultado': None}

    def confirmar_sim():
        resposta['resultado'] = True
        popup.destroy()

    def confirmar_nao():
        resposta['resultado'] = False
        popup.destroy()

    popup = Toplevel(root)
    popup.title("Confirmação Manual")
    popup.geometry("600x400")
    popup.grab_set()

    frame = ctk.CTkFrame(popup)
    frame.pack(pady=20)

    img1 = Image.open(img1_path).resize((250, 250))
    img2 = Image.open(img2_path).resize((250, 250))
    img1_tk = ImageTk.PhotoImage(img1)
    img2_tk = ImageTk.PhotoImage(img2)

    label1 = ctk.CTkLabel(frame, image=img1_tk, text="")
    label1.grid(row=0, column=0, padx=10)

    label2 = ctk.CTkLabel(frame, image=img2_tk, text="")
    label2.grid(row=0, column=1, padx=10)

    texto = ctk.CTkLabel(popup, text="Essas fotos são da mesma pessoa?", font=("Arial", 18))
    texto.pack(pady=10)

    botoes_frame = ctk.CTkFrame(popup)
    botoes_frame.pack(pady=10)

    botao_sim = ctk.CTkButton(botoes_frame, text="Sim", command=confirmar_sim, width=120)
    botao_sim.grid(row=0, column=0, padx=20)

    botao_nao = ctk.CTkButton(botoes_frame, text="Não", command=confirmar_nao, width=120)
    botao_nao.grid(row=0, column=1, padx=20)

    popup.wait_window()
    return resposta['resultado']

def calcular_distancia(img1, img2):
    try:
        result = DeepFace.verify(img1_path=img1, img2_path=img2, model_name="ArcFace", model=modelo, enforce_detection=False)
        return result['distance']
    except Exception as e:
        print(f"Erro ao comparar imagens: {e}")
        return 1.0

def agrupar_faces(pasta_fotos, status_label, progress_bar):
    arquivos = [os.path.join(pasta_fotos, f) for f in os.listdir(pasta_fotos)
                if f.lower().endswith(('jpg', 'jpeg', 'png'))]
    grupos = []

    total_arquivos = len(arquivos)
    if total_arquivos == 0:
        status_label.configure(text="Nenhuma imagem encontrada.")
        return

    pasta_saida, falha_pasta = criar_pasta_saida(pasta_fotos)

    for idx, caminho_foto in enumerate(arquivos):
        try:
            img = cv2.imread(caminho_foto)
            if img is None:
                raise Exception("Imagem inválida")
        except Exception as e:
            print(f"Erro ao carregar {caminho_foto}: {e}")
            shutil.copy2(caminho_foto, falha_pasta)
            continue

        encontrado = False
        for grupo in grupos:
            distancia = calcular_distancia(grupo[0], caminho_foto)

            if distancia < 0.4:
                grupo.append(caminho_foto)
                encontrado = True
                break
            elif distancia < 0.6:
                confirmacao = perguntar_usuario(grupo[0], caminho_foto)
                if confirmacao:
                    grupo.append(caminho_foto)
                    encontrado = True
                    break

        if not encontrado:
            grupos.append([caminho_foto])

        progresso = (idx + 1) / total_arquivos
        progress_bar.set(progresso)
        status_label.configure(text=f"Processando {int(progresso * 100)}%...")
        root.update_idletasks()

    for idx, grupo in enumerate(grupos):
        pasta_pessoa = os.path.join(pasta_saida, f"Pessoa_{idx + 1}")
        os.makedirs(pasta_pessoa, exist_ok=True)
        for foto in grupo:
            try:
                shutil.copy2(foto, pasta_pessoa)
            except Exception as e:
                print(f"Erro ao copiar {foto} para {pasta_pessoa}: {e}")

    progress_bar.set(1)
    status_label.configure(text="Organização concluída!")
    messagebox.showinfo("Finalizado", f"Organização concluída!\n\nTotal de fotos processadas: {len(arquivos)}")

def iniciar_agrupamento():
    pasta = selecionar_pasta()
    if pasta:
        status_label.configure(text="Processando...")
        progress_bar.set(0)
        root.update_idletasks()
        agrupar_faces(pasta, status_label, progress_bar)
    else:
        status_label.configure(text="Nenhuma pasta selecionada.")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Photo Organizer PRO (IA)")
    root.geometry("600x400")

    titulo = ctk.CTkLabel(root, text="Organizador Inteligente de Fotos", font=("Arial", 22))
    titulo.pack(pady=(20, 10))

    botao = ctk.CTkButton(root, text="Selecionar Pasta e Iniciar", command=iniciar_agrupamento, font=("Arial", 16))
    botao.pack(pady=(10, 20))

    progress_bar = ctk.CTkProgressBar(root, width=450)
    progress_bar.set(0)
    progress_bar.pack(pady=(5, 20))

    status_label = ctk.CTkLabel(root, text="Aguardando ação...", font=("Arial", 16))
    status_label.pack(pady=(0, 20))

    root.mainloop()
