import sqlite3
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox, ttk

# Configurações de fonte e visual (Tudo maior e legível)
FONTE_PADRAO = ("Arial", 14)
FONTE_TITULO = ("Arial", 18, "bold")
FONTE_BOTAO = ("Arial", 14, "bold")

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
        self.geometry("1100x750")
        self.usuario_atual = None
        self.usuario_id = None

        self.tela_login()

    def limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ================= TELA DE LOGIN =================
    def tela_login(self):
        self.limpar_tela()

        frame = ctk.CTkFrame(self, width=450, height=500, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        lbl_logo = ctk.CTkLabel(frame, text="🛒 GESTOR COMERCIAL", font=FONTE_TITULO)
        lbl_logo.pack(pady=35)

        self.entry_user = ctk.CTkEntry(frame, placeholder_text="Usuário", font=FONTE_PADRAO, width=320, height=45)
        self.entry_user.pack(pady=10)

        self.entry_senha = ctk.CTkEntry(frame, placeholder_text="Senha", show="*", font=FONTE_PADRAO, width=320, height=45)
        self.entry_senha.pack(pady=10)

        btn_entrar = ctk.CTkButton(frame, text="Entrar", font=FONTE_BOTAO, fg_color="#2ecc71", hover_color="#27ae60", width=320, height=45, command=self.fazer_login)
        btn_entrar.pack(pady=20)

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

        top_bar = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("#e0e0e0", "#2b2b2b"))
        top_bar.pack(side="top", fill="x")

        lbl_bemvindo = ctk.CTkLabel(top_bar, text=f"👤 Operador: {self.usuario_atual}", font=FONTE_PADRAO)
        lbl_bemvindo.pack(side="left", padx=20)

        btn_tema = ctk.CTkButton(top_bar, text="🌓 Alternar Tema", font=FONTE_PADRAO, width=140, command=self.alternar_modo)
        btn_tema.pack(side="right", padx=20)

        btn_sair = ctk.CTkButton(top_bar, text="Sair", font=FONTE_PADRAO, fg_color="#e74c3c", hover_color="#c0392b", width=100, command=self.tela_login)
        btn_sair.pack(side="right")

        # Configurar Estilo das Tabelas para letras maiores e linhas espaçosas
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 13), rowheight=32)
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

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
        btn_salvar_prod.pack(pady=20, padx=15, fill="x")

        self.tree_estoque = ttk.Treeview(self.tab_estoque, columns=("ID", "Nome", "Qtd", "Custo", "Venda"), show="headings")
        self.tree_estoque.heading("ID", text="ID")
        self.tree_estoque.heading("Nome", text="Produto")
        self.tree_estoque.heading("Qtd", text="Qtd")
        self.tree_estoque.heading("Custo", text="Custo (R$)")
        self.tree_estoque.heading("Venda", text="Venda (R$)")
        self.tree_estoque.pack(side="right", fill="both", expand=True, padx=10, pady=10)

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

    def atualizar_tabela_estoque(self):
        for row in self.tree_estoque.get_children():
            self.tree_estoque.delete(row)
        db.cursor.execute("SELECT id, nome, quantidade, preco_custo, preco_venda FROM produtos WHERE usuario_id = ?", (self.usuario_id,))
        for row in db.cursor.fetchall():
            self.tree_estoque.insert("", "end", values=row)

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

        btn_excluir_venda = ctk.CTkButton(frame_esq, text="Excluir Venda Selecionada", font=FONTE_BOTAO, fg_color="#c0392b", height=45, command=self.excluir_venda)
        btn_excluir_venda.pack(pady=5, padx=15, fill="x")

        self.tree_vendas = ttk.Treeview(self.tab_vendas, columns=("ID", "Produto", "Qtd", "Custo Total", "Venda Total", "Lucro", "Data"), show="headings")
        for col in self.tree_vendas["columns"]:
            self.tree_vendas.heading(col, text=col)
        self.tree_vendas.pack(side="right", fill="both", expand=True, padx=10, pady=10)

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

            db.cursor.execute("SELECT produto_id, quantidade_vendida FROM vendas WHERE id = ?", (venda_id,))
            prod_id, qtd_vendida = db.cursor.fetchone()

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
        btn_gasto.pack(pady=20, padx=15, fill="x")

        self.tree_gastos = ttk.Treeview(self.tab_gastos, columns=("ID", "Categoria", "Descrição", "Valor", "Data"), show="headings")
        for col in self.tree_gastos["columns"]:
            self.tree_gastos.heading(col, text=col)
        self.tree_gastos.pack(side="right", fill="both", expand=True, padx=10, pady=10)

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

    def atualizar_tabela_gastos(self):
        for row in self.tree_gastos.get_children():
            self.tree_gastos.delete(row)
        db.cursor.execute("SELECT id, categoria, descricao, valor, data FROM gastos WHERE usuario_id = ?", (self.usuario_id,))
        for row in db.cursor.fetchall():
            row_fmt = list(row)
            row_fmt[3] = f"R$ {row_fmt[3]:.2f}"
            self.tree_gastos.insert("", "end", values=row_fmt)

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

        self.txt_relatorio = ctk.CTkTextbox(self.tab_relatorio, font=("Arial", 16))
        self.txt_relatorio.pack(fill="both", expand=True, padx=10, pady=10)

        self.gerar_relatorio()

    def gerar_relatorio(self):
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
        total_gastos = res_gastos[0] if res_gastos and res_gastos[0] else 0.0

        lucro_liquido = lucro_bruto - total_gastos

        db.cursor.execute("""
            SELECT categoria, SUM(valor) FROM gastos 
            WHERE usuario_id = ? AND data >= ? GROUP BY categoria
        """, (self.usuario_id, data_limite))
        gastos_cat = db.cursor.fetchall()

        texto = f"=== RELATÓRIO FINANCEIRO ({periodo}) ===\n\n"
        texto += f"💰 Faturamento Total com Vendas: R$ {total_vendas:.2f}\n"
        texto += f"📈 Lucro Bruto (Vendas - Custo dos Produtos): R$ {lucro_bruto:.2f}\n"
        texto += f"💸 Total de Gastos e Despesas: R$ {total_gastos:.2f}\n"
        texto += "-" * 50 + "\n"
        texto += f"💎 LUCRO LÍQUIDO NO PERÍODO: R$ {lucro_liquido:.2f}\n"
        texto += "-" * 50 + "\n\n"
        
        texto += "Detalhamento de Gastos por Categoria:\n"
        if gastos_cat:
            for cat, val in gastos_cat:
                texto += f" • {cat}: R$ {val:.2f}\n"
        else:
            texto += " Nenhum gasto registrado neste período.\n"

        self.txt_relatorio.delete("0.0", "end")
        self.txt_relatorio.insert("0.0", texto)

if __name__ == "__main__":
    app = GestorComercialApp()
    app.mainloop()
