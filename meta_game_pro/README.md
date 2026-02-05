# Meta Game PRO 🎮💰
App gamificado de metas + financeiro (SQLite) pronto para Coolify.

## Recursos
- Metas diárias/semanais/mensais (com data)
- Conclusão de metas dá XP e sobe nível
- Streak (sequência de dias com metas concluídas)
- Financeiro: ganhos/gastos, categorias, filtros por semana/mês, resumo
- Dashboard com gráficos (Chart.js)
- Login (usuário/senha) simples (armazenado com hash)
- Banco persistente via `DB_PATH` (recomendado montar volume em `/data`)

## Rodar local (dev)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
python -m app
# abre http://localhost:5000
```

## Variáveis de ambiente
- `DB_PATH` (padrão: `/data/metagame.db` se existir pasta /data, senão `./metagame.db`)
- `SECRET_KEY` (recomendado definir no Coolify)

## Credenciais iniciais
Ao primeiro start, o sistema cria um admin:
- usuário: `admin`
- senha: `admin123`

> Troque em **Configurações** dentro do app.
