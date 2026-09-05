from datetime import datetime
import sqlite3
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor Comercial", page_icon="🛒", layout="centered")

# --- BANCO DE DADOS ---
DB_NAME = "gestor_comercial.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    with get_db() as conn:
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

criar_tabelas()

# --- CONTROLE DE SESSÃO ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""

# --- TELA DE LOGIN / CADASTRO ---
if st.session_state.user_id is None:
    st.title("🛒 GESTOR COMERCIAL")
    st.write("Faça login ou cadastre-se para acessar o sistema.")
    
    aba_login, aba_cad = st.tabs(["🔑 Entrar", "📝 Cadastrar"])
    
    with aba_login:
        user_l = st.text_input("Usuário", key="l_user")
        senha_l = st.text_input("Senha", type="password", key="l_senha")
        if st.button("Entrar no Sistema", use_container_width=True):
            if not user_l or not senha_l:
                st.error("Preencha todos os campos!")
            else:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, username FROM usuarios WHERE username = ? AND senha = ?", (user_l, senha_l))
                    res = cursor.fetchone()
                if res:
                    st.session_state.user_id = res["id"]
                    st.session_state.username = res["username"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")

    with aba_cad:
        user_c = st.text_input("Novo Usuário", key="c_user")
        senha_c = st.text_input("Nova Senha", type="password", key="c_senha")
        if st.button("Criar Cadastro", use_container_width=True):
            if not user_c or not senha_c:
                st.error("Preencha usuário e senha!")
            else:
                try:
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (user_c, senha_c))
                        conn.commit()
                    st.success("Cadastro realizado com sucesso! Vá para a aba 'Entrar'.")
                except sqlite3.IntegrityError:
                    st.error("Este nome de usuário já existe.")

