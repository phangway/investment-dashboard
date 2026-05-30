import openpyxl
from returns import build_returns

EXCEL = "/mnt/c/Users/MULIA-PC/Desktop/股票/投资记录.xlsx"
wb = openpyxl.load_workbook(EXCEL, data_only=True)

# 用接近验算快照的输入（汇率 3.97，市值取报告快照值）
rate = 3.97
moomoo_usd = 33650.94
tiger_usd = 15836.84
mplus_total_myr = 194269.81
mplus_net_profit = 162474.48

r = build_returns(wb, rate, mplus_total_myr, moomoo_usd, tiger_usd, mplus_net_profit)

# XIRR 区间检查（容忍数据日期差异）
assert 0.10 < r["xirr"]["mplus"]  < 0.16, f"马股XIRR异常: {r['xirr']['mplus']}"
assert 0.16 < r["xirr"]["moomoo"] < 0.24, f"MooMoo XIRR异常: {r['xirr']['moomoo']}"
assert -0.05 < r["xirr"]["tiger"] < 0.05, f"Tiger XIRR异常: {r['xirr']['tiger']}"
assert 0.06 < r["xirr"]["total"]  < 0.12, f"总XIRR异常: {r['xirr']['total']}"

# ROI 精确检查
assert abs(r["roi"]["mplus"]["value"] - 162474.48 / 140000) < 0.001
assert abs(r["roi"]["us"]["value"]    - 47048 / 133418)     < 0.01
assert abs(r["roi"]["total"]["value"] - (162474.48 + 47048) / 273418) < 0.01

print("✅ test_returns 全部通过")
print("  XIRR:", {k: round(v * 100, 2) for k, v in r["xirr"].items()})
print("  ROI :", {k: round(v["value"] * 100, 2) for k, v in r["roi"].items()})
