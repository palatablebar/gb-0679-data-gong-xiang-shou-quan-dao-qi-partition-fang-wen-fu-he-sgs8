from pathlib import Path
import os
ROOT=Path(__file__).resolve().parent.parent
DATA_DIR=Path(os.environ.get("DATA_DIR", "/tmp/grantpartition"))
TITLE='数据共享授权到期与分区访问复核'
SHORT='grantpartition'
COLUMNS=['event_id', 'principal', 'resource', 'partition', 'access_time', 'observed', 'reported', 'note']
MODULES=[('accesses', '访问采信'), ('resources', '资源映射'), ('grants', '授权定版'), ('conflicts', '冲突裁决'), ('partitions', '分区判定'), ('audit', '访问对账'), ('seals', '审计归档')]
RULE_VERSION="2026.11.18-r2"
# 月度访问结论口径：统一UTC月。集团日结要求UTC口径；授权生效窗已按UTC比较，
# 月度归集与授权裁决共用同一UTC时刻，避免口径分裂。来源地区月仅作证据保留。
MONTH_POLICY="UTC"
MONTH_POLICY_BASIS="集团日结统一UTC月；来源地区月仅作证据保留"
SAMPLES={"dirty.csv","clean.csv","legacy.csv","crossmonth.csv"}
