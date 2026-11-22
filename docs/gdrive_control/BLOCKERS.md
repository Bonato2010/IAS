# VANTIS — BLOCKERS & DEPENDENCIES

| ID | Data | Descrição do Bloqueio | Impacto | Ação Necessária | Responsável | Estado |
|---|---|---|---|---|---|---|
| BLK-001 | 2026-11-21 | Credenciais OAuth do YouTube para publicação real em canais de teste | Impede teste de upload real (mesmo que estritamente privado) nos canais do YouTube. O serviço de upload atualmente gera o pacote, manifesto e executa mock de upload. | Fornecer `client_secrets.json` e autorizar o canal de teste quando o usuário desejar testar uploads reais privados. | Usuário | Em espera (não bloqueia pipelines nem interface) |
| BLK-002 | 2026-11-21 | Chave de API externa de modelos pagos não autorizada | Nenhuma (por design, política $0.00). Modelos locais e Edge-TTS estão suprindo 100% da operação. | Nenhuma ação necessária no momento. | Sistema | Resolvido por design |
