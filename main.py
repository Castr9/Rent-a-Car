# Importação das bibliotecas necessárias
import sqlite3  # Para manipulação de banco de dados
import bcrypt  # Para criptografia de senhas
import tkinter as tk  # Interface gráfica
from tkinter import ttk, messagebox, filedialog  # Widgets e diálogos do Tkinter
from PIL import Image, ImageTk  # Manipulação de imagens
import matplotlib.pyplot as plt  # Para gráficos
import calendar  # Funções de calendário
from datetime import datetime, timedelta  # Manipulação de datas
import os  # Funções para interação com o sistema operacional
import csv  # Leitura e escrita de arquivos CSV

# Constantes e funções de banco de dados
DB_FILE = 'ProjetoFinal/database/informacoes.db'  # Caminho do banco de dados
IMAGE_SIZE = (200, 200)  # Tamanho padrão das imagens


# Função para conectar ao banco de dados
def conectar():
    conn = sqlite3.connect('ProjetoFinal/database/informacoes.db')  # Abre uma conexão com o banco de dados
    return conn


# Função para fechar a conexão com o banco de dados
def fechar_conexao(conn):
    conn.close()


# Funções relacionadas a veículos

# Função para adicionar um veículo à lista e salvar
def adicionar_veiculo(id, marca, modelo, ano, preco, imagem):
    veiculo = [id, marca, modelo, ano, preco, imagem]  # Criação de um novo veículo
    veiculos.append(veiculo)  # Adiciona à lista de veículos
    salvar_veiculos(veiculos)  # Função para salvar veículos


