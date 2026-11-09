"""마켓 시뮬레이터 - 주식 + 비트코인 모의 투자 게임 (Streamlit)

실행: streamlit run main.py
- 10초(1배속)마다 하루가 지나며, 배속은 1/2/5/10/30배 중 선택
- 초기 자금 100만원, 매월 27일 생활비 30만원 출금
- 뉴스(황당한 사건 포함)에 따라 주가가 움직이고, 기업은 파산해 다른 회사로 교체될 수 있음
- 비트코인 거래, 1,000만원 채굴기 구매, 리셋, 파산 시 게임 오버 후 재시작
"""
import datetime as dt
import random
import time

# ───────────────────────── 게임 로직 ─────────────────────────
START, LIVING, BILLDAY = 1_000_000, 300_000, 27
MINER, FEE, MINE, ELEC = 10_000_000, 0.001, 0.0008, 15_000
DAY_SEC, SPEEDS = 10, (1, 2, 5, 10, 30)

SEC = {"tech": "IT", "auto": "자동차", "bio": "바이오", "energy": "에너지", "food": "식품",
       "game": "게임", "ent": "엔터", "fin": "금융", "air": "항공", "bld": "건설", "ret": "유통"}
POOL = [("한빛전자", "tech", 68000, 2.2), ("넥서스AI", "tech", 142000, 3.2), ("퀀텀닷소프트", "tech", 31000, 3.5),
        ("애플트리", "tech", 210000, 1.8), ("대성모터스", "auto", 74000, 2), ("테슬로", "auto", 320000, 3.4),
        ("청운바이오", "bio", 52000, 3.8), ("메디온", "bio", 18000, 4.2), ("미래에너지", "energy", 39000, 2.3),
        ("선샤인파워", "energy", 27000, 2.8), ("그린푸드", "food", 23000, 1.3), ("별미식품", "food", 61000, 1.5),
        ("서울게임즈", "game", 45000, 3.1), ("픽셀웍스", "game", 12000, 4), ("별빛엔터", "ent", 33000, 3.3),
        ("달토끼엔터", "ent", 9000, 4.5), ("한강은행", "fin", 48000, 1.4), ("오션캐피탈", "fin", 96000, 1.7),
        ("스카이라인항공", "air", 17000, 3), ("다온건설", "bld", 21000, 2.4), ("아마존강물류", "ret", 88000, 2.1),
        ("마트로이드", "ret", 36000, 1.6)]

NN = [("{n}, 분기 사상 최대 실적 발표", .07), ("{n}, 대규모 해외 수주 계약 체결", .08),
      ("{n}, 핵심 임원 횡령 의혹으로 압수수색", -.09), ("{n}, 주력 제품 결함으로 리콜 결정", -.08),
      ("{n}, 유상증자 공시… 주주가치 희석 우려", -.06), ("{n}, 경쟁사와 특허 분쟁 패소", -.07)]
AN = [("{n} CEO, \"어젯밤 외계인과 합작 계약 맺었다\" 발언… 시장은 일단 반응", .09),
      ("{n} 본사 앞 비둘기 떼가 일제히 한 방향 응시… 점쟁이 \"상승 신호\"", .06),
      ("{n} 구내식당 김치찌개에서 고대 문명 유물 발견, 박물관이 인수 제안", .07),
      ("{n} 신입사원, 전 직원 연봉표를 비둘기 발에 묶어 유출", -.08),
      ("{n} 회장 꿈에 나온 번호로 신사업 결정, 임원진 당혹", -.07),
      ("{n}, 달 표면 광고판 계약 성사… 달토끼협회 \"소음 공해\" 항의", .08),
      ("{n} 로고를 본 전국 고양이들이 일제히 앉아… 집사들 계좌 개설 러시", .09),
      ("{n} 대표, 시간여행자 자처… \"내년 주가는 알지만 말 못 한다\"", -.05),
      ("{n} 엘리베이터가 17층과 19층 사이 존재하지 않는 층에 멈춰… 감사 착수", -.06)]
