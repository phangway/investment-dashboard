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

if __name__ == "__main__":
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    us, monthly, yearly, totals = read_us_stocks(wb)
    print("美股总资产:", us)
    print("月度数据条数:", len(monthly))
    print("最新3条:", monthly[-3:])
    print("年度数据:", yearly[-2:])
    print("历史总盈亏:", totals)
