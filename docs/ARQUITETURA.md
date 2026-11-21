# CENTRAL INTELIGENTE DE YOUTUBE SHORTS — ARQUITETURA DE SISTEMA

## 1. Visão Geral da Arquitetura
A plataforma foi concebida para operar uma rede de aproximadamente **20 canais independentes** no YouTube Shorts, mantendo um banco inicial de **2.000 a 3.000 referências** categorizadas e operando com um armazenamento central em **Google Drive de 5 TB**.

O princípio basilar da engenharia é: **o computador local não é depósito de vídeos**. O computador atua como nó de controle e interface administrativa. Todo material processado é transferido para o Google Drive e o buffer temporário local é eliminado.

---

## 2. Diagrama de Blocos da Solução

```mermaid
flowchart TD
    subgraph Pesquisa & Catalogacao
        A1["Busca Automatizada (YouTube API / yt-dlp)"] --> A2["Cataloger (Metadados & Transcrições)"]
        A2 --> A3[("Banco Relacional: shorts_central.db")]
    end

    subgraph Inteligencia & DNA Viral
        A3 --> B1["Intelligence Engine (Gemini 4 / Flash)"]
        B1 --> B2["Mineração de Ganchos (0-3s)"]
        B1 --> B3["Estruturas Narrativas & Ritmo"]
        B2 & B3 --> B4["Playbook Viral & Padrões"]
    end

    subgraph Criacao & Producao
        B4 --> C1["Script Generator (100% Original / Zero Plágio)"]
        C1 --> C2{"Aprovação Humana Obrigatória"}
        C2 -- Aprovado --> C3["Pipeline de Renderização (FFmpeg 9.1)"]
        C3 --> C4["Legendas Dinâmicas & Reframe 9:16"]
    end

    subgraph Armazenamento & Distribuicao
        C4 --> D1["GDrive Manager (Google Drive 5 TB)"]
        D1 --> D2["13 Pastas Oficiais no Drive"]
        D1 --> D3["Limpeza Imediata do Buffer Local"]
        D2 --> E1["YouTube Distributor (20 Canais)"]
        E1 --> E2["Upload Escalonado (Staggering)"]
        E1 --> E3["Métricas & Performance Tracking"]
    end
```

---

## 3. Modelo de Dados Relacional (`shorts_central.db`)
O sistema utiliza SQLite com abstração preparada para PostgreSQL, contendo:
* **`video_references`**: Armazena as 3.000 referências (título, canal, duração, views, likes, engajamento, permissão de uso).
* **`categories`**: 15 categorias nativas (Podcasts, Esportes, Humor, Memes, Storytelling, Curiosidades, Tecnologia, etc.).
* **`content_patterns`**: Biblioteca de fórmulas de abertura (0-3s), estruturas narrativas e elementos de retenção.
* **`channels`**: Gerenciamento individual dos 20 canais (nicho, público, tom, estilo de edição, frequência).
* **`scripts`**: Roteiros originais gerados pela IA, com controle de status e aprovação humana obrigatória.
* **`production_pipeline`**: Fila de renderização, links do Drive e rastreamento de etapas.
* **`publications`**: Histórico de publicações por canal, agendamentos e IDs de vídeos postados.
* **`audit_logs`**: Logs detalhados de operações do Drive, YouTube e erros do sistema.

---

## 4. Política de Armazenamento no Google Drive 5 TB
* O acesso é feito via Google Drive API v3 oficial (OAuth 2.0).
* O script cria automaticamente as 13 pastas da `CENTRAL SHORTS`:
  - `00 - Banco de referências`
  - `01 - Vídeos catalogados`
  - `02 - Vídeos autorizados`
  - `03 - Vídeos em análise`
  - `04 - Inteligência e padrões`
  - `05 - Roteiros e ideias`
  - `06 - Produção`
  - `07 - Vídeos finalizados`
  - `08 - Thumbnails e materiais`
  - `09 - Relatórios e métricas`
  - `10 - Canais` (contendo 20 subpastas: Canal 01 até Canal 20)
  - `11 - Arquivos temporários`
  - `12 - Backups e documentação`
* **Limpeza Automática:** Nenhum vídeo permanece no disco local após o upload confirmado no Google Drive.
* **Não-Destruição:** A plataforma possui política estrita de não deletar arquivos do Drive sem confirmação explícita do usuário.
