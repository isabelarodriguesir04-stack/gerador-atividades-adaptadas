from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import date, datetime
import sqlite3
import hashlib
import re

app = FastAPI(
    title="Sistema de Atividades Pedagógicas Adaptadas",
    description="Exercícios com conteúdo conteudista direto, sem metalinguagem sobre a aula.",
    version="1.0.0"
)

def init_db():
    conn = sqlite3.connect("sistema_pedagogico.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lotes_atividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_email TEXT NOT NULL,
            disciplina TEXT NOT NULL,
            serie_turma TEXT NOT NULL,
            tema TEXT NOT NULL,
            descricao_aula TEXT NOT NULL,
            diagnostico_codigo TEXT NOT NULL,
            densidade_visual TEXT NOT NULL,
            total_atividades INTEGER NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

DIAGNOSTICOS = [
    {"codigo": "TEA_1", "nome": "TEA - Nível 1 de Suporte", "diretriz": "Enunciados diretos, sem metáforas e com foco em factos objetivos."},
    {"codigo": "TEA_2", "nome": "TEA - Nível 2 de Suporte", "diretriz": "Apoio visual fotográfico direto, redução de alternativas distratoras e frases curtas afirmativas."},
    {"codigo": "TEA_3", "nome": "TEA - Nível 3 de Suporte", "diretriz": "Pareamento concreto, palavras isoladas e identificação imediata."},
    {"codigo": "TDAH", "nome": "TDAH", "diretriz": "Etapas curtas, palavras-chave em negrito e caixas de resposta bem delimitadas."},
    {"codigo": "DI", "nome": "Deficiência Intelectual", "diretriz": "Vocabulário direto, correspondência de termos simples e associação visual clara."},
    {"codigo": "SINDROME_DOWN", "nome": "Síndrome de Down", "diretriz": "Tipografia ampliada, grande espaçamento para escrita e apoio imagético nítido."},
    {"codigo": "TOD", "nome": "Transtorno Opositivo Desafiador (TOD)", "diretriz": "Questões objetivas de escolha direta e comandos transparentes."}
]

IMAGENS_POR_DISCIPLINA = {
    "matematica": [
        ("https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=400&q=80", "Cálculo e Geometria"),
        ("https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=400&q=80", "Valores e Moeda"),
        ("https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=400&q=80", "Partes e Frações"),
        ("https://images.unsplash.com/photo-1508962914676-134849a727f0?auto=format&fit=crop&w=400&q=80", "Medição de Tempo"),
        ("https://images.unsplash.com/photo-1596495578065-6e0763fa1178?auto=format&fit=crop&w=400&q=80", "Contagem de Elementos")
    ],
    "ciencias": [
        ("https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=400&q=80", "Estrutura e Matéria"),
        ("https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=400&q=80", "Corpos Celestes"),
        ("https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=400&q=80", "Ciclo Natural"),
        ("https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&w=400&q=80", "Organismos Vivos"),
        ("https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?auto=format&fit=crop&w=400&q=80", "Vegetação e Solo")
    ],
    "historia": [
        ("https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=400&q=80", "Monumentos e Registos"),
        ("https://images.unsplash.com/photo-1599739291060-4578e77dac5d?auto=format&fit=crop&w=400&q=80", "Civilizações Antigas"),
        ("https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=400&q=80", "Escrita e Arquivo"),
        ("https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=400&q=80", "Sociedade e Cultura"),
        ("https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80", "Património Histórico")
    ],
    "geografia": [
        ("https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=400&q=80", "Representação Cartográfica"),
        ("https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=400&q=80", "Relevo e Solo"),
        ("https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=400&q=80", "Espaço Geográfico"),
        ("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80", "Bacias Hidrográficas"),
        ("https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=400&q=80", "Zonas Climáticas")
    ],
    "portugues": [
        ("https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=400&q=80", "Leitura e Vocabulário"),
        ("https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=400&q=80", "Estrutura Frásica"),
        ("https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=400&q=80", "Classes de Palavras"),
        ("https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=400&q=80", "Gêneros Textuais"),
        ("https://images.unsplash.com/photo-1471107340929-a87cd0f5b5f3?auto=format&fit=crop&w=400&q=80", "Ortografia Aplicada")
    ],
    "geral": [
        ("https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=400&q=80", "Conceito Aplicado"),
        ("https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&w=400&q=80", "Análise de Dados"),
        ("https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=400&q=80", "Observação Prática"),
        ("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=400&q=80", "Estrutura Técnica"),
        ("https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=400&q=80", "Comparação de Elementos")
    ]
}

def extrair_termos(descricao: str, tema: str):
    """Extrai palavras reais do conteúdo informado pelo professor."""
    palavras = re.findall(r'\b[A-Za-zÀ-ÿ]{4,}\b', descricao)
    stopwords = {"para", "como", "sobre", "pela", "pelo", "mais", "esse", "essa", "este", "esta", "onde", "qual", "quais", "fazer", "saber"}
    filtradas = [p.capitalize() for p in palavras if p.lower() not in stopwords]
    
    if len(filtradas) < 4:
        filtradas.extend([tema, "Origem", "Função", "Processo", "Estrutura"])
    return filtradas[:6]

def gerar_exercicios_especificos(disciplina: str, tema: str, descricao: str, diretriz: str, densidade: str):
    termos = extrair_termos(descricao, tema)
    t1, t2, t3, t4 = termos[0], termos[1], termos[2], termos[3]
    disc_lower = disciplina.lower()

    if "matem" in disc_lower:
        fotos = IMAGENS_POR_DISCIPLINA["matematica"]
        itens = [
            ("Operação com Valores Reais", f"<p class='text-sm mb-2'>Resolva o cálculo prático relacionado a <strong>{tema}</strong>:</p><div class='p-3 bg-blue-50 border rounded font-mono text-base font-bold inline-block'>&nbsp;&nbsp;358<br>+ 174<br>------<br>[ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ]</div>"),
            ("Problema de Quantidade e Subtração", f"<p class='text-sm mb-2'>Em um lote inicial havia <strong>250</strong> unidades de <strong>{t1}</strong>. Foram utilizadas <strong>85</strong> unidades. Quantas restam?</p><p class='text-sm font-semibold'>Cálculo: 250 - 85 = [ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ] unidades.</p>"),
            ("Frações e Partes do Todo", f"<p class='text-sm mb-2'>Um conjunto de <strong>{tema}</strong> foi dividido em <strong>6 partes iguais</strong>. Foram destacadas <strong>2 partes</strong>.</p><p class='text-sm font-bold text-blue-900'>Escreva a fração: [ &nbsp;&nbsp; ] / [ &nbsp;&nbsp; ]</p>"),
            ("Multiplicação por Grupos", f"<p class='text-sm mb-2'>Existem <strong>4 caixas</strong> com <strong>12</strong> itens de <strong>{t2}</strong> em cada uma. Qual o total?</p><div class='space-y-1 text-sm'><label class='flex gap-2'><input type='checkbox'> (A) 4 + 12 = 16</label><label class='flex gap-2'><input type='checkbox'> (B) 4 × 12 = 48</label></div>"),
            ("Cálculo Monetário e Troco", f"<p class='text-sm mb-2'>O valor de um item de <strong>{tema}</strong> custa <strong>R$ 37,00</strong>. O pagamento foi feito com uma nota de <strong>R$ 50,00</strong>.</p><p class='text-sm font-bold'>Troco a devolver: R$ [ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ],00</p>"),
            ("Medição e Perímetro", f"<p class='text-sm mb-2'>Calcule o perímetro de um espaço retangular de <strong>{tema}</strong> com <strong>8 metros</strong> de comprimento e <strong>4 metros</strong> de largura:</p><p class='text-xs bg-slate-100 p-1.5 rounded mb-1'>Soma: 8 + 4 + 8 + 4</p><p class='text-sm font-bold'>Perímetro total: [ &nbsp;&nbsp;&nbsp;&nbsp; ] metros.</p>"),
            ("Divisão Exata", f"<p class='text-sm mb-2'>Divida <strong>45</strong> elementos de <strong>{t3}</strong> igualmente entre <strong>5 grupos</strong>:</p><p class='text-sm font-semibold'>45 ÷ 5 = [ &nbsp;&nbsp;&nbsp;&nbsp; ] elementos por grupo.</p>"),
            ("Ordenação Numérica Direta", f"<p class='text-sm mb-2'>Coloque os valores de <strong>{tema}</strong> em ordem crescente (do menor para o maior): <strong>84, 19, 105, 52</strong>.</p><p class='text-sm font-bold text-blue-800'>Ordem: ___ < ___ < ___ < ___</p>"),
            ("Identificação Geométrica", f"<p class='text-sm mb-2'>Indique quantos lados e vértices possui uma figura plana com a forma de <strong>{t4}</strong>:</p><p class='text-sm'>Número de lados: _______ &nbsp;|&nbsp; Número de vértices: _______</p>"),
            ("Sequência Numérica Lógica", f"<p class='text-sm mb-2'>Descubra o padrão e complete os dois números que faltam: <strong>6, 12, 18, [ &nbsp;&nbsp; ], 30, [ &nbsp;&nbsp; ]</strong>.</p><p class='text-xs text-slate-500'>Regra da sequência: múltiplos de 6.</p>")
        ]
    else:
        # Outras disciplinas (História, Ciências, Geografia, Língua Portuguesa...)
        if "hist" in disc_lower:
            fotos = IMAGENS_POR_DISCIPLINA["historia"]
        elif "cien" in disc_lower or "biol" in disc_lower:
            fotos = IMAGENS_POR_DISCIPLINA["ciencias"]
        elif "geog" in disc_lower:
            fotos = IMAGENS_POR_DISCIPLINA["geografia"]
        elif "port" in disc_lower or "ling" in disc_lower:
            fotos = IMAGENS_POR_DISCIPLINA["portugues"]
        else:
            fotos = IMAGENS_POR_DISCIPLINA["geral"]

        itens = [
            (f"Característica Essencial de {tema}", f"<p class='text-sm mb-2'>Em relação a <strong>{tema}</strong>, qual das afirmações descreve corretamente a função de <strong>{t1}</strong>?</p><div class='space-y-1.5 text-sm'><label class='flex gap-2'><input type='checkbox'> (A) Atua diretamente como elemento fundamental no processo de {t1}.</label><label class='flex gap-2'><input type='checkbox'> (B) Não possui nenhuma relação com {t2} ou com {tema}.</label></div>"),
            ("Associação Conceitual de Termos", f"<p class='text-sm mb-2'>Relacione os conceitos de <strong>{tema}</strong> com as suas definições corretas:</p><div class='grid grid-cols-2 gap-3 text-xs bg-slate-50 p-2.5 border rounded'><div>1. <strong>{t1}</strong><br>2. <strong>{t2}</strong><br>3. <strong>{t3}</strong></div><div>( &nbsp; ) Estrutura ligada a {t3}<br>( &nbsp; ) Elemento principal de {t1}<br>( &nbsp; ) Fator de transformação de {t2}</div></div>"),
            ("Preenchimento com Termos Específicos", f"<div class='inline-block bg-blue-50 border border-blue-200 text-blue-900 px-2.5 py-0.5 rounded text-xs font-semibold mb-2'>Banco: [ {t1} ] &nbsp;|&nbsp; [ {t2} ] &nbsp;|&nbsp; [ {t3} ]</div><p class='text-sm leading-relaxed'>No estudo de <strong>{tema}</strong>, o elemento conhecido como ______________ atua em conjunto com ______________ para a manutenção de ______________.</p>"),
            ("Análise Direta de Fatos (V ou F)", f"<p class='text-sm mb-2'>Julgue as afirmações sobre <strong>{tema}</strong> em <strong>(V)</strong> Verdadeiro ou <strong>(F)</strong> Falso:</p><div class='space-y-1 text-sm'><p>[ &nbsp; ] <strong>{t1}</strong> foi um elemento determinante para o desenvolvimento de {tema}.</p><p>[ &nbsp; ] <strong>{t2}</strong> não produziu impactos nem consequências observáveis.</p><p>[ &nbsp; ] É possível comprovar os efeitos de <strong>{t3}</strong> através de evidências materiais ou científicas.</p></div>"),
            ("Sequenciamento Cronológico / Causal", f"<p class='text-sm mb-2'>Numere de 1 a 3 a ordem em que os eventos de <strong>{tema}</strong> ocorrem:</p><div class='space-y-1 text-sm'><p>( &nbsp; ) Ocorrência e atuação de <strong>{t1}</strong>.</p><p>( &nbsp; ) Consequência direta sobre <strong>{t2}</strong>.</p><p>( &nbsp; ) Consolidação final observada em <strong>{t3}</strong>.</p></div>"),
            ("Identificação de Elemento Incompatível", f"<p class='text-sm mb-2'>Circule o único termo do quadro que <strong>NÃO</strong> pertence ao contexto de <strong>{tema}</strong>:</p><div class='p-2 bg-slate-50 border border-dashed rounded text-center text-xs font-bold tracking-wider'>{t1.upper()} &nbsp;&nbsp;•&nbsp;&nbsp; {t2.upper()} &nbsp;&nbsp;•&nbsp;&nbsp; TERMO DESCONEXO &nbsp;&nbsp;•&nbsp;&nbsp; {t3.upper()}</div>"),
            ("Causa e Consequência Direta", f"<p class='text-sm mb-1'><strong>Causa:</strong> Presença e desenvolvimento de <strong>{t1}</strong> em {tema}.</p><p class='text-sm border-b border-slate-300 pb-1'><strong>Consequência imediata:</strong> ____________________________________________________________________</p>"),
            ("Comparação Estruturada", f"<p class='text-sm mb-2'>Indique uma característica marcante de cada elemento de <strong>{tema}</strong>:</p><div class='grid grid-cols-2 gap-2 text-xs'><div class='p-2 border rounded bg-slate-50'><strong>{t1}:</strong><br>______________________________</div><div class='p-2 border rounded bg-slate-50'><strong>{t2}:</strong><br>______________________________</div></div>"),
            ("Localização de Função", f"<p class='text-sm mb-2'>Qual a importância de <strong>{t4}</strong> para o conjunto de <strong>{tema}</strong>?</p><div class='space-y-1 text-sm'><label class='flex gap-2'><input type='checkbox'> Garantir a estabilidade e funcionamento de {t1}.</label><label class='flex gap-2'><input type='checkbox'> Impedir qualquer manifestação de {t2}.</label></div>"),
            ("Síntese Conceitual Factual", f"<p class='text-sm mb-2'>Com base nos conceitos de <strong>{t1}</strong> e <strong>{t2}</strong>, complete a definição conclusiva:</p><div class='p-3 border rounded text-xs bg-slate-50 leading-relaxed'>O conceito de <strong>{tema}</strong> se define por: ________________________________________________________________________________________________________________________________.</div>")
        ]

    cards_html = ""
    for idx, (titulo, corpo) in enumerate(itens, start=1):
        tem_imagem = (densidade == "MAIS_IMAGENS") or (densidade == "PADRAO" and idx % 2 != 0)
        bloco_imagem = ""

        if tem_imagem:
            foto_url, foto_legenda = fotos[(idx - 1) % len(fotos)]
            bloco_imagem = f"""
            <div class="w-36 bg-white border border-slate-300 rounded-lg p-2 flex flex-col items-center justify-center text-center flex-shrink-0 shadow-sm">
              <img src="{foto_url}" alt="Foto real de {foto_legenda}" class="w-full h-20 object-cover rounded mb-1 border border-slate-200">
              <span class="text-[10px] text-blue-950 font-bold uppercase tracking-tight leading-tight">{foto_legenda}</span>
              <span class="text-[9px] text-emerald-700 font-semibold mt-0.5">Suporte Visual</span>
            </div>
            """

        cards_html += f"""
        <div class="page-card bg-white p-4 rounded-xl border border-slate-300 shadow-sm flex gap-4 items-start">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="bg-blue-700 text-white text-xs font-bold px-2 py-0.5 rounded-full">Questão {idx}</span>
              <h2 class="text-sm font-bold text-slate-900">{titulo}</h2>
            </div>
            <p class="text-[11px] text-slate-500 italic mb-2 bg-slate-50 px-2 py-1 rounded border border-slate-200">
              Adaptação NEE: {diretriz}
            </p>
            {corpo}
          </div>
          {bloco_imagem}
        </div>
        """
    return cards_html

@app.get("/cadastro", response_class=HTMLResponse)
async def tela_cadastro(erro: str = ""):
    alerta = f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{erro}</div>' if erro else ""
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"><title>Registo</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-slate-100 min-h-screen flex items-center justify-center p-6">
      <div class="bg-white p-8 rounded-xl shadow-md max-w-md w-full border border-slate-200">
        <h1 class="text-2xl font-bold text-blue-700 mb-2">Novo Professor</h1>
        <p class="text-xs text-slate-500 mb-6">Registo restrito a maiores de 18 anos (RN-01).</p>
        {alerta}
        <form action="/cadastro" method="POST" class="space-y-4">
          <div><label class="block text-sm font-semibold text-slate-700 mb-1">Nome Completo *</label><input type="text" name="nome" required class="w-full px-3 py-2 border rounded-lg"></div>
          <div><label class="block text-sm font-semibold text-slate-700 mb-1">E-mail *</label><input type="email" name="email" required class="w-full px-3 py-2 border rounded-lg"></div>
          <div><label class="block text-sm font-semibold text-slate-700 mb-1">Palavra-passe *</label><input type="password" name="senha" required class="w-full px-3 py-2 border rounded-lg"></div>
          <div><label class="block text-sm font-semibold text-slate-700 mb-1">Data de Nascimento (RN-01) *</label><input type="date" name="data_nascimento" required class="w-full px-3 py-2 border rounded-lg"></div>
          <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg shadow">Concluir Registo</button>
        </form>
      </div>
    </body>
    </html>
    """

@app.post("/cadastro", response_class=HTMLResponse)
async def processar_cadastro(nome: str = Form(...), email: str = Form(...), senha: str = Form(...), data_nascimento: str = Form(...)):
    try:
        nasc = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
    except ValueError:
        return await tela_cadastro(erro="Formato de data inválido.")

    hoje = date.today()
    idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    if idade < 18:
        return await tela_cadastro(erro=f"Registo recusado (RN-01): Utilizador possui {idade} anos. Idade mínima: 18 anos.")

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    try:
        conn = sqlite3.connect("sistema_pedagogico.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO professores (nome, email, senha_hash, data_nascimento) VALUES (?, ?, ?, ?)", (nome, email, senha_hash, data_nascimento))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return await tela_cadastro(erro="Este e-mail já está registado.")

    return RedirectResponse(url="/?professor=" + email, status_code=303)

@app.get("/", response_class=HTMLResponse)
async def pagina_inicial(professor: str = "professor@escola.gov.br"):
    opcoes = "".join([f'<option value="{d["codigo"]}">{d["nome"]}</option>' for d in DIAGNOSTICOS])
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"><title>Portal do Professor - Atividades Adaptadas</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-slate-50 text-slate-900 min-h-screen font-sans">
      <header class="bg-blue-700 text-white shadow p-5">
        <div class="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 class="text-xl font-bold">Portal do Professor - Gerador de Atividades Adaptadas</h1>
            <p class="text-blue-100 text-xs mt-0.5">Questões centradas no conteúdo disciplinar com fotos reais</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="bg-blue-800 text-xs px-3 py-1 rounded-full font-semibold">{professor}</span>
            <a href="/cadastro" class="text-xs bg-white text-blue-700 px-2.5 py-1 rounded font-bold hover:bg-blue-50">Novo Registo</a>
          </div>
        </div>
      </header>

      <main class="max-w-4xl mx-auto p-6 mt-4">
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-7">
          <h2 class="text-lg font-bold text-slate-800 mb-1">Configuração do Lote de Atividades</h2>
          <p class="text-xs text-slate-500 mb-6">Insira os termos centrais do conteúdo no campo de descrição para gerar perguntas 100% conteudistas.</p>

          <form action="/gerar" method="POST" class="space-y-5">
            <input type="hidden" name="professor_email" value="{professor}">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">Disciplina *</label>
                <input type="text" name="disciplina" required placeholder="Ex.: História, Ciências, Geografia, Matemática" class="w-full px-3.5 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">Ano / Turma *</label>
                <input type="text" name="serie_turma" required placeholder="Ex.: 6º ano fundamental" class="w-full px-3.5 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">Tema da Atividade *</label>
              <input type="text" name="tema" required placeholder="Ex.: Egito Antigo, Sistema Solar, Frações, Relevo Brasileiro" class="w-full px-3.5 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">Conceitos / Palavras-chave do Conteúdo *</label>
              <textarea name="descricao_aula" rows="3" required placeholder="Digite os termos reais que devem ser cobrados nas questões. Ex.: Rio Nilo, Faraó, Pirâmides, Múmias, Agricultura, Papiro..." class="w-full px-3.5 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"></textarea>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">Perfil NEE (RF-03) *</label>
                <select name="diagnostico_codigo" required class="w-full px-3.5 py-2 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500">{opcoes}</select>
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">Densidade Visual (RF-04) *</label>
                <select name="densidade_visual" required class="w-full px-3.5 py-2 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500">
                  <option value="MAIS_IMAGENS">Mais imagens (Fotos reais nas 10 atividades - RN-04)</option>
                  <option value="PADRAO" selected>Padrão (Misto balanceado)</option>
                  <option value="MENOS_IMAGENS_TEXTO_SIMPLIFICADO">Menos imagens / Texto simplificado</option>
                </select>
              </div>
            </div>

            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg shadow transition">
              Gerar Lote com 10 Atividades Conteudistas Adaptadas
            </button>
          </form>
        </div>
      </main>
    </body>
    </html>
    """

@app.post("/gerar", response_class=HTMLResponse)
async def processar_geracao(
    professor_email: str = Form("professor@escola.gov.br"),
    disciplina: str = Form(...),
    serie_turma: str = Form(...),
    tema: str = Form(...),
    descricao_aula: str = Form(...),
    diagnostico_codigo: str = Form(...),
    densidade_visual: str = Form(...)
):
    diag = next((d for d in DIAGNOSTICOS if d["codigo"] == diagnostico_codigo), None)
    nome_diag = diag["nome"] if diag else diagnostico_codigo
    diretriz_diag = diag["diretriz"] if diag else ""

    cards_html = gerar_exercicios_especificos(disciplina, tema, descricao_aula, diretriz_diag, densidade_visual)

    conn = sqlite3.connect("sistema_pedagogico.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lotes_atividades 
        (professor_email, disciplina, serie_turma, tema, descricao_aula, diagnostico_codigo, densidade_visual, total_atividades)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (professor_email, disciplina, serie_turma, tema, descricao_aula, diagnostico_codigo, densidade_visual, 10))
    conn.commit()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8"><title>Atividades - {tema}</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
        @media print {{
          body {{ background-color: white !important; font-size: 10pt; }}
          .no-print {{ display: none !important; }}
          .page-card {{ box-shadow: none !important; border: 1px solid #cbd5e1 !important; page-break-inside: avoid; margin-bottom: 0.6rem !important; }}
        }}
      </style>
    </head>
    <body class="bg-slate-100 text-slate-900 min-h-screen p-5">
      <div class="max-w-4xl mx-auto mb-5 flex justify-between items-center no-print">
        <a href="/?professor={professor_email}" class="text-blue-600 hover:underline font-semibold text-sm">← Voltar ao Formulário</a>
        <button onclick="window.print()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-5 rounded-lg shadow text-sm">
          🖨️ Imprimir Folhas A4 / Guardar PDF
        </button>
      </div>

      <div class="max-w-4xl mx-auto space-y-3">
        <div class="bg-white p-5 rounded-xl border border-slate-300 shadow-sm">
          <div class="border-b pb-3 mb-3">
            <h1 class="text-xl font-bold text-slate-900">Atividades Adaptadas - {disciplina}</h1>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2 text-xs text-slate-600">
              <p><strong>Turma:</strong> {serie_turma}</p>
              <p><strong>Tema:</strong> {tema}</p>
              <p><strong>Perfil NEE:</strong> {nome_diag}</p>
              <p><strong>Densidade:</strong> {densidade_visual}</p>
            </div>
          </div>
          <div class="text-xs text-slate-500">
            Nome do Aluno: __________________________________________________ Data: ____/____/________
          </div>
        </div>
        {cards_html}
      </div>
    </body>
    </html>
    """