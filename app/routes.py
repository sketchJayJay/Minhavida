from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta
from .db import connect
from .auth import login_required
from .utils import today_str, parse_date, week_bounds, month_bounds, rank_from_level

bp = Blueprint("meta", __name__)

def db():
    return current_app.config["DB_PATH"]

def get_settings(con):
    return con.execute("SELECT * FROM settings WHERE id=1").fetchone()

def get_state(con):
    return con.execute("SELECT * FROM game_state WHERE id=1").fetchone()

def get_char(con):
    return con.execute("SELECT * FROM character WHERE id=1").fetchone()

def compute_balance(con):
    gain = con.execute("SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='gain'").fetchone()["s"]
    spend = con.execute("SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='spend'").fetchone()["s"]
    return float(gain) - float(spend)

def task_done_in_period(con, task_id: int, kind: str, day: date, due_date: str | None):
    if kind == "once":
        return due_date == day.isoformat() and con.execute(
            "SELECT 1 FROM task_logs WHERE task_id=? AND done_date=?", (task_id, day.isoformat())
        ).fetchone() is not None
    if kind == "daily":
        return con.execute("SELECT 1 FROM task_logs WHERE task_id=? AND done_date=?",
                           (task_id, day.isoformat())).fetchone() is not None
    if kind == "weekly":
        a,b = week_bounds(day)
        return con.execute("SELECT 1 FROM task_logs WHERE task_id=? AND done_date BETWEEN ? AND ?",
                           (task_id, a.isoformat(), b.isoformat())).fetchone() is not None
    if kind == "monthly":
        a,b = month_bounds(day)
        return con.execute("SELECT 1 FROM task_logs WHERE task_id=? AND done_date BETWEEN ? AND ?",
                           (task_id, a.isoformat(), b.isoformat())).fetchone() is not None
    return False

def tasks_for_date(con, day: date):
    ds = day.isoformat()
    rows = con.execute("SELECT * FROM tasks WHERE active=1 ORDER BY kind DESC, xp DESC, id DESC").fetchall()
    visible = []
    for t in rows:
        kind = t["kind"]
        if kind == "once" and t["due_date"] != ds:
            continue
        done = task_done_in_period(con, t["id"], kind, day, t["due_date"])
        visible.append((t, done))
    return visible

def streak_update(con, completed_today: bool, today: date):
    st = get_state(con)
    last = st["last_streak_date"]
    streak = int(st["streak"])
    if not completed_today:
        return
    if last is None:
        con.execute("UPDATE game_state SET streak=?, last_streak_date=? WHERE id=1", (1, today.isoformat()))
        return
    last_d = parse_date(last)
    if last_d == today:
        return
    if last_d == today - timedelta(days=1):
        streak += 1
    else:
        streak = 1
    con.execute("UPDATE game_state SET streak=?, last_streak_date=? WHERE id=1", (streak, today.isoformat()))

def award_xp(con, xp_gain: int):
    st = get_state(con)
    settings = get_settings(con)
    xp = int(st["xp"]) + int(xp_gain)
    level = int(st["level"])
    cap = int(settings["level_xp"])
    while xp >= cap:
        xp -= cap
        level += 1
    con.execute("UPDATE game_state SET xp=?, level=? WHERE id=1", (xp, level))

def add_stat_for_tag(con, tag: str):
    if tag == "saude":
        con.execute("UPDATE character SET strength = strength + 1 WHERE id=1")
    elif tag == "estudo":
        con.execute("UPDATE character SET focus = focus + 1 WHERE id=1")
    elif tag == "dinheiro":
        con.execute("UPDATE character SET discipline = discipline + 1 WHERE id=1")
    elif tag == "trabalho":
        con.execute("UPDATE character SET focus = focus + 1 WHERE id=1")
    elif tag == "casa":
        con.execute("UPDATE character SET discipline = discipline + 1 WHERE id=1")

def maybe_daily_bonus(con, day: date):
    # bônus: ao completar 5+ missões no dia → +10 XP (uma vez por dia)
    ds = day.isoformat()
    already = con.execute("SELECT 1 FROM day_bonus WHERE done_date=?", (ds,)).fetchone()
    if already:
        return
    c = con.execute("SELECT COUNT(*) as c FROM task_logs WHERE done_date=?", (ds,)).fetchone()["c"]
    if int(c) >= 5:
        con.execute("INSERT INTO day_bonus(done_date) VALUES (?)", (ds,))
        award_xp(con, 10)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        with connect(db()) as con:
            u = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            if u and check_password_hash(u["password_hash"], password):
                session["uid"] = u["id"]
                session["username"] = u["username"]
                return redirect(request.args.get("next") or url_for("meta.dashboard"))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("meta.login"))

