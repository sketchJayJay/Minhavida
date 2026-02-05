# Meta Game PRO NEON 🎮⚡💰 (JayJay)
Versão PRO com personagem (JayJay) + missões pré-cadastradas (Cyber/Neon).

## Destaques
- Personagem JayJay evolui com as missões (XP e nível)
- Ranks automáticos por nível (Neon Rookie → Neon Legend)
- Missões diárias/semanais/mensais pré-cadastradas com XP por missão
- Bônus diário: ao completar 5+ missões no dia → +10 XP (uma vez por dia)
- Financeiro: ganhos/gastos, categorias, filtro semana/mês + gráfico por categoria
- Login simples (hash de senha)
- SQLite persistente via volume (/data)

## Variáveis de ambiente
- `DB_PATH` (padrão: `/data/metagame.db` se existir `/data`, senão `./metagame.db`)
- `SECRET_KEY` (recomendado definir no Coolify)

## Credenciais iniciais
- usuário: `admin`
- senha: `admin123` (troque em Config)

## Coolify (importante)
Monte um volume em `/data` para não perder o banco (metas/financeiro/personagem).
Porta do app: `5000`.
