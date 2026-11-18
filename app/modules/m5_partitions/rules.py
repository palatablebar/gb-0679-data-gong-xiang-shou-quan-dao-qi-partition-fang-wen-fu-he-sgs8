from app.reasons import reject
from app.values import number
from app.errors import DomainError
from app.config import MONTH_POLICY,MONTH_POLICY_BASIS
def conclude(rows):
    "批次唯一月度访问结论：统一UTC月定版，来源地区月仅作证据；跨月行逐条可解释。"
    months={};cross=[]
    for row in rows:
        month=row.get("access_month") or "未定论"
        months[month]=months.get(month,0)+1
        if row.get("cross_month"):cross.append(row)
    unexplained=[r for r in cross if not r.get("month_note")]
    return {"policy":MONTH_POLICY,"basis":MONTH_POLICY_BASIS,"access_total":len(rows),"months":dict(sorted(months.items())),"cross_month_count":len(cross),"cross_month_events":[str(r.get("event_id",r.get("_line",""))) for r in cross],"unexplained_count":len(unexplained)}
def evaluate(rows,context):
    good=[];bad=[]
    for row in rows:
        if row.get("observed") not in {"allowed","blocked"}:bad.append(reject(row,"BAD_ACCESS_OUTCOME","访问结果必须为allowed或blocked"));continue
        effect=row["effect"];expected="1" if effect=="allow" else "0";actual="1" if row["observed"]=="allowed" else "0"
        good.append({**row,"expected":expected,"reported":actual,"upstream_decision":row["reported"],"partition_result":"授权内" if row["matched_rules"] else "未授权分区","violation":"越权放行" if expected=="0" and actual=="1" else "误拦截" if expected=="1" and actual=="0" else "一致"})
    conclusion=conclude(good)
    return {"rows":good,"quarantine":bad,"metrics":{"allowed":sum(r["expected"]=="1" for r in good),"blocked":sum(r["expected"]=="0" for r in good),"violations":sum(r["violation"]=="越权放行" for r in good),"false_blocks":sum(r["violation"]=="误拦截" for r in good),"cross_month":conclusion["cross_month_count"],"unexplained":conclusion["unexplained_count"]},"conclusion":conclusion}
