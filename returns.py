"""读取出入金/现金股息，组装各账户现金流，计算 XIRR + ROI。"""
import datetime
from datetime import date
from xirr import xirr

# ===== 可调常量（用户可改）=====
ROI_BASE = {"mplus": 140000, "us": 133418}   # ROI 代表性本金基准
US_INVESTED_TOTAL = 163418   # 美股真实总投入：2021换汇133,418 + 2026从马股30,000
US_CASH_RETURNED = 14000     # 美股已提回私人现金：2024 MooMoo 提款


def _d(x):
    return x.date() if isinstance(x, datetime.datetime) else x

def _isdate(x):
    return isinstance(x, (datetime.datetime, datetime.date))

def _isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def mplus_capital_flows(wb):
    """马股本金进出（Mplus出入金记录 B=日期 C=金额）：存款=负、提款=正。"""
    flows = []
    for row in wb["Mplus出入金记录"].iter_rows(min_row=2, values_only=True):
        d, a = row[1], row[2]
        if _isdate(d) and _isnum(a):
            flows.append((_d(d), -float(a)))
    return flows


def mplus_dividend_flows(wb):
    """马股现金股息（已提取）作为正现金流。
    J列(第10列)=当年累计现金股息，按每期增量计入，跨年重置。"""
    flows = []
    prev_year, prev_j = None, 0.0
    for row in wb["马股投资账户"].iter_rows(min_row=4, values_only=True):
        dt, j = row[1], row[9]
        if not _isdate(dt) or not _isnum(j):
            continue
        y = _d(dt).year
        if y != prev_year:
            prev_year, prev_j = y, 0.0
        inc = float(j) - prev_j
        prev_j = float(j)
        if inc > 0:                      # 只计正增量（J 沿用上一行=0，倒退则跳过）
            flows.append((_d(dt), inc))
    return flows


def moomoo_io_flows(wb):
    """MooMoo 出入金（MooMoo MY 出入金记录 B=日期 C=金额，MYR）：存=负、提=正。"""
    flows = []
    for row in wb["MooMoo MY 出入金记录"].iter_rows(min_row=2, values_only=True):
        d, a = row[1], row[2]
        if _isdate(d) and _isnum(a):
            flows.append((_d(d), -float(a)))
    return flows


def tiger_io_flows(wb):
    """Tiger：用 Exchange record 的真实换汇 MYR。
    Instarem>CIMB SG(换出投入)=负；CIMB SG>CIMB MY(换回)=正。"""
    flows = []
    for row in wb["Exchange record"].iter_rows(values_only=True):
        if len(row) < 6 or not _isdate(row[1]):
            continue
        note = str(row[5]) if row[5] else ""
        if "CIMB SG > CIMB MY" in note and _isnum(row[3]):
            flows.append((_d(row[1]), float(row[3])))    # 换回 MYR(第4列) = 正
        elif _isnum(row[2]):
            flows.append((_d(row[1]), -float(row[2])))    # 换出 MYR(第3列) = 负
    return flows


def build_returns(wb, rate, mplus_total_myr, moomoo_usd, tiger_usd, mplus_net_profit):
    """组装 4 个 XIRR + 3 个 ROI，返回写入 data.json 的 dict。"""
    today = date.today()
    moomoo_myr = moomoo_usd * rate
    tiger_myr = tiger_usd * rate
    us_value_myr = moomoo_myr + tiger_myr

    cap = mplus_capital_flows(wb)
    div = mplus_dividend_flows(wb)
    mm = moomoo_io_flows(wb)
    tg = tiger_io_flows(wb)

    mplus_cf = cap + div + [(today, mplus_total_myr)]
    moomoo_cf = mm + [(today, moomoo_myr)]
    tiger_cf = tg + [(today, tiger_myr)]
    total_cf = cap + div + tg + mm + [(today, mplus_total_myr + us_value_myr)]

    us_net_profit = us_value_myr + US_CASH_RETURNED - US_INVESTED_TOTAL
    total_net = mplus_net_profit + us_net_profit

    def _x(cf):
        v = xirr(cf)
        return round(v, 4) if v is not None else None

    def roi(profit, base):
        return {"value": round(profit / base, 4),
                "net_profit": round(profit, 2), "base": base}

    return {
        "as_of": str(today),
        "usd_myr": rate,
        "mplus_xirr_incl_dividends": True,
        "xirr": {
            "mplus": _x(mplus_cf),
            "moomoo": _x(moomoo_cf),
            "tiger": _x(tiger_cf),
            "total": _x(total_cf),
        },
        "roi": {
            "mplus": roi(mplus_net_profit, ROI_BASE["mplus"]),
            "us": roi(us_net_profit, ROI_BASE["us"]),
            "total": roi(total_net, ROI_BASE["mplus"] + ROI_BASE["us"]),
        },
    }
