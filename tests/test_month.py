import csv,io
import pytest
from app.errors import DomainError
from app.pipeline import calculate,execute,load_sample
from app import store
from app.values import zoned
from app.modules.m3_grants.rules import evaluate as grants
from app.modules.m7_seals.rules import evaluate as seals
def test_zoned_cross_month_boundary():
    "来源时钟已入12月，UTC仍在11月"
    utc,source,month=zoned("2026-12-01T00:30:00+08:00")
    assert (source,month)==("2026-12","2026-11") and utc.hour==16 and utc.day==30
def test_zoned_negative_offset_cross():
    _,source,month=zoned("2026-11-30T20:30:00-05:00")
    assert (source,month)==("2026-11","2026-12")
def test_zoned_same_month():
    _,source,month=zoned("2026-11-15T12:00:00+08:00")
    assert source==month=="2026-11"
def test_zoned_naive_rejected():
    with pytest.raises(DomainError) as e: zoned("2026-11-15T12:00:00")
    assert e.value.code=="INVALID_TIME"
def test_grants_rows_carry_month_fields():
    row=grants([{"access_time":"2026-12-01T00:30:00+08:00","reported":"1","principal":"analyst","resource":"orders","partition":"2026-11"}],{})["rows"][0]
    assert row["access_month"]=="2026-11" and row["source_month"]=="2026-12" and row["cross_month"] is True and row["month_note"]
def test_unique_monthly_conclusion():
    "每批唯一月度结论：UTC定版，逐月合计与访问总数对平"
    mc=calculate(load_sample("crossmonth.csv"))["monthly_conclusion"]
    assert mc["policy"]=="UTC" and mc["cross_month_count"]==4 and mc["unexplained_count"]==0
    assert sum(mc["months"].values())==mc["access_total"]==6
    assert mc["months"]=={"2026-10":1,"2026-11":4,"2026-12":1}
def test_conclusion_governs_stage_rows():
    "分区判定各行结论月与批次结论一致"
    result=calculate(load_sample("crossmonth.csv"))
    rows=result["stages"][4]["rows"]
    assert all(r["access_month"] in result["monthly_conclusion"]["months"] for r in rows)
    assert {r["event_id"] for r in rows if r["cross_month"]}==set(result["monthly_conclusion"]["cross_month_events"])
def test_unexplained_cross_month_cannot_seal():
    "无法解释的跨月差异不能封存"
    row={"event_id":"X1","cross_month":True,"month_note":"","access_month":"2026-11","source_month":"2026-12"}
    with pytest.raises(DomainError) as e: seals([row],{})
    assert e.value.code=="UNEXPLAINED_CROSS_MONTH"
def test_explained_cross_month_seals():
    row={"event_id":"X1","cross_month":True,"month_note":"来源地区月2026-12与UTC月2026-11相邻，按集团日结统一UTC月定版","access_month":"2026-11","source_month":"2026-12"}
    assert seals([row],{})["metrics"]["ready"] is True
def test_crossmonth_sample_seals():
    result=calculate(load_sample("crossmonth.csv"))
    assert result["stages"][6]["metrics"]["ready"] is True and result["stages"][6]["metrics"]["cross_month"]==4
def test_rerun_adds_no_new_conclusion():
    "同一批次重跑不新增结论"
    raw=load_sample("crossmonth.csv")
    a=execute(raw);b=execute(raw)
    assert a["run_id"]==b["run_id"] and len(store.history())==1
    assert a["monthly_conclusion"]==b["monthly_conclusion"]
def test_failed_rerun_keeps_old_version_and_evidence(client):
    "重跑失败保留旧版与原证据"
    p=client.post("/api/runs",json={"sample":"crossmonth.csv"}).get_json()
    url="/api/runs/"+p["run_id"]
    assert client.post(url+"/review",json={"version":1,"decision":"已复核"}).status_code==200
    assert client.post("/api/runs",json={"csv":"bad"}).status_code==422
    kept=client.get(url).get_json()
    assert kept["version"]==2 and kept["decision"]=="已复核" and kept["monthly_conclusion"]==p["monthly_conclusion"]
    archive=client.get(url+"/archive")
    assert archive.status_code==200 and p["manifest"]["input_sha256"] in archive.data.decode("utf-8-sig")
def test_archive_carries_conclusion(client):
    "证据导出服从月度结论"
    p=client.post("/api/runs",json={"sample":"crossmonth.csv"}).get_json()
    rows=list(csv.reader(io.StringIO(client.get("/api/runs/"+p["run_id"]+"/archive").data.decode("utf-8-sig"))))
    assert rows[0][7:]==["month_policy","access_month","source_month","cross_month"]
    kinds={r[3] for r in rows[1:]}
    assert {"conclusion","accepted"}<=kinds
    accepted=[r for r in rows[1:] if r[3]=="accepted"]
    assert all(r[7]=="UTC" and r[8] for r in accepted)
    crossed=[r for r in accepted if r[10]=="True"]
    assert len(crossed)==4 and all(r[9]!=r[8] for r in crossed)
