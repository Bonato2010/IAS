# VIAGEM / IAS — Central de Inteligência de Conteúdo

> **IAS (Intelligence & Automation System)**: Plataforma profissional de inteligência artificial multimodal para pesquisa, análise crítica, mineração de padrões virais e produção automatizada de YouTube Shorts em escala (200.000+ referências) integrada a 20 canais e Google Drive de 5 TB.

---

## 🏛️ 1. Arquitetura do Sistema

```
VIAGEM / CENTRAL SHORTS
├── agents/                       # SISTEMA MULTIAGENTE DE PRODUÇÃO E CONSELHO
│   ├── base_agent.py             # Interface base, memória de trabalho e métricas técnicas
│   ├── specialists.py            # Os 9 Especialistas + Agente Diretor de Conteúdo
│   ├── research_agents.py        # Central Multiagente de Pesquisadores Especializados
│   └── company.py                # Mesa Redonda, deliberação e coordenação do conselho
├── core/                         # MOTORES E PIPELINES PRINCIPAIS
│   ├── research_pipeline.py      # Algoritmo de Pesquisa e Aprendizado (200.000+ Shorts)
│   ├── critical_analysis.py      # Módulo Profissional de Análise Crítica
│   ├── podcast_deep_analyzer.py  # Ingestão e segmentação inteligente de podcasts longos
│   ├── large_scale_cataloger.py  # Catálogo em larga escala (Zero consumo de HD local)
│   ├── editorial_profiles.py     # As 10 Personalidades Editoriais e combinador híbrido
│   ├── experimentation.py        # Laboratório de Experimentos A/B com feedback loop
│   ├── gdrive_manager.py         # Repositório oficial Google Drive 5 TB (13 pastas)
│   ├── video_editor.py           # Renderização vertical 9:16 com legendas karaoke (.ass)
│   ├── channel_manager.py        # Gerenciamento independente dos 20 canais
│   └── script_generator.py       # Gerador de roteiros 100% originais e livres de plágio
├── memory/                       # INTELIGÊNCIA COMPARTILHADA
│   └── central_memory.py         # Memória Central, Nós de Conhecimento e Padrões Virais
├── database/                     # CAMADA RELACIONAL E ESTRUTURADA
│   ├── schema.sql                # 16 tabelas relacionais completas
│   └── shorts_central.db         # Banco SQLite de alta performance
├── web/                          # DASHBOARD OPERACIONAL INTEGRADO
│   ├── app.py                    # Servidor REST API FastAPI
│   └── static/index.html         # Interface corporativa profissional
├── credentials/                  # ISOLAMENTO CRÍTICO DE SEGREDOS (Git-Ignored)
│   ├── gdrive_credentials.json   # Credenciais OAuth do Google Cloud (não versionado)
│   └── gdrive_token.json         # Token de acesso permanente (não versionado)
└── workspace/                    # Buffer de processamento temporário (limpo automaticamente)
```

---

## 🌿 2. Estrutura de Branches do Git

O projeto adota a estratégia profissional de branching:

* **`main`**: Versão estável, homologada e validada para operação. Somente recebe merges de `develop` após testes aprovados.
* **`develop`**: Branch ativa de desenvolvimento contínuo, integração de novos agentes, algoritmos e funcionalidades.

### Fluxo de Trabalho (Workflow):
```bash
# 1. Trabalhar sempre a partir da develop
git checkout develop

# 2. Criar branch de feature quando necessário
git checkout -b feature/nome-da-funcionalidade

# 3. Testar e integrar de volta na develop
git checkout develop
git merge feature/nome-da-funcionalidade

# 4. Homologação para a main
git checkout main
git merge develop
```

---

## 👥 3. O Conselho Editorial e os Agentes Especializados

A operação conta com **10 agentes especializados** com instruções, critérios técnicos e memória de trabalho própria:

1. **Agente de Esportes & Futebol:** Entrevistas, bastidores de atletas, polêmicas e debates de torcida.
2. **Agente de Podcasts:** Mineração de momentos de ouro com independência de contexto e frases de impacto.
3. **Agente de Humor & Zoeira:** Timing cômico, quebra de expectativas e compatibilidade com memes.
4. **Agente de Storytelling:** Estrutura em 3 atos (premissa, conflito, clímax e reviravolta).
5. **Agente de Retenção:** Análise dos primeiros 3 segundos, ritmo de fala (WPM) e combate à queda de retenção.
6. **Agente de Edição:** Enquadramento 9:16, zooms enfáticos a cada 3.2s e legendas animadas em karaoke.
7. **Agente de Público & Demografia:** Adequação linguística, faixa etária e tom por nicho.
8. **Agente de Tendências:** Radar de formatos virais perenes vs modismos passageiros.
9. **Agente de Originalidade:** **Garante zero plágio**, checando similaridade com referências e exigindo agregação de valor.
10. **Agente Diretor de Conteúdo:** Preside a Mesa Redonda, pondera os votos e emite o veredito final.

---

## 🔍 4. Algoritmo de Pesquisa em Larga Escala (200.000+ Shorts)

O pipeline opera sem armazenar gigabytes de vídeos brutos no computador local:

```
PESQUISA ➔ DESCOBERTA ➔ CATALOGAÇÃO ➔ VALIDAÇÃO ➔ ANÁLISE MULTIMODAL
   ➔ EXTRAÇÃO DE PADRÕES ➔ MEMÓRIA CENTRAL ➔ APRENDIZADO ➔ GERAÇÃO DE IDEIAS ➔ PRODUÇÃO
```

* **Zero Acúmulo no Disco:** Somente metadados, ganchos e transcrições estruturadas são armazenados no banco local. Vídeos e assets brutos residem exclusivamente no **Google Drive de 5 TB**.
* **Controle de Taxa (Rate Limits):** Filas inteligentes com backoff exponencial e detecção de duplicatas para proteger cotas de API.

---

## ☁️ 5. Google Drive 5 TB — As 13 Pastas Mandatórias

O repositório oficial na nuvem organiza todos os ativos nas seguintes pastas:
1. `00 - Banco de referências`
2. `01 - Vídeos catalogados`
3. `02 - Vídeos autorizados`
4. `03 - Vídeos em análise`
5. `04 - Inteligência e padrões`
6. `05 - Roteiros e ideias`
7. `06 - Produção`
8. `07 - Vídeos finalizados`
9. `08 - Thumbnails e materiais`
10. `09 - Relatórios e métricas`
11. `10 - Canais` *(contendo as 20 subpastas dos canais)*
12. `11 - Arquivos temporários`
13. `12 - Backups e documentação`

---

## 🚀 6. Como Executar a Operação

### Iniciar o Dashboard Web:
Execute no terminal ou dê dois cliques em `ABRIR CENTRAL SHORTS.bat`:
```powershell
python run_dashboard.py
```
Acesse no navegador: `http://127.0.0.1:8000`

### Conectar o Google Drive 5 TB:
Dê dois cliques no atalho `CONECTAR MEU GOOGLE DRIVE.bat` na sua pasta do Desktop e autorize a conta Google.
