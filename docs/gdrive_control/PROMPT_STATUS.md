# VANTIS — PROMPT STATUS

| Prompt | Estado | Evidência | Bloqueios |
|---|---|---|---|
| 01 Auditoria/Arquitetura | verified | Auditoria completa, contratos em docs/audit/CONTRACTS.md, mapeamento de dependências e banco consolidado. | — |
| 02 Infraestrutura/Dados | verified | SQLite WAL, 25 tabelas, migrações 001 a 007, isolamento multitenant de canais, task_queue resiliente com backoff exponencial. | — |
| 03 Agentes/Memória | verified | 10 agentes especializados sob VantisBaseAgent, LangGraph com ramificações condicionais para Portal 1 e 2, memória semântica FastEmbed isolada por canal. | — |
| 04 Pesquisa/Editorial | verified | RealYouTubeDiscoveryService via yt-dlp, governança Portal 1 no fluxo com reforço de memória, personas dos 5 primeiros canais piloto. | — |
| 05 Produção audiovisual | verified | Pipeline industrial de 10 etapas (audiovisual_pipeline.py), FFmpeg 9.1, PySceneDetect, OpenCV Smart Crop 9:16, Faster-Whisper com patch PyAV 19.0.2, Edge-TTS, legendas ASS, áudio EBU R128 (-14 LUFS) e CQ automatizado. | — |
| 06 Dashboard | verified | Interface SPA visual profissional (web/static/index.html) conectada a 78 endpoints REST (web/app.py). Visão central com KPIs reais, Portal 1, Portal 2, governança de canais, gaveta de inspeção técnica de cada canal e ausência de dados fictícios. | — |
| 07 YouTube | implemented | UploadService com trava estrita de privacyStatus: 'private', verificação obrigatória de token humano e geração de manifesto de auditoria JSON. Aguarda credenciais OAuth reais para teste live de publicação privada. | Credenciais OAuth reais de canal do usuário |
| 08 Cinco canais | verified | 5 canais piloto operacionais com identidades distintas, cadastro de rascunhos (create_channel), completude incremental, cálculo de prontidão (readiness 0-100%), seleção de canal-piloto, arquivamento e isolamento estrito de memória e finanças. Testes em test_fase11. | — |
| 09 Segurança/Testes | verified | 82 testes automatizados de regressão em 12 suítes passando com 100% de sucesso (run_all_tests.py), política de custo zero ($0.00) travada por software, ausência de credenciais hardcoded. | — |
| 10 Deploy/Operação | verified | INICIAR_CENTRAL_IAS.bat unificado, task queue com reintentos e backoff exponencial, rotas /health e /api/health reportando telemetria operacional, scripts atômicos de backup (backup_db.py) e restauração (restore_db.py) com integridade verificada, autolimpeza de temporários (cleanup_temp_files.py) e .env.example consolidado. Testes em test_fase12. | — |
| 11 Treinamento/Expansão | verified | Loop de feedback ativo com aprovação gerando vetores positivos e rejeição indexando rejected_pattern com valência negativa e isolamento estrito por canal; mapeamento e isolamento operacional comprovados para expansão dos canais 06 a 20. Testes em test_fase12. | — |
| 12 Aprendizado Audiovisual Massivo | verified | Sistema de aprendizado multimodal em larga escala (audiovisual_learning_system.py) com meta configurável (7.000+ vídeos, expansível para 200.000+), deduplicação por fingerprint multimodal com tolerância temporal de 1.5s, teto anti-monopólio por criador (máx 50 vídeos), progressão estrita de 5 etapas (descoberto, metadados, transcrição WPM/gancho 0-3s, áudio EBU R128/clareza vocal, visual cortes/min/9:16 vertical), biblioteca de conhecimento editorial com scores logarítmicos de confiança e amarração a evidence_video_ids, isolamento multitenant dos 5 canais piloto com polinização cruzada controlada, checkpoints resilientes de lote e health score de auditoria. 11 testes em test_fase13. | — |
| 13 Correção Estrutural e Aprendizado Real | verified | Eliminação de dados/métricas inventadas (views, likes, retenção, duração); PatternLearner multimodal (narrativa/áudio/visual) com classificação editorial (OBSERVAÇÃO, PADRÃO, APRENDIZADO_VALIDADO); CentralMemory isolada por canal com amarração estrita de evidence_video_ids; ModelGateway bloqueando modelos comerciais pagos com custo zero ($0.00); 13 indicadores granulares auditáveis no dashboard e index.html; 12 testes em test_fase14 com 100% de sucesso. | — |

Estados permitidos:
- `not_started`
- `in_progress`
- `blocked`
- `implemented`
- `verified`

Use `verified` somente com evidências e testes. Nunca marque concluído por intenção.