@bp.route("/")
@login_required
def dashboard():
    d = request.args.get("date") or today_str()
    day = parse_date(d)

    with connect(db()) as con:
        settings = get_settings(con)
        state = get_state(con)
        char = get_char(con)
        rank = rank_from_level(int(state["level"]))
        balance = compute_balance(con)

        items = tasks_for_date(con, day)
        done_count = sum(1 for _, done in items if done)
        total = len(items)

        m0, m1 = month_bounds(day)
        month_gain = con.execute(
            "SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='gain' AND tdate BETWEEN ? AND ?",
            (m0.isoformat(), m1.isoformat())
        ).fetchone()["s"]
        month_spend = con.execute(
            "SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='spend' AND tdate BETWEEN ? AND ?",
            (m0.isoformat(), m1.isoformat())
        ).fetchone()["s"]

        # chart net last 14 days
        start = day - timedelta(days=13)
        days = [(start + timedelta(days=i)) for i in range(14)]
        labels = [x.strftime("%d/%m") for x in days]
        net = []
        for x in days:
            ds = x.isoformat()
            g = con.execute("SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='gain' AND tdate=?", (ds,)).fetchone()["s"]
            s = con.execute("SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='spend' AND tdate=?", (ds,)).fetchone()["s"]
            net.append(float(g) - float(s))

        bonus_done = con.execute("SELECT 1 FROM day_bonus WHERE done_date=?", (day.isoformat(),)).fetchone() is not None

    return render_template(
        "dashboard.html",
        settings=settings, state=state, char=char, rank=rank,
        balance=balance, items=items, day=day,
        done_count=done_count, total=total,
        month_gain=float(month_gain), month_spend=float(month_spend),
        chart_labels=labels, chart_net=net,
        bonus_done=bonus_done
    )

@bp.route("/tasks")
@login_required
def tasks():
    with connect(db()) as con:
        rows = con.execute("SELECT * FROM tasks ORDER BY active DESC, kind DESC, xp DESC, id DESC").fetchall()
    return render_template("tasks.html", tasks=rows)

@bp.route("/tasks/add", methods=["POST"])
@login_required
def tasks_add():
    title = request.form.get("title","").strip()
    kind = request.form.get("kind","daily")
    due_date = request.form.get("due_date") or None
    tag = request.form.get("tag","geral")
    xp = int(request.form.get("xp") or 10)
    if not title:
        flash("Digite um título de missão.", "warning")
        return redirect(url_for("meta.tasks"))
    from datetime import datetime
    with connect(db()) as con:
        con.execute(
            "INSERT INTO tasks(title, kind, due_date, tag, xp, created_at) VALUES (?,?,?,?,?,?)",
            (title, kind, due_date, tag, xp, datetime.utcnow().isoformat())
        )
        con.commit()
    flash("Missão adicionada ✅", "success")
    return redirect(url_for("meta.tasks"))

@bp.route("/tasks/toggle/<int:tid>")
@login_required
def tasks_toggle(tid):
    with connect(db()) as con:
        t = con.execute("SELECT active FROM tasks WHERE id=?", (tid,)).fetchone()
        if t:
            newv = 0 if int(t["active"]) == 1 else 1
            con.execute("UPDATE tasks SET active=? WHERE id=?", (newv, tid))
            con.commit()
    return redirect(url_for("meta.tasks"))

@bp.route("/tasks/done/<int:tid>")
@login_required
def tasks_done(tid):
    d = request.args.get("date") or today_str()
    day = parse_date(d)

    with connect(db()) as con:
        t = con.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        if not t:
            return redirect(url_for("meta.dashboard", date=day.isoformat()))

        kind = t["kind"]
        # checa duplicidade por período
        if task_done_in_period(con, tid, kind, day, t["due_date"]):
            return redirect(url_for("meta.dashboard", date=day.isoformat()))

        # registra log com a data do clique (day)
        con.execute("INSERT INTO task_logs(task_id, done_date) VALUES (?,?)", (tid, day.isoformat()))
        # XP por missão
        award_xp(con, int(t["xp"]))
        # stats
        add_stat_for_tag(con, t["tag"])
        # streak conta só por dia (se completou algo hoje)
        streak_update(con, True, day)
        # bônus 5+ no dia
        maybe_daily_bonus(con, day)

        con.commit()

    return redirect(url_for("meta.dashboard", date=day.isoformat()))

