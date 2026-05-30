from datetime import date
from xirr import xirr

# 案例1：投 1000，约一年后变 1100 → XIRR ≈ 10%/年
r = xirr([(date(2020, 1, 1), -1000), (date(2021, 1, 1), 1100)])
assert r is not None and abs(r - 0.10) < 0.002, f"案例1 期望≈0.10, 得到 {r}"

# 案例2：分两笔投入，最后取回，年化为正
r2 = xirr([(date(2020, 1, 1), -1000), (date(2020, 7, 1), -1000), (date(2022, 1, 1), 2300)])
assert r2 is not None and 0.05 < r2 < 0.12, f"案例2 超出预期: {r2}"

# 案例3：全是同号现金流 → 无解 → None
assert xirr([(date(2020, 1, 1), -100), (date(2021, 1, 1), -50)]) is None

# 案例4：少于两笔 → None
assert xirr([(date(2020, 1, 1), -100)]) is None

print("✅ test_xirr 全部通过")
