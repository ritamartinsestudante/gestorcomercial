from datetime import datetime
import sqlite3
import flet as ft

# --- BANCO DE DADOS ---
def get_db():
    conn = sqlite3.connect("gestor_comercial.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)
    cursor.execute("""
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
    cursor.execute("""
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
    cursor.execute("""
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
    conn.commit()
    conn.close()

criar_tabelas()

def main(page: ft.Page):
    page.title = "Gestor Comercial"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1100
    page.window_height = 750

    user_session = {"id": None, "username": ""}

    def mostrar_alerta(mensagem, cor=ft.Colors.RED):
        snack = ft.SnackBar(ft.Text(mensagem, color=ft.Colors.WHITE), bgcolor=cor)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def carregar_dashboard():
        page.clean()

        # --- ABA ESTOQUE ---
        txt_prod_nome = ft.TextField(label="Nome do Produto", width=250)
        txt_prod_qtd = ft.TextField(label="Qtd Inicial", width=250, keyboard_type=ft.KeyboardType.NUMBER)
        txt_prod_custo = ft.TextField(label="Preço Custo (R$)", width=250)
        txt_prod_venda = ft.TextField(label="Preço Venda (R$)", width=250)
        tabela_produtos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Custo")),
                ft.DataColumn(ft.Text("Venda")),
                ft.DataColumn(ft.Text("Ação")),
            ],
            rows=[]
        )

        def atualizar_estoque():
            tabela_produtos.rows.clear()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos WHERE usuario_id = ?", (user_session["id"],))
            produtos = cursor.fetchall()
            conn.close()

            for p in produtos:
                def excluir_p(e, pid=p["id"]):
                    conn = get_db()
                    conn.cursor().execute("DELETE FROM produtos WHERE id = ? AND usuario_id = ?", (pid, user_session["id"]))
                    conn.commit()
                    conn.close()
                    atualizar_estoque()
                    atualizar_vendas()

                tabela_produtos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p["id"]))),
                        ft.DataCell(ft.Text(p["nome"])),
                        ft.DataCell(ft.Text(str(p["quantidade"]))),
                        ft.DataCell(ft.Text(f"R$ {p['preco_custo']:.2f}")),
                        ft.DataCell(ft.Text(f"R$ {p['preco_venda']:.2f}")),
                        ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=excluir_p, tooltip="Excluir Produto")),
                    ])
                )
            page.update()

        def salvar_produto(e):
            try:
                nome = txt_prod_nome.value
                qtd = int(txt_prod_qtd.value)
                custo = float(txt_prod_custo.value.replace(",", "."))
                venda = float(txt_prod_venda.value.replace(",", "."))

                conn = get_db()
                conn.cursor().execute("INSERT INTO produtos (usuario_id, nome, quantidade, preco_custo, preco_venda) VALUES (?, ?, ?, ?, ?)",
                                      (user_session["id"], nome, qtd, custo, venda))
                conn.commit()
                conn.close()

                txt_prod_nome.value = ""
                txt_prod_qtd.value = ""
                txt_prod_custo.value = ""
                txt_prod_venda.value = ""
                atualizar_estoque()
                atualizar_vendas()
                mostrar_alerta("Produto salvo com sucesso!", ft.Colors.GREEN)
            except ValueError:
                mostrar_alerta("Verifique se os campos numéricos estão corretos.")

        tab_estoque_content = ft.Container(
            ft.Row([
                ft.Column([
                    ft.Text("Cadastrar Produto", weight=ft.FontWeight.BOLD),
                    txt_prod_nome, txt_prod_qtd, txt_prod_custo, txt_prod_venda,
                    ft.Button("Salvar Produto", on_click=salvar_produto, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
                ], width=300),
                ft.VerticalDivider(),
                ft.Column([ft.Text("Lista de Produtos", weight=ft.FontWeight.BOLD), ft.Row([tabela_produtos], scroll=ft.ScrollMode.AUTO)], expand=True)
            ], expand=True),
            padding=20
        )

        # --- ABA VENDAS ---
        dd_produtos = ft.Dropdown(label="Selecione o Produto", width=250)
        txt_venda_qtd = ft.TextField(label="Quantidade Vendida", width=250, keyboard_type=ft.KeyboardType.NUMBER)
        tabela_vendas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Total Venda")),
                ft.DataColumn(ft.Text("Lucro")),
                ft.DataColumn(ft.Text("Ação")),
            ],
            rows=[]
        )

        def atualizar_vendas():
            dd_produtos.options.clear()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos WHERE usuario_id = ? AND quantidade > 0", (user_session["id"],))
            for p in cursor.fetchall():
                dd_produtos.options.append(ft.dropdown.Option(key=str(p["id"]), text=f"{p['nome']} (Estoque: {p['quantidade']})"))

            tabela_vendas.rows.clear()
            cursor.execute("""
                SELECT v.*, p.nome as nome_produto FROM vendas v 
                JOIN produtos p ON v.produto_id = p.id WHERE v.usuario_id = ?
            """, (user_session["id"],))
            vendas = cursor.fetchall()
            conn.close()

            for v in vendas:
                def excluir_v(e, vid=v["id"]):
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT produto_id, quantidade_vendida FROM vendas WHERE id = ? AND usuario_id = ?", (vid, user_session["id"]))
                    vend = cursor.fetchone()
                    if vend:
                        cursor.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?", (vend["quantidade_vendida"], vend["produto_id"]))
                        cursor.execute("DELETE FROM vendas WHERE id = ?", (vid,))
                        conn.commit()
                    conn.close()
                    atualizar_estoque()
                    atualizar_vendas()
                    atualizar_relatorio()

                tabela_vendas.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(v["id"]))),
                        ft.DataCell(ft.Text(v["nome_produto"])),
                        ft.DataCell(ft.Text(str(v["quantidade_vendida"]))),
                        ft.DataCell(ft.Text(f"R$ {v['preco_venda_total']:.2f}")),
                        ft.DataCell(ft.Text(f"R$ {v['lucro']:.2f}")),
                        ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=excluir_v, tooltip="Excluir Venda")),
                    ])
                )
            page.update()

        def realizar_venda(e):
            if not dd_produtos.value or not txt_venda_qtd.value:
                mostrar_alerta("Selecione o produto e a quantidade.")
                return
            try:
                prod_id = int(dd_produtos.value)
                qtd_v = int(txt_venda_qtd.value)

                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT quantidade, preco_custo, preco_venda FROM produtos WHERE id = ? AND usuario_id = ?", (prod_id, user_session["id"]))
                p = cursor.fetchone()

                if not p or p["quantidade"] < qtd_v:
                    mostrar_alerta("Estoque insuficiente!")
                    conn.close()
                    return

                custo_total = p["preco_custo"] * qtd_v
                venda_total = p["preco_venda"] * qtd_v
                lucro = venda_total - custo_total
                data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")

                cursor.execute("INSERT INTO vendas (usuario_id, produto_id, quantidade_vendida, preco_custo_total, preco_venda_total, lucro, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (user_session["id"], prod_id, qtd_v, custo_total, venda_total, lucro, data_atual))
                cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (qtd_v, prod_id))
                conn.commit()
                conn.close()

                txt_venda_qtd.value = ""
                dd_produtos.value = None
                atualizar_estoque()
                atualizar_vendas()
                atualizar_relatorio()
                mostrar_alerta("Venda realizada com sucesso!", ft.Colors.GREEN)
            except Exception as ex:
                mostrar_alerta(f"Erro: {ex}")

        tab_vendas_content = ft.Container(
            ft.Row([
                ft.Column([
                    ft.Text("Realizar Venda", weight=ft.FontWeight.BOLD),
                    dd_produtos, txt_venda_qtd,
                    ft.Button("Concluir Venda", on_click=realizar_venda, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
                ], width=300),
                ft.VerticalDivider(),
                ft.Column([ft.Text("Histórico de Vendas", weight=ft.FontWeight.BOLD), ft.Row([tabela_vendas], scroll=ft.ScrollMode.AUTO)], expand=True)
            ], expand=True),
            padding=20
        )

        # --- ABA GASTOS ---
        dd_categoria = ft.Dropdown(label="Categoria", options=[
            ft.dropdown.Option("Água"), ft.dropdown.Option("Energia"), ft.dropdown.Option("IPTU"),
            ft.dropdown.Option("Entrega"), ft.dropdown.Option("Aluguel"), ft.dropdown.Option("Outros")
        ], width=250)
        txt_gasto_desc = ft.TextField(label="Descrição", width=250)
        txt_gasto_valor = ft.TextField(label="Valor (R$)", width=250)
        tabela_gastos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Categoria")),
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Valor")),
                ft.DataColumn(ft.Text("Ação")),
            ],
            rows=[]
        )

        def atualizar_gastos():
            tabela_gastos.rows.clear()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gastos WHERE usuario_id = ?", (user_session["id"],))
            gastos = cursor.fetchall()
            conn.close()

            for g in gastos:
                def excluir_g(e, gid=g["id"]):
                    conn = get_db()
                    conn.cursor().execute("DELETE FROM gastos WHERE id = ? AND usuario_id = ?", (gid, user_session["id"]))
                    conn.commit()
                    conn.close()
                    atualizar_gastos()
                    atualizar_relatorio()

                tabela_gastos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(g["id"]))),
                        ft.DataCell(ft.Text(g["categoria"])),
                        ft.DataCell(ft.Text(g["descricao"])),
                        ft.DataCell(ft.Text(f"R$ {g['valor']:.2f}")),
                        ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=excluir_g, tooltip="Excluir Gasto")),
                    ])
                )
            page.update()

        def salvar_gasto(e):
            try:
                cat = dd_categoria.value
                desc = txt_gasto_desc.value
                valor = float(txt_gasto_valor.value.replace(",", "."))
                data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")

                if not cat or not desc:
                    mostrar_alerta("Preencha todos os campos do gasto.")
                    return

                conn = get_db()
                conn.cursor().execute("INSERT INTO gastos (usuario_id, categoria, descricao, valor, data) VALUES (?, ?, ?, ?, ?)",
                                      (user_session["id"], cat, desc, valor, data_atual))
                conn.commit()
                conn.close()

                txt_gasto_desc.value = ""
                txt_gasto_valor.value = ""
                dd_categoria.value = None
                atualizar_gastos()
                atualizar_relatorio()
                mostrar_alerta("Gasto registrado!", ft.Colors.GREEN)
            except ValueError:
                mostrar_alerta("Valor de gasto inválido.")

        tab_gastos_content = ft.Container(
            ft.Row([
                ft.Column([
                    ft.Text("Registrar Gasto", weight=ft.FontWeight.BOLD),
                    dd_categoria, txt_gasto_desc, txt_gasto_valor,
                    ft.Button("Salvar Gasto", on_click=salvar_gasto, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE)
                ], width=300),
                ft.VerticalDivider(),
                ft.Column([ft.Text("Histórico de Gastos", weight=ft.FontWeight.BOLD), ft.Row([tabela_gastos], scroll=ft.ScrollMode.AUTO)], expand=True)
            ], expand=True),
            padding=20
        )

        # --- ABA RELATÓRIO ---
        lbl_fat = ft.Text("R$ 0.00", size=16, weight=ft.FontWeight.BOLD)
        lbl_lucro_b = ft.Text("R$ 0.00", size=16, weight=ft.FontWeight.BOLD)
        lbl_gastos = ft.Text("R$ 0.00", size=16, weight=ft.FontWeight.BOLD)
        lbl_lucro_l = ft.Text("R$ 0.00", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)

        def atualizar_relatorio():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(preco_venda_total), SUM(lucro) FROM vendas WHERE usuario_id = ?", (user_session["id"],))
            res_v = cursor.fetchone()
            tot_v = res_v[0] if res_v and res_v[0] else 0.0
            luc_b = res_v[1] if res_v and res_v[1] else 0.0

            cursor.execute("SELECT SUM(valor) FROM gastos WHERE usuario_id = ?", (user_session["id"],))
            res_g = cursor.fetchone()
            tot_g = res_g[0] if res_g and res_g[0] else 0.0
            conn.close()

            luc_l = luc_b - tot_g

            lbl_fat.value = f"R$ {tot_v:.2f}"
            lbl_lucro_b.value = f"R$ {luc_b:.2f}"
            lbl_gastos.value = f"R$ {tot_g:.2f}"
            lbl_lucro_l.value = f"R$ {luc_l:.2f}"
            page.update()

        tab_relatorio_content = ft.Container(
            ft.Column([
                ft.Text("Resumo Financeiro", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([ft.Text("💰 Faturamento Total com Vendas:"), lbl_fat]),
                ft.Row([ft.Text("📈 Lucro Bruto:"), lbl_lucro_b]),
                ft.Row([ft.Text("💸 Total de Gastos:"), lbl_gastos]),
                ft.Divider(),
                ft.Row([ft.Text("💎 LUCRO LÍQUIDO:", size=16, weight=ft.FontWeight.BOLD), lbl_lucro_l]),
            ], alignment=ft.MainAxisAlignment.START, spacing=15),
            padding=20
        )

        # --- MENU DE NAVEGAÇÃO PERSONALIZADO ---
        conteudo_aba = ft.Column([tab_estoque_content], expand=True)

        btn_estoque = ft.Button("📦 Estoque", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
        btn_vendas = ft.Button("💰 Vendas", bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLACK)
        btn_gastos = ft.Button("💸 Gastos", bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLACK)
        btn_relatorio = ft.Button("📊 Relatório", bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLACK)

        def mudar_aba(e, aba_selecionada):
            btn_estoque.bgcolor = ft.Colors.GREY_300
            btn_estoque.color = ft.Colors.BLACK
            btn_vendas.bgcolor = ft.Colors.GREY_300
            btn_vendas.color = ft.Colors.BLACK
            btn_gastos.bgcolor = ft.Colors.GREY_300
            btn_gastos.color = ft.Colors.BLACK
            btn_relatorio.bgcolor = ft.Colors.GREY_300
            btn_relatorio.color = ft.Colors.BLACK

            conteudo_aba.controls.clear()

            if aba_selecionada == "estoque":
                btn_estoque.bgcolor = ft.Colors.BLUE_700
                btn_estoque.color = ft.Colors.WHITE
                conteudo_aba.controls.append(tab_estoque_content)
            elif aba_selecionada == "vendas":
                btn_vendas.bgcolor = ft.Colors.BLUE_700
                btn_vendas.color = ft.Colors.WHITE
                conteudo_aba.controls.append(tab_vendas_content)
            elif aba_selecionada == "gastos":
                btn_gastos.bgcolor = ft.Colors.BLUE_700
                btn_gastos.color = ft.Colors.WHITE
                conteudo_aba.controls.append(tab_gastos_content)
            elif aba_selecionada == "relatorio":
                btn_relatorio.bgcolor = ft.Colors.BLUE_700
                btn_relatorio.color = ft.Colors.WHITE
                conteudo_aba.controls.append(tab_relatorio_content)
            page.update()

        btn_estoque.on_click = lambda e: mudar_aba(e, "estoque")
        btn_vendas.on_click = lambda e: mudar_aba(e, "vendas")
        btn_gastos.on_click = lambda e: mudar_aba(e, "gastos")
        btn_relatorio.on_click = lambda e: mudar_aba(e, "relatorio")

        menu_abas = ft.Row([btn_estoque, btn_vendas, btn_gastos, btn_relatorio], alignment=ft.MainAxisAlignment.START, spacing=10)

        def sair(e):
            user_session["id"] = None
            user_session["username"] = ""
            tela_login()

        page.add(
            ft.Row([
                ft.Row([
                    ft.Image(src="logo.png", width=35, height=35, error_content=ft.Text("LOGO")),
                    ft.Text(f"👤 Usuário: {user_session['username']}", weight=ft.FontWeight.BOLD),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Button("Sair", on_click=sair, color=ft.Colors.RED)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            menu_abas,
            ft.Divider(height=10),
            conteudo_aba
        )
        
        atualizar_estoque()
        atualizar_vendas()
        atualizar_gastos()
        atualizar_relatorio()

    def tela_login():
        page.clean()
        
        txt_user = ft.TextField(label="Usuário", width=300)
        txt_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)

        def fazer_login(e):
            if not txt_user.value or not txt_senha.value:
                mostrar_alerta("Preencha todos os campos!")
                return
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM usuarios WHERE username = ? AND senha = ?", (txt_user.value, txt_senha.value))
            res = cursor.fetchone()
            conn.close()

            if res:
                user_session["id"] = res["id"]
                user_session["username"] = res["username"]
                carregar_dashboard()
            else:
                mostrar_alerta("Usuário ou senha incorretos!")

        def fazer_cadastro(e):
            if not txt_user.value or not txt_senha.value:
                mostrar_alerta("Preencha usuário e senha para cadastrar!")
                return
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (txt_user.value, txt_senha.value))
                conn.commit()
                conn.close()
                mostrar_alerta("Usuário cadastrado com sucesso! Faça login.", ft.Colors.GREEN)
                txt_user.value = ""
                txt_senha.value = ""
                page.update()
            except sqlite3.IntegrityError:
                mostrar_alerta("Este nome de usuário já existe. Escolha outro.")

        page.add(
            ft.Column([
                ft.Image(src="logo.png", width=80, height=80, error_content=ft.Text("🛒", size=40)),
                ft.Text("GESTOR COMERCIAL", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                txt_user,
                txt_senha,
                ft.Row([
                    ft.Button("Entrar", on_click=fazer_login, width=140, color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE),
                    ft.Button("Cadastrar", on_click=fazer_cadastro, width=140, color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # Iniciar na tela de login
    tela_login()




if __name__ == "__main__":
    ft.app(target=main)

