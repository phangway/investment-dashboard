import openpyxl
import requests
import json
from datetime import date

EXCEL_PATH = "/mnt/c/Users/MULIA-PC/Desktop/股票/投资记录.xlsx"
OUTPUT_PATH = "/mnt/c/Users/MULIA-PC/Desktop/investment-dashboard/data.json"

def parse_num(val):
    if val is None or val == "—" or str(val).strip() == "—":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def read_us_stocks(wb):
    ws = wb["美股投资账户"]
    rows = list(ws.iter_rows(values_only=True))

    # Current totals: row 4 = index 3, row 5 = index 4, row 6 = index 5
    tiger_total = parse_num(rows[3][1])   # B4
    moomoo_total = parse_num(rows[4][1])  # B5
    combined = parse_num(rows[5][1])      # B6

    # Monthly data: row 8 is header (index 7), data starts row 9 (index 8)
    monthly = []
    yearly = []
    totals = {"tiger_all_time": None, "moomoo_all_time": None, "total_all_time": None}

    for row in rows[8:]:
        year_val = row[0]
        month_val = row[1]
        tiger_val = parse_num(row[2])
        moomoo_val = parse_num(row[3])
        total_val = parse_num(row[4])

        if year_val == "历史总盈亏":
            totals["tiger_all_time"] = tiger_val
            totals["moomoo_all_time"] = moomoo_val
            totals["total_all_time"] = total_val
            continue

        if isinstance(year_val, str) and "年合计" in str(year_val):
            year_num = int(str(year_val).split("年")[0])
            yearly.append({"year": year_num, "tiger": tiger_val,
                           "moomoo": moomoo_val, "total": total_val})
            continue

        if isinstance(year_val, int) and month_val:
            month_str = str(month_val).replace("月", "").strip()
            month_key = f"{year_val}-{int(month_str):02d}"
            monthly.append({"month": month_key, "tiger": tiger_val,
                            "moomoo": moomoo_val, "total": total_val})

    return {
        "tiger_total_usd": tiger_total,
        "moomoo_total_usd": moomoo_total,
        "total_usd": combined,
    }, monthly, yearly, totals

def read_mplus(wb):
    ws = wb["马股投资账户"]
    rows = list(ws.iter_rows(values_only=True))

    # Find summary section by label (robust against new rows being inserted above)
    summary_start = next(
        (i for i, r in enumerate(rows) if r[0] and "孚展市值" in str(r[0])),
        None
    )
    if summary_start is None:
        raise ValueError("找不到孚展市值行，请检查 Excel 马股投资账户工作表结构")

    margin_value = parse_num(rows[summary_start][1])
    cash_total   = parse_num(rows[summary_start + 1][1])
    holding_pnl  = parse_num(rows[summary_start + 2][1])
    div_cash     = parse_num(rows[summary_start + 3][1])
    div_margin   = parse_num(rows[summary_start + 4][1])
    snap_date    = str(rows[summary_start + 5][1])[:10] if rows[summary_start + 5][1] else ""

    total_myr = round((margin_value or 0) + (cash_total or 0), 2)

    # Historical snapshots: rows where both 股票(E, index 4) and 现金(F, index 5) are non-None
    snapshots = []
    for row in rows[3:summary_start]:
        dt = row[1]
        stock = parse_num(row[4])
        cash  = parse_num(row[5])
        if dt and stock is not None and cash is not None:
            snap_total = round(stock + cash, 2)
            snapshots.append({
                "date": str(dt)[:10],
                "total_myr": snap_total
            })

    # Add current snapshot if not duplicate
    if snap_date and (not snapshots or snapshots[-1]["date"] != snap_date):
        snapshots.append({"date": snap_date, "total_myr": total_myr})

    return {
        "margin_market_value_myr": margin_value,
        "cash_total_myr": cash_total,
        "total_myr": total_myr,
        "holding_pnl_myr": holding_pnl,
        "dividends_cash_myr": div_cash,
        "dividends_margin_myr": div_margin,
        "snapshot_date": snap_date,
    }, snapshots

def fetch_exchange_rate():
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=USD&to=MYR", timeout=5)
        r.raise_for_status()
        rate = r.json()["rates"]["MYR"]
        return {"usd_to_myr": round(rate, 4), "fetched_at": str(date.today())}
    except Exception as e:
        print(f"[fetch_exchange_rate] 汇率获取失败: {e}")
        return {"usd_to_myr": None, "fetched_at": str(date.today())}

if __name__ == "__main__":
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    us, monthly, yearly, totals = read_us_stocks(wb)
    mplus, snapshots = read_mplus(wb)
    fx = fetch_exchange_rate()

    output = {
        "updated": str(date.today()),
        "exchange_rate": fx,
        "us_stocks": us,
        "mplus": mplus,
        "monthly_usd": monthly,
        "yearly_summary_usd": yearly,
        "totals_usd": totals,
        "mplus_snapshots": snapshots,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ data.json 已写入: {OUTPUT_PATH}")
    print(f"   美股总资产: USD {us['total_usd']:,.2f}")
    print(f"   M+ 总资产: MYR {mplus['total_myr']:,.2f}")
    print(f"   汇率: 1 USD = MYR {fx['usd_to_myr']}")
