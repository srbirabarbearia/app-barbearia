import streamlit as st
import pandas as pd
import datetime
import qrcode
from io import BytesIO
from PIL import Image

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ATIVAÇÃO DO PWA (APLICATIVO INSTALÁVEL)
# ==============================================================================
st.set_page_config(page_title="Barbearia Club Premium", page_icon="💈", layout="centered")

# Chamada do manifesto e service worker para ativação do PWA no celular
pwa_setup = """
<link rel="manifest" href="./manifest.json">
<script>
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js');
    }
</script>
"""
st.components.v1.html(pwa_setup, height=0)

# ==============================================================================
# INICIALIZAÇÃO DO BANCO DE DADOS EM MEMÓRIA (SESSION STATE)
# ==============================================================================
if 'users' not in st.session_state:
    st.session_state['users'] = {
        'admin': {'password': 'admin123', 'email': 'admin@barbearia.com', 'is_admin': True, 'nome': 'Administrador'}
    }

if 'agendamentos' not in st.session_state:
    st.session_state['agendamentos'] = []

if 'chat' not in st.session_state:
    st.session_state['chat'] = []

if 'config_servicos' not in st.session_state:
    st.session_state['config_servicos'] = {
        "Corte Simples": 40.0,
        "Barba Completa": 30.0,
        "Combo (Cabelo + Barba)": 65.0
    }

if 'config_horarios' not in st.session_state:
    st.session_state['config_horarios'] = {
        'abertura': datetime.time(9, 0),
        'fechamento': datetime.time(19, 0),
        'intervalo': 30
    }

if 'config_clube' not in st.session_state:
    st.session_state['config_clube'] = {
        'nome': 'Plano VIP Mensal',
        'valor': 119.90,
        'beneficios': '• Cortes ilimitados no mês\n• 1 Barba inclusa\n• 10% de desconto em produtos'
    }

if 'config_instrucoes' not in st.session_state:
    st.session_state['config_instrucoes'] = "Seja bem-vindo! Chegue com 5 minutos de antecedência. Cancelamentos só serão aceitos com até 2 horas de aviso prévio."

if 'logged_user' not in st.session_state:
    st.session_state['logged_user'] = None

# ==============================================================================
# CONFIGURAÇÕES DO ADMINISTRADOR (BARRA LATERAL - ÍCONE DE ENGRENAGEM)
# ==============================================================================
with st.sidebar:
    st.write("## ⚙️ Configurações do Sistema")
    
    if st.session_state['logged_user'] and st.session_state['users'][st.session_state['logged_user']].get('is_admin'):
        with st.expander("🔑 Alterar Senha do ADM"):
            nova_senha_adm = st.text_input("Nova Senha ADM", type="password", key="pwd_adm")
            confirma_senha_adm = st.text_input("Confirmar Nova Senha ADM", type="password", key="pwd_adm_conf")
            if st.button("Atualizar Senha ADM"):
                if nova_senha_adm == confirma_senha_adm and nova_senha_adm != "":
                    st.session_state['users']['admin']['password'] = nova_senha_adm
                    st.success("Senha do administrador alterada com sucesso!")
                else:
                    st.error("As senhas não coincidem ou estão vazias.")
                    
        with st.expander("🕒 Horários e Intervalos"):
            st.session_state['config_horarios']['abertura'] = st.time_input("Horário de Abertura", st.session_state['config_horarios']['abertura'])
            st.session_state['config_horarios']['fechamento'] = st.time_input("Horário de Fechamento", st.session_state['config_horarios']['fechamento'])
            
            # LINHA REPARADA: Lista adicionada e vírgula extra removida com sucesso
            st.session_state['config_horarios']['intervalo'] = st.selectbox(
                "Intervalo de Atendimento",
                [15, 30, 45, 60], 
                index=1,
                format_func=lambda x: f"{x} minutos"
            )
            
        with st.expander("💈 Tabela de Serviços e Preços"):
            for servico, preco in list(st.session_state['config_servicos'].items()):
                novo_preco = st.number_input(f"Preço: {servico} (R$)", value=float(preco), step=5.0, key=f"srv_{servico}")
                st.session_state['config_servicos'][servico] = novo_preco
                
        with st.expander("🏆 Configuração do Clube de Assinatura"):
            st.session_state['config_clube']['nome'] = st.text_input("Nome do Plano", st.session_state['config_clube']['nome'])
            st.session_state['config_clube']['valor'] = st.number_input("Mensalidade (R$)", value=st.session_state['config_clube']['valor'], step=10.0)
            st.session_state['config_clube']['beneficios'] = st.text_area("Benefícios do Clube", st.session_state['config_clube']['beneficios'])
            
        with st.expander("📝 Caixa de Instruções aos Clientes"):
            st.session_state['config_instrucoes'] = st.text_area("Mensagem de Aviso", st.session_state['config_instrucoes'])
    else:
        st.info("Faça login como administrador para liberar as ferramentas de customização.")
        
    if st.session_state['logged_user']:
        st.write("---")
        st.write(f"Usuário ativo: **{st.session_state['logged_user']}**")
        if st.button("🚪 Sair do Aplicativo", use_container_width=True):
            st.session_state['logged_user'] = None
            st.rerun()