MN = [("정체불명의 거대 오리가 한강에 출현… 증시 전반 투자심리 위축", -.025), ("중앙은행 기준금리 동결, 시장 안도 랠리", .02),
      ("전국 와이파이가 3분간 동시에 노래를 불러… 시민들 \"나쁘진 않았다\"", .012), ("글로벌 공급망 차질 우려 확산", -.02),
      ("지하철 2호선이 하루 동안 거꾸로 달려… 소비심리 위축", -.015)]
SN = [("tech", "전 세계 서버가 동시에 \"안녕하세요\"를 출력… IT업계 \"원인 불명이지만 예의 바름\"", .04),
      ("tech", "차세대 반도체 수출 규제 강화 소식", -.04), ("auto", "전기차 보조금 확대 발표", .04),
      ("bio", "신약 임상 3상 성공 소식… 환자들 \"맛은 딸기맛\"", .05), ("energy", "국제 유가 급락", -.04),
      ("food", "\"라면 먹으면 키 큰다\" 근거 없는 소문 확산… 식품주 들썩", .04), ("game", "게임 셧다운 규제 논의 재점화", -.04),
      ("air", "조종사 전원이 같은 꿈을 꿨다며 운항 거부… 결항 속출", -.05), ("bld", "부동산 규제 완화 기대감", .04),
      ("ret", "초대형 쇼핑 페스티벌 개막, 소비 폭발", .04), ("fin", "기준금리 인상 시사에 은행주 강세", .04)]
BN = [("비트코인 창시자를 자처하는 햄스터 등장… 시장 \"일단 믿어본다\"", .09), ("주요국 가상자산 규제 강화 발표", -.1),
      ("채굴장에서 지하 1km 금괴 발견… 알고 보니 초콜릿", -.05), ("대형 기관, 비트코인 대량 매수", .1),
      ("전국 전기밥솥이 일제히 채굴 시작… 밥은 설익음", .06)]
BK = ["누적 적자와 자금난 끝에", "회계 부정 적발로 신용이 붕괴되며", "채권단의 대출 회수에 막혀",
      "회장이 전 재산을 사내 메기 경주에 걸었다 모두 잃고", "본사 건물이 통째로 사라진 사건(경찰 \"주차장은 남아 있음\") 끝에"]


def gz():
    return (sum(random.random() for _ in range(6)) - 3) * 1.414


def won(n):
    return f"{round(n):,}원"


def pct(v):
    return f"{v * 100:+.2f}%"


def tick(p):
    for lim, t in ((2000, 1), (5000, 5), (20000, 10), (50000, 50), (200000, 100), (500000, 500)):
        if p < lim:
            return t
    return 1000


def rt(p):
    t = tick(p)
    return max(1, round(p / t) * t)


def fd(d):
    return f"{d.year}년 {d.month}월 {d.day}일 ({'월화수목금토일'[d.weekday()]})"


def candle(o, c, v, d):
    return (o, max(o, c) * (1 + random.random() * v * .6), min(o, c) * (1 - random.random() * v * .6), c, d)


class Asset:
    def __init__(self, name, sec, p, v, is_btc=False):
        self.n, self.s, self.p, self.ipo, self.v, self.is_btc = name, sec, p, p, v, is_btc
        self.b = 0.3 if is_btc else 0.6 + random.random() * 0.8
        self.q, self.cost, self.drift = 0.0, 0.0, []
        cs = [p]
        for _ in range(29):
            q = cs[0] / (1 + gz() * v)
            cs.insert(0, round(q / 1000) * 1000 if is_btc else rt(q))
        self.c = [candle(cs[i - 1] if i else x, x, v, i - 28) for i, x in enumerate(cs)]
        self.prev = cs[28]
        self.new_book()

    def new_book(self):
        self.ob = ([random.random() for _ in range(5)], [random.random() for _ in range(5)])

    @property
    def value(self):
        return self.q * self.p


