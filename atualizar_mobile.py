import os
import re

print("🔄 Iniciando correção da navegação mobile (Menu Hamburguer)...")

BASE_DIR = os.getcwd()

# --- 1. Atualizar style.css (Adiciona estilos do menu móvel) ---
css_path = os.path.join(BASE_DIR, "static/css/style.css")

# Novo CSS que reintroduz os links de forma responsiva
new_mobile_css = """
/* --- CORREÇÃO MOBILE --- */
/* Oculta os links por padrão na versão Desktop */
.nav-links { display: flex; gap: 20px; align-items: center; } 
.menu-toggle { display: none; background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; }

@media (max-width: 768px) {
    /* Mostra o botão de menu (hamburguer) */
    .menu-toggle { display: block; }
    
    /* Esconde a navegação completa */
    .nav-links {
        display: none; 
        flex-direction: column;
        position: absolute;
        top: 75px; /* Altura do header */
        left: 0;
        width: 100%;
        background: #0a0a0a; 
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }
    .nav-links.active {
        display: flex; /* Exibe ao clicar */
    }
    .nav-links a {
        width: 100%;
        padding: 15px 20px;
        text-align: left;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
}
"""

# Leitura do CSS atual para inserir a correção
try:
    with open(css_path, "r", encoding="utf-8") as f:
        style_content = f.read()
    
    # Encontra a última media query e insere o novo bloco (ou apenas anexa)
    if '/* --- CORREÇÃO MOBILE --- */' not in style_content:
        style_content += "\n" + new_mobile_css
    
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(style_content)
    print("✅ static/css/style.css atualizado com estilos do menu móvel.")

except Exception as e:
    print(f"❌ Erro ao atualizar style.css: {e}")


# --- 2. Atualizar Templates HTML (Adiciona o ícone e o JavaScript) ---

# Função para atualizar o HTML (adicionando o ícone e o script de toggle)
def update_template(filename):
    path = os.path.join(BASE_DIR, "templates", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # 1. Adiciona o botão Hamburguer no Navbar (antes do nav-links)
        if '<button class="menu-toggle"' not in html_content:
            # Encontra onde o nav-links começa e insere o botão antes
            html_content = re.sub(
                r'(<div class="nav-links">)',
                '<button class="menu-toggle" id="menu-toggle"><i class="fas fa-bars"></i></button>\n\\1',
                html_content, count=1
            )

        # 2. Adiciona o JavaScript de Toggle no final do corpo
        js_script = """
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const toggleButton = document.getElementById('menu-toggle');
        const navLinks = document.querySelector('.nav-links');
        
        if (toggleButton && navLinks) {
            toggleButton.addEventListener('click', function() {
                navLinks.classList.toggle('active');
            });
        }
    });
</script>
"""
        # Remove script anterior se existir e adiciona o novo (para evitar duplicação)
        html_content = re.sub(r'<script>.*?</script>', '', html_content, flags=re.DOTALL)
        if 'document.getElementById(\'menu-toggle\')' not in html_content:
             html_content = html_content.replace('</body>', f'{js_script}\n</body>')


        # 3. Faz o ajuste no nav-links para incluir o botão SOBRE
        if 'href="/sobre"' not in html_content:
             # Isso garante que todos os templates tenham o link SOBRE
             html_content = re.sub(
                r'(<a href="/">LOJA</a>)',
                '\\1\n                <a href="/sobre">SOBRE</a>',
                html_content, count=1
            )
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ templates/{filename} atualizado com Menu Hamburguer.")
        
    except FileNotFoundError:
        print(f"⚠️ Aviso: templates/{filename} não encontrado. Ignorando.")
    except Exception as e:
        print(f"❌ Erro ao processar templates/{filename}: {e}")

# Executa para os principais templates
update_template("index.html")
update_template("sobre.html")
update_template("admin.html")
update_template("login.html")

# --- 3. Comandos Git para Subir a Correção ---

def subir_correcao_git():
    print("\n🚀 Preparando para subir a correção (Mobile Fix) no GitHub...")
    os.system('git add .')
    os.system('git commit -m "FEAT: Implementado Menu Hamburguer para mobile (Responsividade Fix)"')
    os.system('git push')
    print("\n🎉 CORREÇÃO ENVIADA. O Render iniciará o novo deploy.")

subir_correcao_git()