else:
    # --- DASHBOARD PRINCIPAL ---
    col_topo1, col_topo2 = st.columns([0.8, 0.2])
    col_topo1.markdown(f"### 👤 Usuário: **{st.session_state.username}**")
    if col_topo2.button("Sair", type="secondary"):
        st.session_state.user_id = None
        st.session_state.username = ""
        st.rerun()

    st.divider()

    aba_est, aba_vend, aba_gast, aba_rel = st.tabs(["📦 Estoque", "💰 Vendas", "💸 Gastos", "📊 Relatório"])

    # --- ABA 1: ESTOQUE ---
    with aba_est:
        st.subheader("Gerenciamento de Estoque")
        col_cad, col_lst = st.columns([1, 2])
        
        with col_cad:
            st.text("Cadastrar Produto")
            p_nome = st.text_input("Nome do Produto")
            p_qtd = st.number_input("Qtd Inicial", min_value=0, step=1)
            p_custo = st.text_input("Preço Custo (R$)", value="0.00")
            p_venda = st.text_input("Preço Venda (R$)", value="0.00")
            
            if st.button("Salvar Produto", use_container_width=True):
                try:
                    custo_val = float(p_custo.replace(",", "."))
                    venda_val = float(p_venda.replace(",", "."))
                    if not p_nome:
                        st.error("Informe o nome do produto.")
                    else:
                        with get_db() as conn:
                            conn.cursor().execute(
                                "INSERT INTO produtos (usuario_id, nome, quantidade, preco_custo, preco_venda) VALUES (?, ?, ?, ?, ?)",
                                (st.session_state.user_id, p_nome, p_qtd, custo_val, venda_val)
                            )
                            conn.commit()
                        st.success("Produto salvo!")
                        st.rerun()
                except ValueError:
                    st.error("Verifique se os valores numéricos estão corretos.")

        with col_lst:
            st.text("Produtos Cadastrados")
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, quantidade, preco_custo, preco_venda FROM produtos WHERE usuario_id = ?", (st.session_state.user_id,))
                produtos = cursor.fetchall()

            if produtos:
                for p in produtos:
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                    c1.write(f"**{p['nome']}** (Estoque: {p['quantidade']})")
                    c2.write(f"C: R$ {p['preco_custo']:.2f}")
                    c3.write(f"V: R$ {p['preco_venda']:.2f}")
                    if c4.button("🗑️", key=f"del_p_{p['id']}"):
                        with get_db() as conn:
                            conn.cursor().execute("DELETE FROM produtos WHERE id = ? AND usuario_id = ?", (p['id'], st.session_state.user_id))
                            conn.commit()
                        st.rerun()
            else:
                st.info("Nenhum produto cadastrado.")

    # --- ABA 2: VENDAS ---
    with aba_vend:
        st.subheader("Registro de Vendas")
        col_v1, col_v2 = st.columns([1, 2])

        with col_v1:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, quantidade FROM produtos WHERE usuario_id = ? AND quantidade > 0", (st.session_state.user_id,))
                prods_disponiveis = cursor.fetchall()

            dict_prods = {f"{p['nome']} (Estoque: {p['quantidade']})": p['id'] for p in prods_disponiveis}
            
            if dict_prods:
                prod_escolhido = st.selectbox("Selecione o Produto", options=list(dict_prods.keys()))
                qtd_vendida = st.number_input("Quantidade Vendida", min_value=1, step=1)
                
                if st.button("Concluir Venda", use_container_width=True):
                    pid = dict_prods[prod_escolhido]
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT quantidade, preco_custo, preco_venda FROM produtos WHERE id = ?", (pid,))
                        prod_info = cursor.fetchone()
                        
                        if prod_info and prod_info["quantidade"] >= qtd_vendida:
                            c_total = prod_info["preco_custo"] * qtd_vendida
                            v_total = prod_info["preco_venda"] * qtd_vendida
                            lucro = v_total - c_total
                            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")

                            cursor.execute(
                                "INSERT INTO vendas (usuario_id, produto_id, quantidade_vendida, preco_custo_total, preco_venda_total, lucro, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (st.session_state.user_id, pid, qtd_vendida, c_total, v_total, lucro, data_atual)
                            )
                            cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (qtd_vendida, pid))
                            conn.commit()
                            st.success("Venda realizada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Estoque insuficiente!")
            else:
                st.warning("Não há produtos com estoque disponível para venda.")

        with col_v2:
            st.text("Histórico de Vendas")
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT v.id, p.nome, v.quantidade_vendida, v.preco_venda_total, v.lucro 
                    FROM vendas v JOIN produtos p ON v.produto_id = p.id WHERE v.usuario_id = ?
                """, (st.session_state.user_id,))
                vendas = cursor.fetchall()

            if vendas:
                for v in vendas:
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.write(f"**{v['nome']}** (Qtd: {v['quantidade_vendida']})")
                    c2.write(f"Venda: R$ {v['preco_venda_total']:.2f} | Lucro: R$ {v['lucro']:.2f}")
                    if c3.button("🗑️", key=f"del_v_{v['id']}"):
                        with get_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT produto_id, quantidade_vendida FROM vendas WHERE id = ?", (v['id'],))
                            v_info = cursor.fetchone()
                            if v_info:
                                cursor.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?", (v_info['quantidade_vendida'], v_info['produto_id']))
                                cursor.execute("DELETE FROM vendas WHERE id = ?", (v['id'],))
                                conn.commit()
                        st.rerun()
            else:
                st.info("Nenhuma venda registrada.")

    # --- ABA 3: GASTOS ---
    with aba_gast:
        st.subheader("Registro de Gastos")
        col_g1, col_g2 = st.columns([1, 2])

        with col_g1:
            g_cat = st.selectbox("Categoria", ["Água", "Energia", "IPTU", "Entrega", "Aluguel", "Outros"])
            g_desc = st.text_input("Descrição do Gasto")
            g_val = st.text_input("Valor (R$)", value="0.00")

            if st.button("Salvar Gasto", use_container_width=True):
                try:
                    val_gasto = float(g_val.replace(",", "."))
                    if not g_desc:
                        st.error("Informe a descrição.")
                    else:
                        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
                        with get_db() as conn:
                            conn.cursor().execute(
                                "INSERT INTO gastos (usuario_id, categoria, descricao, valor, data) VALUES (?, ?, ?, ?, ?)",
                                (st.session_state.user_id, g_cat, g_desc, val_gasto, data_atual)
                            )
                            conn.commit()
                        st.success("Gasto registrado!")
                        st.rerun()
                except ValueError:
                    st.error("Valor inválido.")

        with col_g2:
            st.text("Histórico de Gastos")
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, categoria, descricao, valor FROM gastos WHERE usuario_id = ?", (st.session_state.user_id,))
                gastos = cursor.fetchall()

            if gastos:
                for g in gastos:
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.write(f"**[{g['categoria']}]** {g['descricao']}")
                    c2.write(f"R$ {g['valor']:.2f}")
                    if c3.button("🗑️", key=f"del_g_{g['id']}"):
                        with get_db() as conn:
                            conn.cursor().execute("DELETE FROM gastos WHERE id = ? AND usuario_id = ?", (g['id'], st.session_state.user_id))
                            conn.commit()
                        st.rerun()
            else:
                st.info("Nenhum gasto registrado.")

    # --- ABA 4: RELATÓRIO ---
    with aba_rel:
        st.subheader("Resumo Financeiro")
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(preco_venda_total), SUM(lucro) FROM vendas WHERE usuario_id = ?", (st.session_state.user_id,))
            res_v = cursor.fetchone()
            tot_v = res_v[0] if res_v and res_v[0] else 0.0
            luc_b = res_v[1] if res_v and res_v[1] else 0.0

            cursor.execute("SELECT SUM(valor) FROM gastos WHERE usuario_id = ?", (st.session_state.user_id,))
            res_g = cursor.fetchone()
            tot_g = res_g[0] if res_g and res_g[0] else 0.0

        luc_l = luc_b - tot_g

        st.metric("💰 Faturamento Total com Vendas", f"R$ {tot_v:.2f}")
        st.metric("📈 Lucro Bruto", f"R$ {luc_b:.2f}")
        st.metric("💸 Total de Gastos", f"R$ {tot_g:.2f}")
        st.divider()
        st.metric("💎 LUCRO LÍQUIDO", f"R$ {luc_l:.2f}")