class News:
    def __init__(self, day, text, v, kind, cat, asset):
        self.d, self.t, self.v, self.k, self.cat, self.a = day, text, v, kind, cat, asset


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start = dt.date.today()
        pool = [Asset(n, s, p, v / 100) for n, s, p, v in POOL]
        random.shuffle(pool)
        self.stocks, self.res = pool[:12], pool[12:]
        self.btc = Asset("비트코인", "btc", 90_000_000, 0.035, True)
        self.sel = self.stocks[0]
        self.day, self.cash, self.miners, self.mkt = 1, START, 0, 0.0
        self.idx = self.idx_prev = 1000.0
        self.news, self.today, self.ban = [], [], None
        self.over, self.why, self.peak, self.idle = False, "", START, False
        self.add(f"모의 시장이 개장했습니다. 매월 {BILLDAY}일에 생활비 {won(LIVING)}이 출금됩니다.", 0, "bill", "안내")

    # ── 조회
    def assets(self):
        return [self.btc] + self.stocks

    def date(self, day=None):
        return self.start + dt.timedelta(days=(day or self.day) - 1)

    @property
    def net_worth(self):
        return self.cash + sum(a.value for a in self.assets()) + self.miners * MINER

    def next_bill(self):
        for k in range(1, 32):
            d = self.date(self.day + k)
            if d.day == BILLDAY:
                return f"{d.month}월 {d.day}일 (D-{k})"

    # ── 뉴스
    def add(self, text, v=0, kind="", cat="", asset=None):
        n = News(self.day, text, v, kind, cat, asset)
        self.news.insert(0, n)
        del self.news[80:]
        if v:
            self.today.append(n)
        return n

    def hit(self, s, v):
        s.p = rt(max(50, s.p * (1 + v * .6)))
        s.drift.append([v * .4 / 4, 4])

    def new_news(self):
        r = random.random()
        if r < .12:
            t, b = random.choice(BN), self.btc
            b.p = max(5e6, round(b.p * (1 + t[1] * .7) / 1000) * 1000)
            b.drift.append([t[1] * .3 / 4, 4])
            return self.add(t[0], t[1], "", "코인", b)
        if r < .27:
            t = random.choice(MN)
            for s in self.stocks:
                self.hit(s, t[1] * s.b)
            return self.add(t[0], t[1], "", "시장")
        if r < .45:
            t = random.choice(SN)
            grp = [s for s in self.stocks if s.s == t[0]]
            if grp:
                for s in grp:
                    self.hit(s, t[2])
                return self.add(t[1], t[2], "", SEC[t[0]], grp[0])
        s = random.choice(self.stocks)
        t = random.choice(AN if random.random() < .45 else NN)
        self.hit(s, t[1])
        self.add(t[0].format(n=s.n), t[1], "", s.n, s)

    def bankrupt(self, s, why):
        i = self.stocks.index(s)
        if self.res:
            n = self.res.pop()
        else:
            n = Asset(random.choice(["신성", "대한", "네오", "블루", "제니스"]) + random.choice(["테크", "홀딩스", "산업", "랩스"]),
                      random.choice(list(SEC)), random.randint(10000, 150000), (1.5 + random.random() * 3) / 100)
        lost = f" 보유 중이던 {int(s.q):,}주({won(s.value)}어치)는 휴지조각이 됐습니다." if s.q else ""
        self.add(f"{s.n}, {why} 파산 선고… 상장폐지.{lost}", -1, "bk", "상장폐지")
        self.stocks[i] = n
        if self.sel is s:
            self.sel = n
        self.add(f"신규 상장: {n.n}({SEC[n.s]}) 공모가 {won(n.p)}", 0, "", "신규상장", n)

    # ── 거래
    def sell(self, a, q):
        self.cash += round(q * a.p * (1 - FEE))
        a.cost *= 1 - q / a.q
        a.q -= q
        if a.q < 1e-9:
            a.q = a.cost = 0.0

    def order(self, side, a, q):
        """주문 실행. 실패하면 오류 메시지를 돌려준다."""
        q = int(q) if not a.is_btc else int(q * 1e6) / 1e6
        if q <= 0:
            return "수량을 확인하세요"
        if side == "buy":
            c = round(q * a.p * (1 + FEE))
            if c > self.cash + 1:
                return "현금이 부족합니다"
            self.cash = max(0, self.cash - c)
            a.cost += c
            a.q += q
        else:
            if q > a.q + 1e-9:
                return "보유 수량이 부족합니다"
            self.sell(a, min(q, a.q))

    def buy_miner(self):
        if self.cash < MINER:
            return "현금이 부족합니다"
        self.cash -= MINER
        self.miners += 1
        self.add(f"채굴기를 구매했습니다. 하루 {MINE} BTC를 채굴합니다.", 0, "bill", "채굴")

    def bill(self):
        forced = False
        if self.cash < LIVING:
            for a in sorted(self.assets(), key=lambda x: -x.value):
                if self.cash >= LIVING:
                    break
                if a.q:
                    need = (LIVING - self.cash) / (a.p * (1 - FEE))
                    self.sell(a, min(a.q, need if a.is_btc else -(-need // 1)))
                    forced = True
        if self.cash >= LIVING - 2:
            self.cash = max(self.cash, LIVING)
        if self.cash < LIVING:
            self.cash, self.over = 0, True
            self.why = f"{fd(self.date())} 생활비를 내지 못해"
            return self.add("생활비를 내지 못했습니다.", 0, "bill", "생활비")
        self.cash -= LIVING
        self.add(f"생활비 {won(LIVING)}이 출금됐습니다." + (" 현금이 부족해 보유 자산이 일부 강제 매도됐습니다." if forced else ""),
                 0, "bill", "생활비")

    # ── 하루 진행
    def move(self, a, r):
        if a.is_btc:
            a.p = max(5e6, round(a.p * (1 + r) / 1000) * 1000)
        else:
            a.p = rt(max(50, a.p * (1 + r)))
        a.c.append(candle(a.prev, a.p, a.v, self.day))
        del a.c[:-80]
        a.new_book()

    def next_day(self):
        self.day += 1
        self.today = []
        for a in self.assets():
            a.prev = a.p
        self.new_news()
        if random.random() < .25:
            self.new_news()
        self.mkt = self.mkt * .9 + gz() * .0006
        m = self.mkt + gz() * .007
        sec = {k: gz() * .006 for k in SEC}
        sr = 0.0
        for s in list(self.stocks):
            d = sum(x[0] for x in s.drift)
            s.drift = [[x[0], x[1] - 1] for x in s.drift if x[1] > 1]
            self.move(s, max(-.3, min(.3, s.b * m + sec[s.s] + s.v * gz() + d)))
            sr += s.p / s.prev - 1
            if s.p < s.ipo * .15 and random.random() < .06:
                self.bankrupt(s, random.choice(BK))
        self.idx_prev, self.idx = self.idx, self.idx * (1 + sr / len(self.stocks))
        if random.random() < .004:
            self.bankrupt(random.choice(self.stocks), random.choice(BK))
        b = self.btc
        d = sum(x[0] for x in b.drift)
        b.drift = [[x[0], x[1] - 1] for x in b.drift if x[1] > 1]
        self.move(b, max(-.25, min(.25, .3 * m + .035 * gz() + d)))
        if self.miners:
            cost = ELEC * self.miners
            if self.cash >= cost:
                self.cash -= cost
                b.q += MINE * self.miners
                self.idle = False
            elif not self.idle:
                self.idle = True
                self.add("전기료를 내지 못해 채굴기가 멈췄습니다. 현금을 확보하세요.", 0, "bill", "채굴")
        if self.date().day == BILLDAY:
            self.bill()
        if self.today:
            self.ban = max(self.today, key=lambda n: abs(n.v))
        self.check_over()

    def check_over(self):
        if self.over:
            return
        mp = min(s.p for s in self.stocks) * (1 + FEE)
        if self.cash < mp and not any(s.q for s in self.stocks) and self.btc.value < mp:
            self.over, self.why = True, ""
        self.peak = max(self.peak, self.net_worth)


# ───────────────────────── 화면 (Streamlit) ─────────────────────────
import html as _html

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="마켓 시뮬레이터", layout="wide")
UP, DN, GD, KK, MU = "#ff4b5c", "#3d85ff", "#f0b44a", "#e879f9", "#7a8697"
cl = lambda v: UP if v > 0 else DN if v < 0 else "inherit"
BOX = "rgba(127,127,127,.14)"
LINE = "rgba(127,127,127,.25)"

if "g" not in st.session_state:
    st.session_state.g = Game()
    st.session_state.acc = 0.0
    st.session_state.last = time.time()
g = st.session_state.g

msg = st.session_state.pop("flash", None)
if msg:
    st.toast(msg)


def restart():
    st.session_state.g.reset()
    st.session_state.acc = 0.0
    st.session_state.last = time.time()
    st.session_state.flash = "새 게임을 시작했습니다."
    st.rerun()


def table(head, rows):
    al = lambda i: "left" if i == 0 else "right"
    h = "".join(f'<th style="text-align:{al(i)};color:{MU};font-weight:500;padding:3px 6px;font-size:12px">{t}</th>'
                for i, t in enumerate(head))
    b = "".join("<tr>" + "".join(
        f'<td style="text-align:{al(i)};padding:4px 6px;border-top:1px solid {LINE};color:{c}">{v}</td>'
        for i, (v, c) in enumerate(r)) + "</tr>" for r in rows)
    return f'<table style="width:100%;border-collapse:collapse;font-size:13px"><tr>{h}</tr>{b}</table>'


def chip(n):
    if n.k == "bk":
        return f'<b style="color:{KK};white-space:nowrap">전량 소멸</b>'
    if n.v:
        return f'<b style="color:{cl(n.v)};white-space:nowrap">{"▲ +" if n.v > 0 else "▼ "}{abs(n.v * 100):.0f}%</b>'
    return ""


# ── 상단: 날짜 · 지수 · 배속 · 정지 · 리셋
top = st.columns([3, 2.2, 3.4, 1.2, 1.2])
top[0].markdown(f"### {fd(g.date())} · {g.day}일차")
ic = g.idx / g.idx_prev - 1
top[1].markdown(f'가상지수 **{g.idx:.2f}** <span style="color:{cl(ic)}">{"▲" if ic >= 0 else "▼"} {pct(ic)}</span>',
                unsafe_allow_html=True)
top[2].radio("배속", SPEEDS, horizontal=True, format_func=lambda x: f"{x}x", key="speed")
top[3].toggle("일시정지", key="paused")
with top[4].popover("리셋"):
    st.write("모든 진행 상황이 초기화됩니다.")
    if st.button("정말 리셋", key="rs"):
        restart()


@st.fragment(run_every=0.5)
def clock():
    s = st.session_state
    now = time.time()
    dt_ = min(now - s.last, 2.0)
    s.last = now
    gm = s.g
    if not (s.get("paused") or gm.over):
        s.acc += dt_ * s.get("speed", 1)
        n = 0
        while s.acc >= DAY_SEC and n < 60 and not gm.over:
            s.acc -= DAY_SEC
            gm.next_day()
            n += 1
        if n:
            st.rerun()
    st.progress(min(1.0, s.acc / DAY_SEC), text="다음 날까지" if not s.get("paused") else "일시정지 중")


clock()

# ── 게임 오버
if g.over:
    st.error(f"💥 파산 — {g.why + ' ' if g.why else ''}{g.day}일 만에 모든 자산을 잃었습니다. 최고 자산은 {won(g.peak)}였습니다.")
    if st.button("다시 시작", type="primary"):
        restart()
    st.stop()

# ── 요약
nw = g.net_worth
st_val = sum(s.value for s in g.stocks) + g.btc.value
m = st.columns(5)
m[0].metric("총자산", won(nw))
m[1].metric("수익률", pct(nw / START - 1))
m[2].metric("현금", won(g.cash))
m[3].metric("주식 · 코인 평가", won(st_val))
m[4].metric(f"월 생활비 (매월 {BILLDAY}일)", f"−{won(LIVING)}", f"다음 출금 {g.next_bill()}", delta_color="off")

# ── 속보 배너
b = g.ban
if b:
    col = KK if b.k == "bk" else cl(b.v)
    st.markdown(f'<div style="padding:14px 18px;border-radius:6px;border-left:6px solid {col};background:{BOX};'
                f'font-size:19px;font-weight:650;line-height:1.4"><span style="background:{col};color:#fff;font-size:12px;'
                f'padding:2px 8px;border-radius:3px;margin-right:10px">{"상장폐지" if b.k == "bk" else "속보"}</span>'
                f'{_html.escape(b.t)} &nbsp;{chip(b)}</div>', unsafe_allow_html=True)
else:
    st.info("아직 큰 뉴스가 없습니다. 시장을 지켜보세요.")

left, mid, right = st.columns([1.15, 2.5, 1.15])
A = g.assets()

# ── 왼쪽: 종목 선택 / 관심종목 / 보유
with left:
    idx = st.selectbox("종목 선택", range(len(A)), format_func=lambda i: A[i].n, key="sel_i")
    g.sel = a = A[idx]
    rows = []
    for s in A:
        d = s.p - s.prev
        c = cl(d)
        rows.append([(("▶ " if s is a else "") + f"<b>{s.n}</b>", "inherit"), (f"{s.p:,}", c),
                     (f"{'▲' if d > 0 else '▼'}{abs(d):,}" if d else "-", c), (pct(s.p / s.prev - 1), c)])
    st.markdown(table(["종목", "현재가", "대비", "등락률"], rows), unsafe_allow_html=True)
    st.markdown("**보유 종목**")
    held = [s for s in A if s.q > 0]
    if held:
        rows = []
        for s in held:
            r = s.value / s.cost - 1
            rows.append([(s.n, "inherit"), (f"{s.q:.4f}" if s.is_btc else f"{int(s.q):,}", "inherit"),
                         (f"{round(s.cost / s.q):,}", "inherit"), (pct(r), cl(r))])
        st.markdown(table(["종목", "수량", "평균단가", "손익"], rows), unsafe_allow_html=True)
    else:
        st.caption("보유 종목이 없습니다.")

# ── 가운데: 차트 / 뉴스
with mid:
    d = a.p - a.prev
    k = a.c[-1]
    st.markdown(f'<span style="font-size:18px;font-weight:700">{a.n}</span> &nbsp;'
                f'<span style="font-size:26px;font-weight:700;color:{cl(d)}">{a.p:,}</span> &nbsp;'
                f'<span style="color:{cl(d)}">{"▲" if d >= 0 else "▼"} {abs(d):,} ({pct(a.p / a.prev - 1)})</span> &nbsp;'
                f'<span style="color:{MU};font-size:12px">시 {k[0]:,.0f} 고 {k[1]:,.0f} 저 {k[2]:,.0f}</span>',
                unsafe_allow_html=True)
    K = a.c[-60:]
    xs = [g.date(x[4]).isoformat() for x in K]
    closes = [x[3] for x in a.c]
    fig = go.Figure(go.Candlestick(
        x=xs, open=[x[0] for x in K], high=[x[1] for x in K], low=[x[2] for x in K], close=[x[3] for x in K],
        increasing_line_color=UP, increasing_fillcolor=UP, decreasing_line_color=DN, decreasing_fillcolor=DN,
        name="일봉", showlegend=False))
    for mlen, mcol in ((5, GD), (20, "#b78bff")):
        ys = []
        for i in range(len(K)):
            j = len(closes) - len(K) + i
            ys.append(sum(closes[j - mlen + 1:j + 1]) / mlen if j >= mlen - 1 else None)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=mcol, width=1), name=f"{mlen}일선"))
    fig.add_hline(y=a.p, line_dash="dash", line_width=1, line_color=UP if a.p >= a.prev else DN)
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), xaxis_rangeslider_visible=False,
                      yaxis_side="right", legend=dict(orientation="h", y=1.08), xaxis_type="category",
                      xaxis=dict(nticks=8))
    st.plotly_chart(fig)

    st.markdown("**실시간 뉴스**")
    items = ""
    for n in g.news[:60]:
        dd = g.date(n.d)
        fresh = f"background:rgba(240,180,74,.12);border-left:3px solid {GD};" if n.d == g.day else ""
        tcol = KK if n.k == "bk" else GD if n.k == "bill" else "inherit"
        items += (f'<div style="padding:10px 8px;border-bottom:1px solid {LINE};font-size:16px;line-height:1.5;{fresh}">'
                  f'<span style="color:{MU};font-size:12px">{dd.month}/{dd.day}</span> '
                  f'<span style="font-size:11px;padding:1px 7px;border-radius:3px;background:{LINE}">{n.cat or "알림"}</span> '
                  f'<span style="color:{tcol}">{_html.escape(n.t)}</span> &nbsp;{chip(n)}</div>')
    with st.container(height=420):
        st.markdown(items, unsafe_allow_html=True)

