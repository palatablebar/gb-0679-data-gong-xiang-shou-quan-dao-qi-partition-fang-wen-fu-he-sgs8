import csv,io,json
def build_archive(run):
    stream=io.StringIO(newline="");writer=csv.writer(stream)
    writer.writerow(["run_id","input_sha256","rule_version","kind","source_lines","reason","evidence","month_policy","access_month","source_month","cross_month"])
    meta=run["manifest"];conclusion=run.get("monthly_conclusion") or {};policy=conclusion.get("policy","")
    if conclusion: writer.writerow([run["run_id"],meta["input_sha256"],meta["rule_version"],"conclusion","",policy,json.dumps(conclusion,ensure_ascii=False),policy,"","",""])
    for row in run["stages"][-1]["rows"]:
        writer.writerow([run["run_id"],meta["input_sha256"],meta["rule_version"],"accepted",json.dumps(row.get("_sources",[])),row.get("status",""),json.dumps(row,ensure_ascii=False),policy,row.get("access_month",""),row.get("source_month",""),row.get("cross_month","")])
    for row in run["stages"][-1].get("cumulative_quarantine",[]):
        writer.writerow([run["run_id"],meta["input_sha256"],meta["rule_version"],"quarantine",json.dumps(row.get("_sources",[])),row.get("reason",""),json.dumps(row,ensure_ascii=False),policy,row.get("access_month",""),row.get("source_month",""),row.get("cross_month","")])
    return "\ufeff"+stream.getvalue()
