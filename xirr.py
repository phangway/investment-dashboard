"""纯 Python XIRR（真实年化回报率）。无需安装任何库。
现金流约定：钱投进投资=负（流出口袋），钱回到口袋/当前市值=正。"""


def xnpv(rate, cashflows):
    """cashflows: [(date, amount), ...]，返回以最早日期为基准的净现值。"""
    t0 = min(d for d, _ in cashflows)
    return sum(a / (1.0 + rate) ** ((d - t0).days / 365.0) for d, a in cashflows)


def xirr(cashflows):
    """二分法求 XIRR。现金流需同时含正负，否则返回 None。"""
    flows = [(d, float(a)) for d, a in cashflows if a is not None]
    if len(flows) < 2:
        return None
    lo, hi = -0.9999, 10.0
    f_lo, f_hi = xnpv(lo, flows), xnpv(hi, flows)
    if f_lo * f_hi > 0:
        return None  # 无符号变化 → 无实数解
    for _ in range(300):
        mid = (lo + hi) / 2.0
        f_mid = xnpv(mid, flows)
        if abs(f_mid) < 1e-7:
            return mid
        if f_lo * f_mid < 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0