# ==============================================================================
# FUNÇÃO AUXILIAR: GERADOR DE QR CODE
# ==============================================================================
def gerar_qr_code(texto_dados):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(texto_dados)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==============================================================================
# TELA DE LOGIN E CADASTRO / REDEFINIÇÃO DE SENHA
# ==============================================================================
if st.session_state['logged_user'] is None:
    st.title("💈 Barbearia Club Premium")
    st.subheader("Agende seu horário com praticidade")
    
    aba_login, aba_cadastro = st.tabs(["🔐 Entrar na Conta", "📝 Criar Nova Conta"])
    
    with aba_login:
        user_input = st.text_input("Nome de Usuário (Login)", key="login_user").strip()
        pass_input = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            if user_input in st.session_state['users'] and st.session_state['users'][user_input]['password'] == pass_input:
                st.session_state['logged_user'] = user_input
                st.success(f"Bem-vindo de volta, {user_input}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                
        with st.expander("🛟 Esqueci minha senha / Redefinir"):
            st.write("Confirme seus dados para atualizar suas credenciais:")
            redef_user = st.text_input("Confirmar Usuário", key="ref_u")
            redef_email = st.text_input("Confirmar E-mail Cadastrado", key="ref_e")
            
            if redef_user in st.session_state['users'] and st.session_state['users'][redef_user]['email'] == redef_email:
                st.success("Dados validados! Digite sua nova senha:")
                nova_senha = st.text_input("Nova Senha", type="password", key="new_p")
                confirma_nova = st.text_input("Confirmar Nova Senha", type="password", key="new_p_c")
                
                if st.button("Salvar Nova Senha", use_container_width=True):
                    if nova_senha == confirma_nova and nova_senha != "":
                        st.session_state['users'][redef_user]['password'] = nova_senha
                        st.success("Senha redefinida com sucesso! Prossiga para o Login acima.")
                    else:
                        st.error("As senhas informadas não coincidem.")
            elif redef_user != "" or redef_email != "":
                st.error("Combinação de usuário e e-mail inválida.")

    with aba_cadastro:
        st.write("### Ficha de Cadastro do Cliente")
        cad_user = st.text_input("Escolha um Nome de Usuário", key="cad_u").strip()
        cad_nome = st.text_input("Nome Completo", key="cad_n")
        cad_senha = st.text_input("Crie uma Senha", type="password", key="cad_p")
        cad_email = st.text_input("E-mail", key="cad_em")
        cad_fone = st.text_input("Telefone / WhatsApp", key="cad_ph")
        
        if st.button("Finalizar Meu Cadastro", use_container_width=True):
            if cad_user == "" or cad_senha == "" or cad_email == "":
                st.error("Campos Usuário, Senha e E-mail são obrigatórios.")
            elif cad_user in st.session_state['users']:
                st.error("Este nome de usuário já está cadastrado.")
            else:
                st.session_state['users'][cad_user] = {
                    'password': cad_senha,
                    'email': cad_email,
                    'nome': cad_nome,
                    'telefone': cad_fone,
                    'is_admin': False,
                    'data_cadastro': datetime.date.today().strftime("%d/%m/%Y")
                }
                st.success("Conta criada! Alterne para a aba 'Entrar na Conta'.")

# ==============================================================================
# PAINEL DO CLIENTE LOGADO
# ==============================================================================
elif not st.session_state['users'][st.session_state['logged_user']].get('is_admin'):
    st.title(f"Olá, {st.session_state['users'][st.session_state['logged_user']]['nome']}! 👋")