# Função para registrar um veículo no banco de dados
def registrar_veiculo(dados):
    # Valida se todos os campos foram preenchidos
    if not all(dados):
        messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")
        return

    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()
    try:
        # Insere os dados do veículo na tabela Veiculos
        cursor.execute('''INSERT INTO Veiculos (marca, modelo, categoria, transmissao, tipo, capacidade_pessoas, 
                          valor_diaria, data_ultima_revisao, data_proxima_revisao, data_ultima_inspecao, 
                          data_proxima_inspecao, imagem_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', dados)
        conn.commit()  # Salva as mudanças
        messagebox.showinfo("Sucesso", "Veículo registrado com sucesso!")  # Mensagem de sucesso
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao registrar veículo: {e}")  # Mensagem de erro
    finally:
        fechar_conexao(conn)  # Fecha a conexão com o banco


# Função para listar os veículos registrados no banco de dados
def listar_veiculos():
    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM Veiculos')  # Busca todos os veículos
        veiculos = cursor.fetchall()  # Recupera os dados
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao listar veiculos: {e}")  # Mensagem de erro
        veiculos = []  # Se houver erro, retorna uma lista vazia
    finally:
        fechar_conexao(conn)  # Fecha a conexão com o banco
    return veiculos


def obter_veiculos_para_manutencao():
    conn = conectar()
    cursor = conn.cursor()

    # Definindo um intervalo para considerar a manutenção necessária
    hoje = datetime.now()
    intervalo_dias = 15
    data_limite = hoje + timedelta(days=intervalo_dias)

    # Consulta SQL para buscar veículos que precisam de manutenção
    cursor.execute("""
        SELECT id, modelo, marca, data_proxima_revisao, data_proxima_inspecao 
        FROM Veiculos 
        WHERE data_proxima_revisao <= ? OR data_proxima_inspecao <= ?
    """, (data_limite.strftime('%Y-%m-%d'), data_limite.strftime('%Y-%m-%d')))

    veiculos = cursor.fetchall()
    fechar_conexao(conn)
    return veiculos


def atualizar_listbox_manutencao(listbox):
    listbox.delete(0, tk.END)  # Limpa a Listbox
    veiculos = obter_veiculos_para_manutencao()  # Obtém os veículos para manutenção

    veiculos_notificacao = []  # Lista para armazenar veículos próximos da revisão

    for veiculo in veiculos:
        proxima_revisao = veiculo[3] if veiculo[3] else 'N/A'
        proxima_inspecao = veiculo[4] if veiculo[4] else 'N/A'

        # Adiciona à Listbox
        listbox.insert(tk.END,
                       f"ID: {veiculo[0]}, Modelo: {veiculo[1]}, Marca: {veiculo[2]}, Próxima Revisão: {proxima_revisao}, Próxima Inspeção: {proxima_inspecao}")

        # Verifica veículos com revisão próxima para notificação
        if proxima_revisao != 'N/A' or proxima_inspecao != 'N/A':
            veiculos_notificacao.append(veiculo)

    # Exibe notificação se houver veículos próximos da revisão
    if veiculos_notificacao:
        mensagem = "Os seguintes veículos estão próximos da revisão/inspeção:\n"
        for veiculo in veiculos_notificacao:
            mensagem += f"ID: {veiculo[0]}, Modelo: {veiculo[1]}, Marca: {veiculo[2]}, Próxima Revisão: {veiculo[3]}, Próxima Inspeção: {veiculo[4]}\n"
        messagebox.showinfo("Atenção: Revisões Próximas", mensagem)


def enviar_para_revisao(listbox):
    try:
        indice_selecionado = listbox.curselection()[0]  # Pega o índice do item selecionado
        veiculo = listbox.get(indice_selecionado)  # Obtém os dados do veículo selecionado

        id_veiculo = int(veiculo.split(",")[0].split(":")[1].strip())  # ID: {id}

        conn = conectar()
        cursor = conn.cursor()

        data_atual = datetime.now().strftime('%Y-%m-%d')
        nova_data_revisao = (datetime.now() + timedelta(days=30)).strftime(
            '%Y-%m-%d')  # Define a próxima revisão para 30 dias
        cursor.execute("""
            UPDATE Veiculos
            SET data_ultima_revisao = ?, 
                data_proxima_revisao = ?, 
                data_ultima_inspecao = ?, 
                data_proxima_inspecao = ?, 
                em_manutencao = 1 
            WHERE id = ?
        """, (data_atual, nova_data_revisao, data_atual, nova_data_revisao, id_veiculo))

        conn.commit()  # Salva as alterações no banco de dados
        fechar_conexao(conn)

        atualizar_listbox_manutencao(listbox)

    except IndexError:
        print("Selecione um veículo da lista para enviar para revisão.")


def criar_frame_manutencao(aba_notebook):
    frame_manutencao = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_manutencao, text="Enviar para Manutenção/Revião")

    listbox_manutencao = tk.Listbox(frame_manutencao, width=80, height=15)
    listbox_manutencao.pack(padx=10, pady=10)

    # Botão para enviar veículo para revisão
    tk.Button(frame_manutencao, text="Enviar para Revisão/Revisão",
              command=lambda: enviar_para_revisao(listbox_manutencao)).pack(pady=5)

    # Atualiza a Listbox ao iniciar
    atualizar_listbox_manutencao(listbox_manutencao)


# Função para verificar o status de aluguel de um veículo
def verificar_status_aluguel(veiculo_id):
    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()
    status = "Disponível"  # Status padrão
    try:
        # Verifica se o veículo está em manutenção
        cursor.execute('SELECT em_manutencao FROM Veiculos WHERE id = ?', (veiculo_id,))
        if cursor.fetchone()[0] == 1:
            status = "Em Manutenção"
        else:
            # Verifica se o veículo está alugado
            cursor.execute('SELECT COUNT(*) FROM Alugueis WHERE veiculo_id = ? AND data_fim > ?',
                           (veiculo_id, datetime.now().strftime('%Y-%m-%d')))
            if cursor.fetchone()[0] > 0:
                status = "Alugado"
    except sqlite3.Error as e:
        print(f"Erro ao verificar status do aluguel: {e}")  # Mensagem de erro no console
    finally:
        fechar_conexao(conn)  # Fecha a conexão com o banco

    return status


# Função para alugar um veículo
def alugar_veiculo(veiculo_id, periodo_dias, forma_pagamento_id, listbox_veiculos_alugados):
    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()

    if not str(periodo_dias).isdigit():  # Valida se o período é um número
        messagebox.showerror("Erro", "Informe um período de dias válido.")
        return
    periodo_dias = int(periodo_dias)  # Converte para inteiro

    cursor.execute('SELECT em_manutencao FROM Veiculos WHERE id = ?', (veiculo_id,))
    resultado = cursor.fetchone()
    if resultado is None:
        messagebox.showerror("Erro", "Veículo não encontrado.")
        fechar_conexao(conn)
        return
    if resultado[0] == 1:  # Verifica se o veículo está em manutenção
        messagebox.showerror("Erro", "Este veículo está em manutenção.")
        fechar_conexao(conn)
        return

    cursor.execute('SELECT COUNT(*) FROM Alugueis WHERE veiculo_id = ? AND data_fim > ?',
                   (veiculo_id, datetime.now().strftime('%Y-%m-%d')))
    if cursor.fetchone()[0] > 0:  # Verifica se o veículo já está alugado
        messagebox.showerror("Erro", "Este veículo já está alugado.")
        fechar_conexao(conn)
        return

    # Calcula a data de início e fim do aluguel
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=periodo_dias)
    dias_restantes = data_fim - data_inicio
    try:
        cursor.execute(
            'INSERT INTO Alugueis (veiculo_id, data_inicio, periodo_dias, data_fim, forma_pagamento_id) '
            'VALUES (?, ?, ?, ?, ?)',
            (veiculo_id, data_inicio.strftime('%Y-%m-%d'), periodo_dias, data_fim.strftime('%Y-%m-%d'),
             forma_pagamento_id)
        )
        conn.commit()  # Salva no banco de dados
        messagebox.showinfo("Sucesso", f"Veículo {veiculo_id} alugado por {periodo_dias} dias!")  # Mensagem de sucesso

        # Atualiza a Listbox com os veículos alugados
        atualizar_listbox_veiculos_alugados(listbox_veiculos_alugados)
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao registrar aluguel: {e}")  # Mensagem de erro
    finally:
        fechar_conexao(conn)  # Fecha a conexão com o banco


def obter_id_aluguel_selecionado(listbox):
    """
    Extrai o ID do aluguel selecionado na Listbox.
    """
    selecionado = listbox.curselection()  # Obtém o índice do item selecionado
    if selecionado:
        texto = listbox.get(selecionado[0])  # Obtém o texto do item selecionado
        print(f"Texto selecionado: {texto}")  # Debug
        try:

            partes = texto.split()
            id_aluguel = int(partes[1].replace(":", ""))  # Extrai o ID corretamente
            return id_aluguel
        except (ValueError, IndexError):
            messagebox.showerror("Erro", "Formato inválido no texto da Listbox.")
            return None
    else:
        messagebox.showerror("Erro", "Nenhum aluguel selecionado.")
        return None


# Função para atualizar a Listbox de veículos alugados
def atualizar_listbox_veiculos_alugados(listbox):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, veiculo_id, data_inicio, data_fim FROM Alugueis')
        alugueis = cursor.fetchall()
        listbox.delete(0, tk.END)  # Limpa a Listbox

        for aluguel in alugueis:
            aluguel_id = aluguel[0]
            veiculo_id = aluguel[1]
            data_inicio = aluguel[2]
            data_fim = aluguel[3]

            # Calcula os dias restantes
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
            dias_restantes = (data_fim_obj - datetime.now()).days

            # Define mensagem para exibição
            if dias_restantes < 0:
                status = "Aluguel expirado"
                dias_restantes_str = "Expirado"
            else:
                status = "Alugado"
                dias_restantes_str = f"{dias_restantes} dias restantes"

            # Exibe os dados do aluguel com os dias restantes
            listbox.insert(tk.END,
                           f"Aluguel {aluguel_id}: Veículo {veiculo_id}, Início: {data_inicio}, Fim: {data_fim}, Status: {status}, {dias_restantes_str}")
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao carregar veículos alugados: {e}")
    finally:
        fechar_conexao(conn)


# Função para editar um aluguel existente
def editar_aluguel(aluguel_id, novo_periodo_dias, nova_forma_pagamento_id, listbox_veiculos_alugados):
    conn = conectar()
    cursor = conn.cursor()

    if not str(novo_periodo_dias).isdigit():  # Valida se o novo período é um número
        messagebox.showerror("Erro", "Informe um período de dias válido.")
        return

    novo_periodo_dias = int(novo_periodo_dias)
    try:
        # Busca o aluguel existente
        cursor.execute('SELECT data_inicio FROM Alugueis WHERE id = ?', (aluguel_id,))
        aluguel = cursor.fetchone()
        if aluguel is None:
            messagebox.showerror("Erro", "Aluguel não encontrado.")
            return

        # Calcula a nova data de fim
        data_inicio = datetime.strptime(aluguel[0], '%Y-%m-%d')
        nova_data_fim = data_inicio + timedelta(days=novo_periodo_dias)

        # Atualiza o aluguel no banco de dados
        cursor.execute('''
            UPDATE Alugueis
            SET periodo_dias = ?, data_fim = ?, forma_pagamento_id = ?
            WHERE id = ?
        ''', (novo_periodo_dias, nova_data_fim.strftime('%Y-%m-%d'), nova_forma_pagamento_id, aluguel_id))
        conn.commit()
        messagebox.showinfo("Sucesso", "Aluguel atualizado com sucesso!")

        # Atualiza a Listbox com os veículos alugados
        atualizar_listbox_veiculos_alugados(listbox_veiculos_alugados)
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao atualizar aluguel: {e}")
    finally:
        fechar_conexao(conn)


def abrir_janela_edicao_aluguel(listbox_veiculos_alugados):
    aluguel_id = obter_id_aluguel_selecionado(listbox_veiculos_alugados)
    if aluguel_id is None:
        return  # Retorna se nenhum aluguel estiver selecionado

    # Cria uma nova janela de edição
    janela_edicao = tk.Toplevel()
    janela_edicao.title("Editar Aluguel")

    # Obtém informações do aluguel selecionado do banco de dados
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT periodo_dias, forma_pagamento_id FROM Alugueis WHERE id = ?', (aluguel_id,))
    aluguel = cursor.fetchone()
    fechar_conexao(conn)

    if aluguel is None:
        messagebox.showerror("Erro", "Aluguel não encontrado.")  # Exibe erro se o aluguel não for encontrado
        return

    periodo_dias_atual, forma_pagamento_atual = aluguel  # Desempacota os dados do aluguel

    # Cria labels e entradas para os novos dados
    tk.Label(janela_edicao, text="Novo Período (dias):").grid(row=0, column=0)
    novo_periodo_entry = tk.Entry(janela_edicao)
    novo_periodo_entry.grid(row=0, column=1)
    novo_periodo_entry.insert(0, str(periodo_dias_atual))  # Preenche com o período atual

    tk.Label(janela_edicao, text="Nova Forma de Pagamento:").grid(row=2, column=0)

    # Cria a Combobox para as formas de pagamento disponíveis
    formas_pagamento = ['Cartão de Crédito', 'Cartão de Débito', 'Dinheiro', 'Transferência Bancária']
    nova_forma_pagamento_combobox = ttk.Combobox(janela_edicao, values=formas_pagamento)
    nova_forma_pagamento_combobox.grid(row=2, column=1)
    nova_forma_pagamento_combobox.set(formas_pagamento[forma_pagamento_atual])  # Define a forma de pagamento atual

    # Função para aplicar as alterações feitas
    def aplicar_edicoes():
        novo_periodo_dias = novo_periodo_entry.get()  # Obtém o novo período de dias
        nova_forma_pagamento = nova_forma_pagamento_combobox.current()  # Obtém o índice da forma de pagamento selecionada

        # Chama a função de edição do aluguel
        editar_aluguel(aluguel_id, novo_periodo_dias, nova_forma_pagamento, listbox_veiculos_alugados)
        janela_edicao.destroy()  # Fecha a janela após aplicar as edições

    # Botão para salvar as edições
    tk.Button(janela_edicao, text="Salvar", command=aplicar_edicoes).grid(row=3, columnspan=2)

    # Inicia o loop principal da nova janela
    janela_edicao.mainloop()


# Função para cancelar um aluguel existente
def cancelar_aluguel(aluguel_id, listbox_veiculos_alugados):
    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()
    try:
        # Verifica se o aluguel existe no banco de dados
        cursor.execute('SELECT COUNT(*) FROM Alugueis WHERE id = ?', (aluguel_id,))
        if cursor.fetchone()[0] == 0:
            messagebox.showerror("Erro", "Aluguel não encontrado.")  # Exibe erro se o aluguel não for encontrado
            return

        # Remove o aluguel do banco de dados
        cursor.execute('DELETE FROM Alugueis WHERE id = ?', (aluguel_id,))
        conn.commit()  # Confirma a exclusão no banco de dados
        messagebox.showinfo("Sucesso", "Aluguel cancelado com sucesso!")  # Mensagem de sucesso

        # Atualiza a Listbox com os veículos alugados
        atualizar_listbox_veiculos_alugados(listbox_veiculos_alugados)
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao cancelar aluguel: {e}")  # Mensagem de erro em caso de falha
    finally:
        fechar_conexao(conn)  # Fecha a conexão com o banco


# Função para editar as informações de um veículo
def editar_veiculo(veiculo_id, dados):
    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()
    try:
        # Atualiza os dados do veículo no banco de dados
        cursor.execute('''UPDATE Veiculos
                          SET marca = ?, modelo = ?, categoria = ?, transmissao = ?, tipo = ?, capacidade_pessoas = ?,
                              valor_diaria = ?, data_ultima_revisao = ?, data_proxima_revisao = ?, data_ultima_inspecao = ?, 
                              data_proxima_inspecao = ?, imagem_path = ?
                          WHERE id = ?''', (*dados, veiculo_id))
        conn.commit()  # Salva as alterações no banco de dados
        messagebox.showinfo("Sucesso", "Veículo atualizado com sucesso!")  # Mensagem de sucesso
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao atualizar veículo: {e}")  # Mensagem de erro em caso de falha
    finally:
        fechar_conexao(conn)  # Fecha a conexão com o banco


# Função para excluir um veículo do banco de dados
def excluir_veiculo(veiculo_id):
    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()

    try:
        # Exclui o veículo do banco de dados
        cursor.execute('DELETE FROM Veiculos WHERE id = ?', (veiculo_id,))
        conn.commit()  # Salva a exclusão no banco de dados
        messagebox.showinfo("Sucesso", "Veículo excluído com sucesso!")  # Mensagem de sucesso
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao excluir veículo: {e}")  # Mensagem de erro em caso de falha
    finally:
        fechar_conexao(conn)  # Fecha a conexão com o banco


# Função para contar os veículos de acordo com um grupo específico (por exemplo, categoria)
def contar_veiculos(grupo):
    conn = conectar()  # Conecta ao banco de dados
    cursor = conn.cursor()
    cursor.execute(f'SELECT {grupo}, COUNT(*) FROM Veiculos GROUP BY {grupo}')  # Conta veículos por grupo
    resultado = cursor.fetchall()  # Recupera o resultado da contagem
    fechar_conexao(conn)  # Fecha a conexão com o banco
    return resultado  # Retorna o resultado da contagem
# Função para exibir os veículos em uma interface gráfica
def exibir_veiculos(frame_veiculos, btn_atualizar):
    # Limpa o conteúdo anterior (exceto o botão de atualização)
    for widget in frame_veiculos.winfo_children():
        if widget != btn_atualizar:  # Preserva o botão de atualização
            widget.destroy()

    # Criando o canvas e a scrollbar para rolagem
    canvas = tk.Canvas(frame_veiculos)
    scrollbar = ttk.Scrollbar(frame_veiculos, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    # Frame que será colocado dentro do canvas para organizar os veículos
    frame_grid = ttk.Frame(canvas)

    # Adicionar a scrollbar ao canvas
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", expand=True, fill="both")
    canvas.create_window((0, 0), window=frame_grid, anchor="nw")

    # Conectando ao banco de dados para buscar veículos
    conn = sqlite3.connect('/home/bobina/Downloads/ProjetoFinal (2)/ProjetoFinal/database/informacoes.db')
    cursor = conn.cursor()

    # Buscando todos os veículos do banco de dados
    cursor.execute("SELECT id, modelo, imagem_path FROM Veiculos")
    veiculos = cursor.fetchall()

    # Layout em grid para os veículos, organizando-os em linhas e colunas
    for i, veiculo in enumerate(veiculos):
        linha = i // 3  # 3 veículos por linha
        coluna = i % 3

        veiculo_id = veiculo[0]  # ID do veículo
        modelo = veiculo[1]
        imagem_path = veiculo[2]

        # Chamando a função para verificar o status de aluguel do veículo
        status_aluguel = verificar_status_aluguel(veiculo_id)

        # Criando um frame para cada veículo
        frame_carro = ttk.Frame(frame_grid)
        frame_carro.grid(row=linha, column=coluna, padx=10, pady=10)

        # Exibindo o modelo do veículo em um label
        tk.Label(frame_carro, text=modelo, font=("Arial", 10, "bold")).pack(pady=5)

        # Carregando e exibindo a imagem do veículo
        try:
            imagem = Image.open(imagem_path)  # Abre a imagem do veículo
            imagem = imagem.resize((150, 150), Image.Resampling.LANCZOS)  # Redimensiona a imagem
            imagem_tk = ImageTk.PhotoImage(imagem)  # Converte a imagem para formato Tkinter
            label_imagem = tk.Label(frame_carro, image=imagem_tk)
            label_imagem.image = imagem_tk  # Mantém a referência da imagem para evitar coleta de lixo
            label_imagem.pack(padx=10, pady=5)
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")  # Exibe erro ao carregar a imagem

        # Exibindo o status do veículo
        status_label = f"Status: {status_aluguel}"
        tk.Label(frame_carro, text=status_label, font=("Arial", 8)).pack(pady=5)

    # Atualiza a área do canvas para acomodar os novos widgets
    frame_grid.update_idletasks()

    # Atualiza a região visível do canvas para incluir todos os veículos
    canvas.config(scrollregion=canvas.bbox("all"))

    # Fecha a conexão com o banco de dados após a exibição
    conn.close()


# Função para atualizar a listbox com a lista de veículos
def atualizar_listbox_veiculos(listbox, label_imagem, botoes_frame):
    listbox.delete(0, tk.END)  # Limpa a listbox antes de atualizar

    veiculos = listar_veiculos()  # Obtém a lista de veículos do banco de dados

    # Limpa o frame onde ficam os botões de ação
    for widget in botoes_frame.winfo_children():
        widget.destroy()

    # Insere os veículos na listbox, formatando as informações
    for veiculo in veiculos:
        listbox.insert(tk.END, f"ID: {veiculo[0]}, Modelo: {veiculo[2]}, Marca: {veiculo[1]}, Categoria: {veiculo[3]}")

    # Criação dos botões de ação para editar e excluir veículos
    botao_editar = tk.Button(botoes_frame, text="Editar Veículo")
    botao_excluir = tk.Button(botoes_frame, text="Excluir Veículo")

    # Posiciona os botões no frame
    botao_editar.pack(pady=5)
    botao_excluir.pack(pady=5)


    def on_select(event):
        selecionado = listbox.curselection()  # Obtém o item selecionado na listbox
        if selecionado:
            index = selecionado[0]
            veiculo_id = veiculos[index][0]  # Obtém o ID do veículo selecionado
            imagem_path = veiculos[index][12]  # Obtém o caminho da imagem do veículo

            # Exibe a imagem do veículo, se disponível
            if imagem_path:
                exibir_imagem_veiculo(imagem_path, label_imagem)
            else:
                label_imagem.config(text="Imagem não disponível", image=None)

            # Atualiza os comandos dos botões de acordo com o veículo selecionado
            botao_editar.config(command=lambda: abrir_janela_edicao(veiculo_id))
            botao_excluir.config(command=lambda: excluir_veiculo(veiculo_id))

    listbox.bind("<<ListboxSelect>>", on_select)  # Associa a seleção na listbox à função on_select


# Função para abrir a janela de edição de um veículo
def abrir_janela_edicao(veiculo_id):
    veiculo = next((v for v in listar_veiculos() if v[0] == veiculo_id), None)  # Busca o veículo pelo ID
    if not veiculo:
        messagebox.showerror("Erro", "Veículo não encontrado.")  # Caso não encontre o veículo
        return

    # Cria uma nova janela para edição
    janela_edicao = tk.Toplevel()
    janela_edicao.title("Editar Veículo")
    janela_edicao.geometry("400x600")  # Ajusta o tamanho da janela para acomodar a imagem

    # Lista de campos para editar o veículo
    labels = ["Marca", "Modelo", "Categoria", "Transmissão", "Tipo", "Capacidade (Pessoas)",
              "Valor Diária", "Última Revisão", "Próxima Revisão", "Última Inspeção", "Próxima Inspeção", "Imagem"]
    entries = []  # Lista para armazenar os campos de entrada (Entry)

    # Cria os campos de entrada para edição
    for i, label_text in enumerate(labels):
        tk.Label(janela_edicao, text=label_text).grid(row=i, column=0, padx=10, pady=5)
        entry = tk.Entry(janela_edicao, width=30)
        entry.insert(0, veiculo[i + 1])  # Pré-preenche os campos com os dados do veículo
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries.append(entry)

    # Adiciona o campo para a imagem (inicializa vazio ou com a imagem atual)
    label_imagem = tk.Label(janela_edicao, text="Nenhuma imagem selecionada")
    label_imagem.grid(row=12, column=0, columnspan=2, pady=10)

    # Botão para selecionar uma nova imagem para o veículo
    tk.Button(janela_edicao, text="Selecionar Imagem",
              command=lambda: selecionar_imagem(entries[-1], label_imagem)).grid(row=13, column=0, columnspan=2,
                                                                                 pady=10)

    # Botão para salvar as alterações no veículo
    tk.Button(janela_edicao, text="Salvar Alterações",
              command=lambda: editar_veiculo(veiculo_id, [entry.get() for entry in entries])).grid(row=13, column=0,
                                                                                                   pady=20)

    # Função para selecionar uma nova imagem para o veículo


def selecionar_imagem(entry_imagem, label_imagem):
    # Abre o diálogo para selecionar uma imagem
    file_path = filedialog.askopenfilename(
        title="Selecione uma Imagem",
        filetypes=[("Imagens PNG", "*.png"), ("Imagens JPEG", ".jpeg"), ("Imagens JPG", "*.jpg"), ("Todos os arquivos", "*.*")]
    )
    if file_path:
        try:
            # Atualiza o campo de entrada (Entry) com o caminho da imagem selecionada
            entry_imagem.delete(0, tk.END),
            entry_imagem.insert(0, file_path)

            # Abre e redimensiona a imagem para exibição
            imagem = Image.open(file_path)
            imagem.thumbnail((200, 200))  # Redimensiona para no máximo 200x200 pixels
            img_tk = ImageTk.PhotoImage(imagem)

            # Atualiza o label com a imagem
            label_imagem.config(image=img_tk, text="")  # Limpa o texto, se houver
            label_imagem.image = img_tk  # Mantém a referência da imagem

        except Exception as e:
            print(f"Erro ao abrir a imagem: {e}")
            label_imagem.config(text="Erro ao carregar imagem", image=None)


# Função para exibir a imagem de um veículo
def exibir_imagem_veiculo(file_path, label):
    # Verifica se o caminho do arquivo é válido
    if file_path and os.path.isfile(file_path):
        try:
            # Carrega e redimensiona a imagem
            imagem = Image.open(file_path)
            imagem = imagem.resize((200, 15), Image.LANCZOS)  # Redimensiona para exibição
            imagem_tk = ImageTk.PhotoImage(imagem)

            # Atualiza o label para exibir a imagem
            label.config(image=imagem_tk, text="")  # Limpa o texto, se houver
            label.image = imagem_tk  # Mantém a referência da imagem
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")
            label.config(text="Erro ao carregar imagem", image=None)
    else:
        label.config(text="Imagem não disponível", image=None)  # Caso a imagem não esteja disponível


# Gestão de clientes
# Lista os clientes e os mostra na apluicação tkinter
def listar_clientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, email FROM Clientes')
    clientes = cursor.fetchall()
    fechar_conexao(conn)
    return clientes


def registrar_cliente(nome, email, password):
    conn = conectar()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute('INSERT INTO Clientes (nome, email, password) VALUES (?, ?, ?)',
                       (nome, email, hashed_password))
        conn.commit()
        messagebox.showinfo("Sucesso", "Cliente registrado com sucesso!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "O e-mail já está registrado.")
    finally:
        fechar_conexao(conn)


# Funções de Interface Gráfica
def atualizar_listbox_clientes(listbox):
    listbox.delete(0, tk.END)
    for cliente in listar_clientes():
        listbox.insert(tk.END, f"ID: {cliente[0]}, Nome: {cliente[1]}, E-mail: {cliente[2]}")


def abrir_editar_cliente(cliente_id, listbox):
    def salvar_edicao():
        novo_nome = nome_entry.get()
        novo_email = email_entry.get()
        editar_cliente(cliente_id, novo_nome, novo_email)
        atualizar_listbox_clientes(listbox)
        janela_editar.destroy()

    # Janela para editar cliente
    janela_editar = tk.Toplevel()
    janela_editar.title("Editar Cliente")

    tk.Label(janela_editar, text="Novo Nome:").grid(row=0, column=0, padx=10, pady=5)
    nome_entry = tk.Entry(janela_editar)
    nome_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(janela_editar, text="Novo E-mail:").grid(row=1, column=0, padx=10, pady=5)
    email_entry = tk.Entry(janela_editar)
    email_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Button(janela_editar, text="Salvar", command=salvar_edicao).grid(
        row=2, column=0, columnspan=2, pady=10
    )


def excluir_cliente_selecionado(listbox):
    try:
        selecionado = listbox.get(listbox.curselection())
        cliente_id = int(selecionado.split(",")[0].split(":")[1].strip())
        excluir_cliente(cliente_id)
        atualizar_listbox_clientes(listbox)
    except tk.TclError:
        messagebox.showerror("Erro", "Selecione um cliente para excluir.")


def editar_cliente(cliente_id, novo_nome, novo_email):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE Clientes SET nome = ?, email = ? WHERE id = ?',
            (novo_nome, novo_email, cliente_id)
        )
        conn.commit()
        messagebox.showinfo("Sucesso", "Cliente atualizado com sucesso!")
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao atualizar cliente: {e}")
    finally:
        fechar_conexao(conn)


def abrir_janela_editar_cliente(listbox):
    try:
        # Obter o cliente selecionado no Listbox
        selecionado = listbox.get(listbox.curselection())
        cliente_id = int(selecionado.split(",")[0].split(":")[1].strip())
        cliente_nome = selecionado.split(",")[1].split(":")[1].strip()
        cliente_email = selecionado.split(",")[2].split(":")[1].strip()

        # Função para salvar as alterações
        def salvar_alteracoes():
            novo_nome = entrada_nome.get()
            novo_email = entrada_email.get()
            if not novo_nome or not novo_email:
                messagebox.showerror("Erro", "Todos os campos são obrigatórios.")
                return
            editar_cliente(cliente_id, novo_nome, novo_email)
            atualizar_listbox_clientes(listbox)
            janela_editar.destroy()

        # Criar a janela de edição
        janela_editar = tk.Toplevel()
        janela_editar.title("Editar Cliente")
        janela_editar.geometry("300x200")

        # Campos de edição
        tk.Label(janela_editar, text="Nome:").pack(pady=5)
        entrada_nome = tk.Entry(janela_editar)
        entrada_nome.insert(0, cliente_nome)
        entrada_nome.pack(pady=5)

        tk.Label(janela_editar, text="E-mail:").pack(pady=5)
        entrada_email = tk.Entry(janela_editar)
        entrada_email.insert(0, cliente_email)
        entrada_email.pack(pady=5)

        # Botão para salvar alterações
        tk.Button(janela_editar, text="Salvar", command=salvar_alteracoes).pack(pady=10)

    except tk.TclError:
        messagebox.showerror("Erro", "Selecione um cliente para editar.")


def excluir_cliente(cliente_id):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Clientes WHERE id = ?', (cliente_id,))
        conn.commit()
        messagebox.showinfo("Sucesso", "Cliente excluído com sucesso!")
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao excluir cliente: {e}")
    finally:
        fechar_conexao(conn)


# Função para calcular o total financeiro do mês
def calcular_total_financeiro_mes():
    conn = conectar()
    cursor = conn.cursor()
    primeiro_dia_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    ultimo_dia_mes = datetime.now().replace(
        day=calendar.monthrange(datetime.now().year, datetime.now().month)[1]).strftime('%Y-%m-%d')

    cursor.execute('''SELECT A.periodo_dias, V.valor_diaria
                      FROM Alugueis A
                      JOIN Veiculos V ON A.veiculo_id = V.id
                      WHERE A.data_inicio BETWEEN ? AND ?''', (primeiro_dia_mes, ultimo_dia_mes))

    alugueis_mes = cursor.fetchall()
    total_financeiro = sum(periodo * valor_diaria for periodo, valor_diaria in alugueis_mes)
    fechar_conexao(conn)
    return total_financeiro


# Função para contar o total de reservas do mês
def contar_reservas_mes():
    conn = conectar()
    cursor = conn.cursor()
    primeiro_dia_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    ultimo_dia_mes = datetime.now().replace(
        day=calendar.monthrange(datetime.now().year, datetime.now().month)[1]).strftime('%Y-%m-%d')

    cursor.execute('SELECT COUNT(*) FROM Alugueis WHERE data_inicio BETWEEN ? AND ?',
                   (primeiro_dia_mes, ultimo_dia_mes))
    total_reservas = cursor.fetchone()[0]
    fechar_conexao(conn)
    return total_reservas


# Função para exibir o relatório financeiro
def mostrar_relatorio_financeiro():
    try:
        total_financeiro = calcular_total_financeiro_mes()  # Total financeiro do mês
        total_reservas = contar_reservas_mes()  # Total de reservas do mês

        # Monta a mensagem para exibir
        mensagem = (
            f"Relatório Financeiro do Mês\n\n"
            f"🔸 Total de Renda: R$ {total_financeiro:.2f}\n"
            f"🔸 Total de Reservas: {total_reservas} reserva(s)"
        )

        # Exibe a mensagem em uma MessageBox
        messagebox.showinfo("Relatório Financeiro do Mês", mensagem)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")


def exibir_dashboard():
    """
    Exibe um dashboard com gráficos de barras para a quantidade de veículos
    agrupados por tipo e categoria, exibindo apenas números inteiros nos eixos.
    """
    # Obtemos os dados de veículos por tipo e por categoria
    dados_por_tipo = contar_veiculos('tipo')
    dados_por_categoria = contar_veiculos('categoria')


    fig, eixos = plt.subplots(1, 2, figsize=(12, 6))  # Dois gráficos lado a lado

    # Gráfico 1: Veículos por Tipo
    tipos, quantidades_tipos = zip(*dados_por_tipo)  # Separa os dados em categorias e valores
    eixos[0].bar(tipos, quantidades_tipos, color='skyblue')
    eixos[0].set_title('Quantidade de Veículos por Tipo')
    eixos[0].set_xlabel('Tipo')
    eixos[0].set_ylabel('Quantidade')
    eixos[0].set_yticks(range(0, max(quantidades_tipos) + 1))  # Apenas inteiros

    # Gráfico 2: Veículos por Categoria
    categorias, quantidades_categorias = zip(*dados_por_categoria)  # Separa os dados
    eixos[1].bar(categorias, quantidades_categorias, color='lightgreen')
    eixos[1].set_title('Quantidade de Veículos por Categoria')
    eixos[1].set_xlabel('Categoria')
    eixos[1].set_ylabel('Quantidade')
    eixos[1].set_yticks(range(0, max(quantidades_categorias) + 1))  # Apenas inteiros

    # Ajuste do layout para evitar sobreposição
    plt.tight_layout()

    # Exibindo o dashboard
    plt.show()


def iniciar_janela_principal():
    janela = tk.Tk()
    janela.title("Locadora de Veículos")
    janela.geometry("900x700")

    aba_notebook = ttk.Notebook(janela)
    aba_notebook.pack(expand=True, fill='both')

    # Frame de Registro de Veículos
    frame_registro = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_registro, text="Registro de Veículo")

    labels = ["Marca", "Modelo", "Categoria", "Transmissão", "Tipo", "Capacidade (Pessoas)",
              "Valor Diária", "Última Revisão", "Próxima Revisão", "Última Inspeção", "Próxima Inspeção", "Imagem"]
    entries = []
    for i, label_text in enumerate(labels):
        tk.Label(frame_registro, text=label_text).grid(row=i, column=0, padx=10, pady=5)
        entry = tk.Entry(frame_registro, width=30)
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries.append(entry)

    tk.Button(frame_registro, text="Selecionar Imagem",
              command=lambda: selecionar_imagem(entries[-1], label_imagem)).grid(row=11, column=2, padx=10, pady=5)
    tk.Button(frame_registro, text="Registrar Veículo",
              command=lambda: registrar_veiculo([entry.get() for entry in entries])).grid(row=12, column=1, pady=20)

    # Frame de Listagem de Veículos
    frame_listagem = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_listagem, text="Listagem de Veículos")
    label_imagem = tk.Label(frame_listagem)
    label_imagem.grid(row=0, column=1, rowspan=5, padx=10, pady=5)
    listbox_veiculos = tk.Listbox(frame_listagem, width=60, height=13)
    listbox_veiculos.grid(row=0, column=0, padx=10, pady=5)

    # Frame para os botões de ação
    botoes_frame = tk.Frame(frame_listagem)
    botoes_frame.grid(row=2, column=1, padx=10, pady=10)

    tk.Button(frame_listagem, text="Atualizar Listagem",
              command=lambda: atualizar_listbox_veiculos(listbox_veiculos, label_imagem, botoes_frame)).grid(row=1,
                                                                                                             column=0,
                                                                                                             pady=5)

    # Frame de Clientes
    frame_clientes = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_clientes, text="Clientes")

    tk.Label(frame_clientes, text="Nome").grid(row=0, column=0, padx=10, pady=5)
    tk.Label(frame_clientes, text="Email").grid(row=1, column=0, padx=10, pady=5)
    entry_nome_cliente = tk.Entry(frame_clientes, width=30)
    entry_email_cliente = tk.Entry(frame_clientes, width=30)
    entry_nome_cliente.grid(row=0, column=1, padx=10, pady=5)
    entry_email_cliente.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(frame_clientes, text="Senha").grid(row=2, column=0, padx=10, pady=5)
    entry_password_cliente = tk.Entry(frame_clientes, show="*", width=30)
    entry_password_cliente.grid(row=2, column=1, padx=10, pady=5)

    tk.Button(frame_clientes, text="Registrar Cliente",
              command=lambda: registrar_cliente(entry_nome_cliente.get(), entry_email_cliente.get(),
                                                entry_password_cliente.get())).grid(row=3, column=1, pady=5)
    listbox_clientes = tk.Listbox(frame_clientes, width=60, height=10)

    listbox_clientes.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
    tk.Button(frame_clientes, text="Atualizar Listagem",
              command=lambda: atualizar_listbox_clientes(listbox_clientes)).grid(row=5, column=1, pady=5)

    frame_veiculos = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_veiculos, text="Veículos")
    btn_atualizar = tk.Button(frame_veiculos, text="Atualizar Lista",
                              command=lambda: exibir_veiculos(frame_veiculos, btn_atualizar))
    btn_atualizar.pack(pady=10)

    # Botão para editar cliente
    tk.Button(frame_clientes, text="Editar Cliente",
              command=lambda: abrir_janela_editar_cliente(listbox_clientes)).grid(row=6, column=1, pady=5)

    # Botão para excluir cliente
    tk.Button(frame_clientes, text="Excluir Cliente",
              command=lambda: excluir_cliente_selecionado(listbox_clientes)).grid(row=7, column=1, pady=5)

    # Frame para aluguel de veiculos
    frame_aluguel = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_aluguel, text="Alugar Veículo")

    tk.Label(frame_aluguel, text="ID do Veículo").grid(row=0, column=0, padx=10, pady=5)
    tk.Label(frame_aluguel, text="Período (dias)").grid(row=1, column=0, padx=10, pady=5)

    entry_id_veiculo = tk.Entry(frame_aluguel, width=30)
    entry_periodo = tk.Entry(frame_aluguel, width=30)
    entry_id_veiculo.grid(row=0, column=1, padx=10, pady=5)
    entry_periodo.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(frame_aluguel, text="Forma de Pagamento").grid(row=2, column=0, padx=10, pady=5)
    combo_pagamento = ttk.Combobox(frame_aluguel, values=["Cartão de Crédito", "Dinheiro", "Transferência Bancária"])
    combo_pagamento.grid(row=2, column=1, padx=10, pady=5)

    # Listbox para exibir veículos alugados
    listbox_veiculos_alugados = tk.Listbox(frame_aluguel, width=80, height=10)
    listbox_veiculos_alugados.grid(row=4, column=0, columnspan=2, pady=10)

    # Botão para alugar veículo
    tk.Button(frame_aluguel, text="Alugar Veículo",
              command=lambda: alugar_veiculo(
                  entry_id_veiculo.get(),
                  int(entry_periodo.get()) if entry_periodo.get().isdigit() else 0,
                  combo_pagamento.current(),
                  listbox_veiculos_alugados
              )
              ).grid(row=3, column=1, pady=10)

    # Botão para editar um aluguel
    tk.Button(frame_aluguel, text="Editar Aluguel",
              command=lambda: abrir_janela_edicao_aluguel(listbox_veiculos_alugados)).grid(row=5, column=0, pady=10)

    # Botão para cancelar um aluguel
    tk.Button(frame_aluguel, text="Cancelar Aluguel",
              command=lambda: cancelar_aluguel(
                  obter_id_aluguel_selecionado(listbox_veiculos_alugados),
                  listbox_veiculos_alugados
              )
              ).grid(row=5, column=1, pady=10)

    # Atualiza a Listbox ao iniciar
    atualizar_listbox_veiculos_alugados(listbox_veiculos_alugados)

    # Chame a função para criar o novo Frame de Manutenção
    criar_frame_manutencao(aba_notebook)

    # Frame de Relatórios
    frame_relatorio = ttk.Frame(aba_notebook)
    # Frame de Relatórios
    frame_relatorio = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_relatorio, text="Relatório Financeiro")

    # Botão que exibe o relatório financeiro
    tk.Button(frame_relatorio, text="Exibir Relatório do Mês", command=mostrar_relatorio_financeiro).pack(pady=20)

    aba_notebook.add(frame_relatorio)

    frame_dashboard = ttk.Frame(aba_notebook)
    aba_notebook.add(frame_dashboard, text="Dashboard")

    # Botão para visualizar o dashboard
    tk.Button(frame_dashboard, text="Visualizar Dashboard", command=exibir_dashboard).pack(pady=20)
    tk.Button(frame_dashboard, text="Exportar Aluguéis", command=exportar_alugueis).pack(pady=20)
    tk.Button(frame_dashboard, text="Exportar Clientes", command=exportar_clientes).pack(pady=20)
    tk.Button(frame_dashboard, text="Exportar Veículos", command=exportar_veiculos).pack(pady=20)

    janela.mainloop()


# As datas nos arquivos csv precisa apenas de um ajuste nas respectivas colunas
# Exportando os alugueis
def exportar_alugueis():
    # Abre uma janela para salvar o arquivo CSV
    arquivo_salvar = filedialog.asksaveasfilename(
        title="Salvar Tabela Alugueis",
        defaultextension=".csv",
        filetypes=[("Arquivos CSV", "*.csv")],
        initialfile="alugueis_exportados.csv"
    )
    if not arquivo_salvar:
        messagebox.showinfo("Cancelado", "A exportação foi cancelada.")
        return

    # Conectar ao banco de dados
    db_path = 'C:/Users/rhuan/PycharmProjects/ProjetoFinal/database/informacoes.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Consultar todos os dados da tabela Alugueis
        query = "SELECT * FROM Alugueis;"
        cursor.execute(query)
        dados = cursor.fetchall()

        # Obter os nomes das colunas
        colunas = [descricao[0] for descricao in cursor.description]

        # Escrever os dados em um arquivo CSV
        with open(arquivo_salvar, mode='w', newline='', encoding='ISO-8859-1') as file:
            writer = csv.writer(file)
            writer.writerow(colunas)  # Escrever cabeçalho
            writer.writerows(dados)  # Escrever dados

        messagebox.showinfo("Exportação Concluída", f"Os dados foram exportados para:\n{arquivo_salvar}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao exportar: {str(e)}")
    finally:
        conn.close()


def exportar_clientes():
    # Abre uma janela para salvar o arquivo CSV
    arquivo_salvar = filedialog.asksaveasfilename(
        title="Salvar Tabela Clientes",
        defaultextension=".csv",
        filetypes=[("Arquivos CSV", "*.csv")],
        initialfile="clientes_exportados.csv"
    )
    if not arquivo_salvar:
        messagebox.showinfo("Cancelado", "A exportação foi cancelada.")
        return

    # Conectar ao banco de dados
    db_path = 'C:/Users/rhuan/PycharmProjects/ProjetoFinal/database/informacoes.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Consultar todos os dados da tabela Clientes
        query = "SELECT * FROM Clientes;"
        cursor.execute(query)
        dados = cursor.fetchall()

        # Obter os nomes das colunas
        colunas = [descricao[0] for descricao in cursor.description]

        # Escrever os dados em um arquivo CSV
        with open(arquivo_salvar, mode='w', newline='', encoding='ISO-8859-1') as file:
            writer = csv.writer(file)
            writer.writerow(colunas)  # Escrever cabeçalho
            writer.writerows(dados)  # Escrever dados

        messagebox.showinfo("Exportação Concluída", f"Os dados foram exportados para:\n{arquivo_salvar}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao exportar: {str(e)}")
    finally:
        conn.close()


def exportar_veiculos():
    # Abre uma janela para salvar o arquivo CSV
    arquivo_salvar = filedialog.asksaveasfilename(
        title="Salvar Tabela Veículos",
        defaultextension=".csv",
        filetypes=[("Arquivos CSV", "*.csv")],
        initialfile="veiculos_exportados.csv"
    )
    if not arquivo_salvar:
        messagebox.showinfo("Cancelado", "A exportação foi cancelada.")
        return

    # Conectar ao banco de dados
    db_path = 'C:/Users/rhuan/PycharmProjects/ProjetoFinal/database/informacoes.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Consultar todos os dados da tabela Veiculos
        query = "SELECT * FROM Veiculos;"
        cursor.execute(query)
        dados = cursor.fetchall()

        # Obter os nomes das colunas
        colunas = [descricao[0] for descricao in cursor.description]

        # Escrever os dados em um arquivo CSV
        with open(arquivo_salvar, mode='w', newline='', encoding='ISO-8859-1') as file:
            writer = csv.writer(file)
            writer.writerow(colunas)  # Escrever cabeçalho
            writer.writerows(dados)  # Escrever dados

        messagebox.showinfo("Exportação Concluída", f"Os dados foram exportados para:\n{arquivo_salvar}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao exportar: {str(e)}")
    finally:
        conn.close()


# Inicia a aplicação
iniciar_janela_principal()