# ── 오른쪽: 호가 / 주문 / 채굴기
with right:
    t = 1000 if a.is_btc else tick(a.p)
    base = 3 if a.is_btc else max(20, round(2e7 / a.p))
    f = lambda r: f"{base * (.3 + r * 2):.2f}" if a.is_btc else f"{round(base * (.3 + r * 2)):,}"
    ob = [[(f"{a.p + t * (i + 1):,}", DN), (f(a.ob[0][i]), "inherit")] for i in range(4, -1, -1)]
    ob.append([(f"<b>{a.p:,}</b>", cl(a.p - a.prev)), (pct(a.p / a.prev - 1), cl(a.p - a.prev))])
    ob += [[(f"{a.p - t * (i + 1):,}", UP), (f(a.ob[1][i]), "inherit")] for i in range(5)]
    st.markdown("**호가** (가상)")
    st.markdown(table(["가격", "잔량"], ob), unsafe_allow_html=True)

    st.markdown("**주문 (시장가)**")
    side = st.radio("구분", ["buy", "sell"], horizontal=True, key="side",
                    format_func=lambda x: "매수" if x == "buy" else "매도", label_visibility="collapsed")
    buy = side == "buy"
    qk = f"qty_{idx}_{side}"
    if qk not in st.session_state:
        st.session_state[qk] = 0.001 if a.is_btc else 1

    def set_pct(p, qk, idx, side):
        gm = st.session_state.g
        x = gm.assets()[idx]
        mx = gm.cash / (x.p * (1 + FEE)) if side == "buy" else x.q
        q = x.q if (p == 1 and side == "sell") else mx * p
        st.session_state[qk] = int(q * 1e6) / 1e6 if x.is_btc else int(q)

    if a.is_btc:
        q = st.number_input("수량 (BTC)", min_value=0.0, step=0.0001, format="%.6f", key=qk)
    else:
        q = st.number_input("수량 (주)", min_value=0, step=1, key=qk)
    pc_ = st.columns(4)
    for col, (label, p) in zip(pc_, (("10%", .1), ("25%", .25), ("50%", .5), ("최대", 1))):
        col.button(label, key=f"pct{p}", on_click=set_pct, args=(p, qk, idx, side))
    mx = g.cash / (a.p * (1 + FEE)) if buy else a.q
    st.caption(f"{'최대' if buy else '보유'} " + (f"{mx:.6f} BTC" if a.is_btc else f"{int(mx):,}주")
               + f" · 예상금액 {won(q * a.p * (1 + FEE if buy else 1 - FEE))} (수수료 0.1%)")
    if st.button(f"{'매수' if buy else '매도'} 주문 · {a.n}", type="primary", key="go"):
        err = g.order(side, a, q)
        st.session_state.flash = err or "주문이 체결됐습니다."
        st.rerun()

    st.markdown("**비트코인 채굴기**")
    st.caption(f"{g.miners}대 보유 · 하루 {MINE * g.miners:.4f} BTC · 전기료 {won(ELEC * g.miners)}/일")
    if st.button(f"채굴기 구매 · {won(MINER)}", disabled=g.cash < MINER, key="miner"):
        st.session_state.flash = g.buy_miner() or "채굴기를 구매했습니다."
        st.rerun()
