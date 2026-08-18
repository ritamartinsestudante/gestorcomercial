import sqlite3
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox, ttk
from PIL import Image
import os

# Configurações de fonte e visual
FONTE_PADRAO = ("Arial", 14)
FONTE_TITULO = ("Arial", 18, "bold")
FONTE_BOTAO = ("Arial", 14, "bold")

ARQUIVO_LOGO = "logo.png"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- BANCO DE DADOS ---
class Database:
    def __init__(self, db_name="gestor_comercial.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.criar_tabelas()

    def criar_tabelas(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                nome TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_custo REAL NOT NULL,
                preco_venda REAL NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                produto_id INTEGER,
                quantidade_vendida INTEGER,
                preco_custo_total REAL,
                preco_venda_total REAL,
                lucro REAL,
                data TEXT,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                categoria TEXT,
                descricao TEXT,
                valor REAL,
                data TEXT,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)
        self.conn.commit()

    def registrar_usuario(self, username, senha):
        try:
            self.cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (username, senha))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verificar_login(self, username, senha):
        self.cursor.execute("SELECT id FROM usuarios WHERE username = ? AND senha = ?", (username, senha))
        return self.cursor.fetchone()

db = Database()

# --- APLICAÇÃO PRINCIPAL ---
class GestorComercialApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gestor Comercial - Pequenos Comércios")
        self.geometry("1100x780")
        self.usuario_atual = None
        self.usuario_id = None

        self.imagem_logo_login = None
        self.imagem_logo_topo = None
        if os.path.exists(ARQUIVO_LOGO):
            img_pil = Image.open(ARQUIVO_LOGO)
            self.imagem_logo_login = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(160, 90))
            self.imagem_logo_topo = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(120, 60))

        self.tela_login()

    def limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

    # Função auxiliar para preencher linhas vazias até embaixo na tabela
    def preencher_linhas_vazias(self, tree, num_linhas_desejadas=14):
        itens_atuais = len(tree.get_children())
        faltam = num_linhas_desejadas - itens_atuais
        for _ in range(max(0, faltam)):
            tree.insert("", "end", values=("", "", "", "", "", "", ""))

    # ================= TELA DE LOGIN =================
    def tela_login(self):
        self.limpar_tela()

        frame = ctk.CTkFrame(self, width=450, height=580, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        if self.imagem_logo_login:
            lbl_logo_img = ctk.CTkLabel(frame, image=self.imagem_logo_login, text="")
            lbl_logo_img.pack(pady=(20, 5))

        lbl_logo = ctk.CTkLabel(frame, text="🛒 GESTOR COMERCIAL", font=FONTE_TITULO)
        lbl_logo.pack(pady=10)

        self.entry_user = ctk.CTkEntry(frame, placeholder_text="Usuário", font=FONTE_PADRAO, width=320, height=45)
        self.entry_user.pack(pady=10)

        self.entry_senha = ctk.CTkEntry(frame, placeholder_text="Senha", show="*", font=FONTE_PADRAO, width=320, height=45)
        self.entry_senha.pack(pady=10)

        btn_entrar = ctk.CTkButton(frame, text="Entrar", font=FONTE_BOTAO, fg_color="#2ecc71", hover_color="#27ae60", width=320, height=45, command=self.fazer_login)
        btn_entrar.pack(pady=15)

        btn_cadastrar = ctk.CTkButton(frame, text="Criar Nova Conta (Multi-usuário)", font=FONTE_BOTAO, fg_color="#3498db", hover_color="#2980b9", width=320, height=45, command=self.cadastrar_usuario)
        btn_cadastrar.pack(pady=5)

    def fazer_login(self):
        user = self.entry_user.get()
        senha = self.entry_senha.get()
        res = db.verificar_login(user, senha)
        if res:
            self.usuario_atual = user
            self.usuario_id = res[0]
            self.tela_principal()
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos!")

    def cadastrar_usuario(self):
        user = self.entry_user.get()
        senha = self.entry_senha.get()
        if not user or not senha:
            messagebox.showwarning("Aviso", "Preencha usuário e senha para cadastrar.")
            return
        if db.registrar_usuario(user, senha):
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso! Faça o login.")
        else:
            messagebox.showerror("Erro", "Nome de usuário já existe.")

    # ================= TELA PRINCIPAL =================
    def tela_principal(self):
        self.limpar_tela()

        top_bar = ctk.CTkFrame(self, height=75, corner_radius=0, fg_color=("#e0e0e0", "#2b2b2b"))
        top_bar.pack(side="top", fill="x")

        if self.imagem_logo_topo:
            lbl_logo_top = ctk.CTkLabel(top_bar, image=self.imagem_logo_topo, text="")
            lbl_logo_top.pack(side="left", padx=15, pady=5)

        lbl_bemvindo = ctk.CTkLabel(top_bar, text=f"👤 Operador: {self.usuario_atual}", font=FONTE_PADRAO)
        lbl_bemvindo.pack(side="left", padx=15)

        btn_tema = ctk.CTkButton(top_bar, text="🌓 Alternar Tema", font=FONTE_PADRAO, width=140, command=self.alternar_modo)
        btn_tema.pack(side="right", padx=20)

        btn_sair = ctk.CTkButton(top_bar, text="Sair", font=FONTE_PADRAO, fg_color="#e74c3c", hover_color="#c0392b", width=100, command=self.tela_login)
        btn_sair.pack(side="right")

        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview", 
                        font=("Arial", 13), 
                        rowheight=42, 
                        background="#ffffff", 
                        foreground="#000000", 
                        fieldbackground="#ffffff",
                        borderwidth=1,
                        relief="solid")
        
        style.configure("Treeview.Heading", 
                        font=("Arial", 14, "bold"), 
                        background="#d0d0d0", 
                        foreground="#000000",
                        relief="solid")
        
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_estoque = self.tabview.add("📦 Estoque & Entrada")
        self.tab_vendas = self.tabview.add("💰 Vendas")
        self.tab_gastos = self.tabview.add("💸 Gastos & Despesas")
        self.tab_relatorio = self.tabview.add("📊 Relatório Financeiro")

        self.construir_aba_estoque()
        self.construir_aba_vendas()
        self.construir_aba_gastos()
        self.construir_aba_relatorio()

    def alternar_modo(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

    # --- ABA 1: ESTOQUE E ENTRADA DE PRODUTOS ---
    def construir_aba_estoque(self):
        frame_esq = ctk.CTkFrame(self.tab_estoque, width=320)
        frame_esq.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(frame_esq, text="Cadastrar / Entrada Produto", font=FONTE_TITULO).pack(pady=15)

        self.ent_nome_prod = ctk.CTkEntry(frame_esq, placeholder_text="Nome do Produto", font=FONTE_PADRAO, height=40)
        self.ent_nome_prod.pack(pady=8, padx=15, fill="x")

        self.ent_qtd_prod = ctk.CTkEntry(frame_esq, placeholder_text="Quantidade Inicial", font=FONTE_PADRAO, height=40)
        self.ent_qtd_prod.pack(pady=8, padx=15, fill="x")

        self.ent_custo_prod = ctk.CTkEntry(frame_esq, placeholder_text="Preço de Custo (R$)", font=FONTE_PADRAO, height=40)
        self.ent_custo_prod.pack(pady=8, padx=15, fill="x")

        self.ent_venda_prod = ctk.CTkEntry(frame_esq, placeholder_text="Preço de Venda (R$)", font=FONTE_PADRAO, height=40)
        self.ent_venda_prod.pack(pady=8, padx=15, fill="x")

        btn_salvar_prod = ctk.CTkButton(frame_esq, text="Salvar no Estoque", font=FONTE_BOTAO, fg_color="#27ae60", height=45, command=self.salvar_produto)
        btn_salvar_prod.pack(pady=15, padx=15, fill="x")

        btn_excluir_prod = ctk.CTkButton(frame_esq, text="Excluir Produto Selecionado", font=FONTE_BOTAO, fg_color="#c0392b", hover_color="#a93226", height=45, command=self.excluir_produto)
        btn_excluir_prod.pack(pady=5, padx=15, fill="x")

        frame_tabela = ctk.CTkFrame(self.tab_estoque)
        frame_tabela.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.tree_estoque = ttk.Treeview(frame_tabela, columns=("ID", "Nome", "Qtd", "Custo", "Venda"), show="headings")
        
        self.tree_estoque.heading("ID", text="ID")
        self.tree_estoque.heading("Nome", text="Produto")
        self.tree_estoque.heading("Qtd", text="Qtd")
        self.tree_estoque.heading("Custo", text="Custo (R$)")
        self.tree_estoque.heading("Venda", text="Venda (R$)")

        self.tree_estoque.column("ID", width=70, anchor="center")
        self.tree_estoque.column("Nome", width=250, anchor="w")
        self.tree_estoque.column("Qtd", width=100, anchor="center")
        self.tree_estoque.column("Custo", width=130, anchor="e")
        self.tree_estoque.column("Venda", width=130, anchor="e")

        scrollbar_estoque = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree_estoque.yview)
        self.tree_estoque.configure(yscrollcommand=scrollbar_estoque.set)

        self.tree_estoque.pack(side="left", fill="both", expand=True)
        scrollbar_estoque.pack(side="right", fill="y")

        self.atualizar_tabela_estoque()

    def salvar_produto(self):
        try:
            nome = self.ent_nome_prod.get()
            qtd = int(self.ent_qtd_prod.get())
            custo = float(self.ent_custo_prod.get().replace(",", "."))
            venda = float(self.ent_venda_prod.get().replace(",", "."))

            if not nome:
                raise ValueError("Nome inválido")

            db.cursor.execute(
                "INSERT INTO produtos (usuario_id, nome, quantidade, preco_custo, preco_venda) VALUES (?, ?, ?, ?, ?)",
                (self.usuario_id, nome, qtd, custo, venda)
            )
            db.conn.commit()
            messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")
            self.atualizar_tabela_estoque()
            self.atualizar_combobox_vendas()
        except ValueError:
            messagebox.showerror("Erro", "Verifique se os campos numéricos e de texto foram preenchidos corretamente.")

    def excluir_produto(self):
        try:
            selecionado = self.tree_estoque.selection()
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um produto na tabela para excluir.")
                return
            
            item = self.tree_estoque.item(selecionado)
            prod_id = item['values'][0]

            if not prod_id or prod_id == "":
                return

            db.cursor.execute("SELECT COUNT(*) FROM vendas WHERE produto_id = ?", (prod_id,))
            qtd_vendas = db.cursor.fetchone()[0]

            if qtd_vendas > 0:
                if not messagebox.askyesno("Atenção", "Existem vendas registradas para este produto. Deseja realmente excluí-lo e apagar o histórico associado?"):
                    return
                db.cursor.execute("DELETE FROM vendas WHERE produto_id = ?", (prod_id,))

            db.cursor.execute("DELETE FROM produtos WHERE id = ?", (prod_id,))
            db.conn.commit()

            messagebox.showinfo("Sucesso", "Produto excluído do estoque com sucesso.")
            self.atualizar_tabela_estoque()
            self.atualizar_combobox_vendas()
            self.atualizar_tabela_vendas()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível excluir o produto: {e}")

    def atualizar_tabela_estoque(self):
        for row in self.tree_estoque.get_children():
            self.tree_estoque.delete(row)
        db.cursor.execute("SELECT id, nome, quantidade, preco_custo, preco_venda FROM produtos WHERE usuario_id = ?", (self.usuario_id,))
        for row in db.cursor.fetchall():
            row_fmt = list(row)
            row_fmt[3] = f"R$ {row_fmt[3]:.2f}"
            row_fmt[4] = f"R$ {row_fmt[4]:.2f}"
            self.tree_estoque.insert("", "end", values=row_fmt)
        
        self.preencher_linhas_vazias(self.tree_estoque, 13)

    # --- ABA 2: VENDAS ---
    def construir_aba_vendas(self):
        frame_esq = ctk.CTkFrame(self.tab_vendas, width=320)
        frame_esq.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(frame_esq, text="Realizar Venda", font=FONTE_TITULO).pack(pady=15)

        ctk.CTkLabel(frame_esq, text="Selecione o Produto:", font=FONTE_PADRAO).pack(anchor="w", padx=15)
        self.combo_produtos = ctk.CTkComboBox(frame_esq, values=[], font=FONTE_PADRAO, height=40)
        self.combo_produtos.pack(pady=8, padx=15, fill="x")

        self.ent_qtd_venda = ctk.CTkEntry(frame_esq, placeholder_text="Quantidade Vendida", font=FONTE_PADRAO, height=40)
        self.ent_qtd_venda.pack(pady=8, padx=15, fill="x")

        btn_vender = ctk.CTkButton(frame_esq, text="Concluir Venda", font=FONTE_BOTAO, fg_color="#2980b9", height=45, command=self.realizar_venda)
        btn_vender.pack(pady=15, padx=15, fill="x")

        btn_excluir_venda = ctk.CTkButton(frame_esq, text="Excluir Venda Selecionada", font=FONTE_BOTAO, fg_color="#c0392b", hover_color="#a93226", height=45, command=self.excluir_venda)
        btn_excluir_venda.pack(pady=5, padx=15, fill="x")

        frame_tabela_vendas = ctk.CTkFrame(self.tab_vendas)
        frame_tabela_vendas.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.tree_vendas = ttk.Treeview(frame_tabela_vendas, columns=("ID", "Produto", "Qtd", "Custo Total", "Venda Total", "Lucro", "Data"), show="headings")
        
        self.tree_vendas.heading("ID", text="ID")
        self.tree_vendas.heading("Produto", text="Produto")
        self.tree_vendas.heading("Qtd", text="Qtd")
        self.tree_vendas.heading("Custo Total", text="Custo Total")
        self.tree_vendas.heading("Venda Total", text="Venda Total")
        self.tree_vendas.heading("Lucro", text="Lucro")
        self.tree_vendas.heading("Data", text="Data/Hora")

        self.tree_vendas.column("ID", width=50, anchor="center")
        self.tree_vendas.column("Produto", width=160, anchor="w")
        self.tree_vendas.column("Qtd", width=50, anchor="center")
        self.tree_vendas.column("Custo Total", width=100, anchor="e")
        self.tree_vendas.column("Venda Total", width=100, anchor="e")
        self.tree_vendas.column("Lucro", width=100, anchor="e")
        self.tree_vendas.column("Data", width=130, anchor="center")

        scrollbar_vendas = ttk.Scrollbar(frame_tabela_vendas, orient="vertical", command=self.tree_vendas.yview)
        self.tree_vendas.configure(yscrollcommand=scrollbar_vendas.set)

        self.tree_vendas.pack(side="left", fill="both", expand=True)
        scrollbar_vendas.pack(side="right", fill="y")

        self.atualizar_combobox_vendas()
        self.atualizar_tabela_vendas()

    def atualizar_combobox_vendas(self):
        db.cursor.execute("SELECT id, nome FROM produtos WHERE usuario_id = ? AND quantidade > 0", (self.usuario_id,))
        produtos = db.cursor.fetchall()
        self.produtos_dict = {f"{p[1]} (ID: {p[0]})": p[0] for p in produtos}
        self.combo_produtos.configure(values=list(self.produtos_dict.keys()))

    def realizar_venda(self):
        try:
            selecionado = self.combo_produtos.get()
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um produto.")
                return
            
            produto_id = self.produtos_dict[selecionado]
            qtd_vendida = int(self.ent_qtd_venda.get())

            db.cursor.execute("SELECT quantidade, preco_custo, preco_venda FROM produtos WHERE id = ?", (produto_id,))
            qtd_estoque, custo_unit, venda_unit = db.cursor.fetchone()

            if qtd_vendida > qtd_estoque:
                messagebox.showerror("Erro", "Quantidade solicitada maior do que o estoque disponível!")
                return

            custo_total = custo_unit * qtd_vendida
            venda_total = venda_unit * qtd_vendida
            lucro = venda_total - custo_total
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")

            db.cursor.execute("""
                INSERT INTO vendas (usuario_id, produto_id, quantidade_vendida, preco_custo_total, preco_venda_total, lucro, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.usuario_id, produto_id, qtd_vendida, custo_total, venda_total, lucro, data_atual))

            nova_qtd = qtd_estoque - qtd_vendida
            db.cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, produto_id))
            db.conn.commit()

            messagebox.showinfo("Sucesso", f"Venda realizada!\nLucro obtido: R$ {lucro:.2f}")
            self.atualizar_tabela_vendas()
            self.atualizar_tabela_estoque()
            self.atualizar_combobox_vendas()
        except ValueError:
            messagebox.showerror("Erro", "Digite uma quantidade válida.")

    def excluir_venda(self):
        try:
            selecionado = self.tree_vendas.selection()
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione uma venda na tabela para excluir.")
                return
            
            item = self.tree_vendas.item(selecionado)
            venda_id = item['values'][0]

            if not venda_id or venda_id == "":
                return

            db.cursor.execute("SELECT produto_id, quantidade_vendida FROM vendas WHERE id = ?", (venda_id,))
            resultado = db.cursor.fetchone()
            if not resultado:
                return
            prod_id, qtd_vendida = resultado

            db.cursor.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?", (qtd_vendida, prod_id))
            db.cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
            db.conn.commit()

            messagebox.showinfo("Sucesso", "Venda excluída e itens retornados ao estoque.")
            self.atualizar_tabela_vendas()
            self.atualizar_tabela_estoque()
            self.atualizar_combobox_vendas()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível excluir: {e}")

    def atualizar_tabela_vendas(self):
        for row in self.tree_vendas.get_children():
            self.tree_vendas.delete(row)
        
        query = """
            SELECT v.id, p.nome, v.quantidade_vendida, v.preco_custo_total, v.preco_venda_total, v.lucro, v.data
            FROM vendas v JOIN produtos p ON v.produto_id = p.id
            WHERE v.usuario_id = ?
        """
        db.cursor.execute(query, (self.usuario_id,))
        for row in db.cursor.fetchall():
            row_fmt = list(row)
            row_fmt[3] = f"R$ {row_fmt[3]:.2f}"
            row_fmt[4] = f"R$ {row_fmt[4]:.2f}"
            row_fmt[5] = f"R$ {row_fmt[5]:.2f}"
            self.tree_vendas.insert("", "end", values=row_fmt)
        
        self.preencher_linhas_vazias(self.tree_vendas, 13)

    # --- ABA 3: GASTOS E DESPESAS ---
    def construir_aba_gastos(self):
        frame_esq = ctk.CTkFrame(self.tab_gastos, width=320)
        frame_esq.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(frame_esq, text="Registrar Gasto", font=FONTE_TITULO).pack(pady=15)

        self.combo_cat = ctk.CTkComboBox(frame_esq, values=["Água", "Energia", "IPTU", "Entrega", "Aluguel", "Outros"], font=FONTE_PADRAO, height=40)
        self.combo_cat.pack(pady=8, padx=15, fill="x")

        self.ent_desc_gasto = ctk.CTkEntry(frame_esq, placeholder_text="Descrição (ex: Frete centro)", font=FONTE_PADRAO, height=40)
        self.ent_desc_gasto.pack(pady=8, padx=15, fill="x")

        self.ent_valor_gasto = ctk.CTkEntry(frame_esq, placeholder_text="Valor (R$)", font=FONTE_PADRAO, height=40)
        self.ent_valor_gasto.pack(pady=8, padx=15, fill="x")

        btn_gasto = ctk.CTkButton(frame_esq, text="Salvar Gasto", font=FONTE_BOTAO, fg_color="#e67e22", hover_color="#d35400", height=45, command=self.salvar_gasto)
        btn_gasto.pack(pady=15, padx=15, fill="x")

        btn_excluir_gasto = ctk.CTkButton(frame_esq, text="Excluir Gasto Selecionado", font=FONTE_BOTAO, fg_color="#c0392b", hover_color="#a93226", height=45, command=self.excluir_gasto)
        btn_excluir_gasto.pack(pady=5, padx=15, fill="x")

        frame_tabela_gastos = ctk.CTkFrame(self.tab_gastos)
        frame_tabela_gastos.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.tree_gastos = ttk.Treeview(frame_tabela_gastos, columns=("ID", "Categoria", "Descrição", "Valor", "Data"), show="headings")
        
        self.tree_gastos.heading("ID", text="ID")
        self.tree_gastos.heading("Categoria", text="Categoria")
        self.tree_gastos.heading("Descrição", text="Descrição")
        self.tree_gastos.heading("Valor", text="Valor")
        self.tree_gastos.heading("Data", text="Data/Hora")

        self.tree_gastos.column("ID", width=60, anchor="center")
        self.tree_gastos.column("Categoria", width=140, anchor="w")
        self.tree_gastos.column("Descrição", width=220, anchor="w")
        self.tree_gastos.column("Valor", width=110, anchor="e")
        self.tree_gastos.column("Data", width=130, anchor="center")

        scrollbar_gastos = ttk.Scrollbar(frame_tabela_gastos, orient="vertical", command=self.tree_gastos.yview)
        self.tree_gastos.configure(yscrollcommand=scrollbar_gastos.set)

        self.tree_gastos.pack(side="left", fill="both", expand=True)
        scrollbar_gastos.pack(side="right", fill="y")

        self.atualizar_tabela_gastos()

    def salvar_gasto(self):
        try:
            cat = self.combo_cat.get()
            desc = self.ent_desc_gasto.get()
            valor = float(self.ent_valor_gasto.get().replace(",", "."))
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")

            db.cursor.execute("INSERT INTO gastos (usuario_id, categoria, descricao, valor, data) VALUES (?, ?, ?, ?, ?)",
                              (self.usuario_id, cat, desc, valor, data_atual))
            db.conn.commit()

            messagebox.showinfo("Sucesso", "Gasto registrado com sucesso!")
            self.atualizar_tabela_gastos()
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido.")

    def excluir_gasto(self):
        try:
            selecionado = self.tree_gastos.selection()
            if not selecionado:
                messagebox.showwarning("Aviso", "Selecione um gasto na tabela para excluir.")
                return
            
            item = self.tree_gastos.item(selecionado)
            gasto_id = item['values'][0]

            if not gasto_id or gasto_id == "":
                return

            db.cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
            db.conn.commit()

            messagebox.showinfo("Sucesso", "Gasto excluído com sucesso.")
            self.atualizar_tabela_gastos()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível excluir o gasto: {e}")

    def atualizar_tabela_gastos(self):
        for row in self.tree_gastos.get_children():
            self.tree_gastos.delete(row)
        db.cursor.execute("SELECT id, categoria, descricao, valor, data FROM gastos WHERE usuario_id = ?", (self.usuario_id,))
        for row in db.cursor.fetchall():
            row_fmt = list(row)
            row_fmt[3] = f"R$ {row_fmt[3]:.2f}"
            self.tree_gastos.insert("", "end", values=row_fmt)
        
        self.preencher_linhas_vazias(self.tree_gastos, 13)

    # --- ABA 4: RELATÓRIO FINANCEIRO ---
    def construir_aba_relatorio(self):
        frame_topo = ctk.CTkFrame(self.tab_relatorio)
        frame_topo.pack(side="top", fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_topo, text="Período do Relatório:", font=FONTE_PADRAO).pack(side="left", padx=10, pady=10)
        
        self.combo_periodo = ctk.CTkComboBox(frame_topo, values=["Últimos 30 Dias", "Últimos 20 Dias", "Últimos 7 Dias", "Todo o Período"], font=FONTE_PADRAO, height=35)
        self.combo_periodo.pack(side="left", padx=10, pady=10)
        self.combo_periodo.set("Últimos 30 Dias")

        btn_gerar = ctk.CTkButton(frame_topo, text="Gerar Relatório", font=FONTE_BOTAO, height=35, command=self.gerar_relatorio)
        btn_gerar.pack(side="left", padx=10, pady=10)

        frame_tabela_rel = ctk.CTkFrame(self.tab_relatorio)
        frame_tabela_rel.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree_relatorio = ttk.Treeview(frame_tabela_rel, columns=("Indicador", "Valor"), show="headings")
        
        self.tree_relatorio.heading("Indicador", text="Indicador / Descrição Financeira")
        self.tree_relatorio.heading("Valor", text="Valor (R$)")

        self.tree_relatorio.column("Indicador", width=600, anchor="w")
        self.tree_relatorio.column("Valor", width=250, anchor="e")

        scrollbar_rel = ttk.Scrollbar(frame_tabela_rel, orient="vertical", command=self.tree_relatorio.yview)
        self.tree_relatorio.configure(yscrollcommand=scrollbar_rel.set)

        self.tree_relatorio.pack(side="left", fill="both", expand=True)
        scrollbar_rel.pack(side="right", fill="y")

        self.gerar_relatorio()

    def gerar_relatorio(self):
        for row in self.tree_relatorio.get_children():
            self.tree_relatorio.delete(row)

        periodo = self.combo_periodo.get()
        dias = 30
        if "20" in periodo:
            dias = 20
        elif "7" in periodo:
            dias = 7
        elif "Todo" in periodo:
            dias = 36500

        data_limite = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

        db.cursor.execute("""
            SELECT SUM(preco_venda_total), SUM(lucro) FROM vendas 
            WHERE usuario_id = ? AND data >= ?
        """, (self.usuario_id, data_limite))
        res_vendas = db.cursor.fetchone()
        total_vendas = res_vendas[0] if res_vendas and res_vendas[0] else 0.0
        lucro_bruto = res_vendas[1] if res_vendas and res_vendas[1] else 0.0

        db.cursor.execute("""
            SELECT SUM(valor) FROM gastos 
            WHERE usuario_id = ? AND data >= ?
        """, (self.usuario_id, data_limite))
        res_gastos = db.cursor.fetchone()
        total_gastos = res_gastos[0] if res_gastos[0] else 0.0

        lucro_liquido = lucro_bruto - total_gastos

        db.cursor.execute("""
            SELECT categoria, SUM(valor) FROM gastos 
            WHERE usuario_id = ? AND data >= ? GROUP BY categoria
        """, (self.usuario_id, data_limite))
        gastos_cat = db.cursor.fetchall()

        self.tree_relatorio.insert("", "end", values=(f"=== RESUMO FINANCEIRO ({periodo}) ===", ""))
        self.tree_relatorio.insert("", "end", values=("💰 Faturamento Total com Vendas", f"R$ {total_vendas:.2f}"))
        self.tree_relatorio.insert("", "end", values=("📈 Lucro Bruto (Vendas - Custo dos Produtos)", f"R$ {lucro_bruto:.2f}"))
        self.tree_relatorio.insert("", "end", values=("💸 Total de Gastos e Despesas", f"R$ {total_gastos:.2f}"))
        self.tree_relatorio.insert("", "end", values=("--------------------------------------------------------------------------------", "---------------------"))
        self.tree_relatorio.insert("", "end", values=("💎 LUCRO LÍQUIDO NO PERÍODO", f"R$ {lucro_liquido:.2f}"))
        self.tree_relatorio.insert("", "end", values=("--------------------------------------------------------------------------------", "---------------------"))
        self.tree_relatorio.insert("", "end", values=("📂 DETALHAMENTO DE GASTOS POR CATEGORIA", ""))
        
        if gastos_cat:
            for cat, val in gastos_cat:
                self.tree_relatorio.insert("", "end", values=(f"    • {cat}", f"R$ {val:.2f}"))
        else:
            self.tree_relatorio.insert("", "end", values=("    • Nenhum gasto registrado neste período.", "R$ 0.00"))

        self.preencher_linhas_vazias(self.tree_relatorio, 13)

if __name__ == "__main__":
    app = GestorComercialApp()
    app.mainloop()