@bp.route("/finance")
@login_required
def finance():
    mode = request.args.get("mode","month")
    d = request.args.get("date") or today_str()
    day = parse_date(d)

    if mode == "week":
        a,b = week_bounds(day)
        title = f"Semana ({a.strftime('%d/%m')} a {b.strftime('%d/%m')})"
    else:
        a,b = month_bounds(day)
        title = f"Mês ({day.strftime('%m/%Y')})"

    with connect(db()) as con:
        tx = con.execute(
            "SELECT * FROM transactions WHERE tdate BETWEEN ? AND ? ORDER BY tdate DESC, id DESC",
            (a.isoformat(), b.isoformat())
        ).fetchall()
        gain = con.execute(
            "SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='gain' AND tdate BETWEEN ? AND ?",
            (a.isoformat(), b.isoformat())
        ).fetchone()["s"]
        spend = con.execute(
            "SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE ttype='spend' AND tdate BETWEEN ? AND ?",
            (a.isoformat(), b.isoformat())
        ).fetchone()["s"]

        cats = con.execute(
            "SELECT category, COALESCE(SUM(amount),0) AS s FROM transactions "
            "WHERE ttype='spend' AND tdate BETWEEN ? AND ? GROUP BY category ORDER BY s DESC",
            (a.isoformat(), b.isoformat())
        ).fetchall()
        cat_labels = [c["category"] for c in cats]
        cat_vals = [float(c["s"]) for c in cats]

    return render_template("finance.html",
                           title=title, tx=tx, mode=mode, day=day,
                           gain=float(gain), spend=float(spend),
                           cat_labels=cat_labels, cat_vals=cat_vals)

@bp.route("/finance/add", methods=["POST"])
@login_required
def finance_add():
    tdate = request.form.get("tdate") or today_str()
    ttype = request.form.get("ttype","spend")
    category = (request.form.get("category") or "Geral").strip() or "Geral"
    note = (request.form.get("note") or "").strip()
    amount_raw = request.form.get("amount","0").replace(",",".")
    try:
        amount = float(amount_raw)
    except:
        flash("Valor inválido.", "danger")
        return redirect(url_for("meta.finance"))
    if amount <= 0:
        flash("Valor precisa ser maior que zero.", "warning")
        return redirect(url_for("meta.finance"))

    with connect(db()) as con:
        con.execute(
            "INSERT INTO transactions(tdate, ttype, category, amount, note) VALUES (?,?,?,?,?)",
            (tdate, ttype, category, amount, note)
        )
        con.commit()
    flash("Movimentação salva 💾", "success")
    return redirect(url_for("meta.finance", date=tdate))

@bp.route("/finance/delete/<int:txid>")
@login_required
def finance_delete(txid):
    with connect(db()) as con:
        con.execute("DELETE FROM transactions WHERE id=?", (txid,))
        con.commit()
    flash("Removido.", "info")
    return redirect(url_for("meta.finance"))

@bp.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    with connect(db()) as con:
        s = get_settings(con)
        ch = get_char(con)
        if request.method == "POST":
            display_name = request.form.get("display_name","JayJay Neon Quest").strip() or "JayJay Neon Quest"
            level_xp = int(request.form.get("level_xp") or 100)
            con.execute("UPDATE settings SET display_name=?, level_xp=? WHERE id=1", (display_name, level_xp))

            # personagem
            cname = request.form.get("cname","JayJay").strip() or "JayJay"
            ccls = request.form.get("ccls","Neon Runner").strip() or "Neon Runner"
            con.execute("UPDATE character SET name=?, cls=? WHERE id=1", (cname, ccls))

            # senha admin
            pw = request.form.get("new_password","").strip()
            if pw:
                con.execute("UPDATE users SET password_hash=? WHERE username='admin'", (generate_password_hash(pw),))
            con.commit()
            flash("Configurações atualizadas ✅", "success")
            return redirect(url_for("meta.settings"))
    return render_template("settings.html", s=s, ch=ch)
