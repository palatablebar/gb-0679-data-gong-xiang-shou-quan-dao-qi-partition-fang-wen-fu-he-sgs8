# 接口

模块GET使用仓内样例，模块POST可传csv或rows与context，直接计算当前规则。/api/runs使用完整流水线并原子保存。每个阶段返回rows、quarantine、metrics；后续阶段还返回累计隔离。/api/upload接收multipart文件file。/api/runs/<id>/archive只导出一份带清单与证据的CSV。

批次载荷含monthly_conclusion（唯一月度访问结论：UTC口径、逐月合计、跨月事件清单、未解释数），全部模块页展示同一结论。归档CSV首行kind=conclusion记录结论，逐行带month_policy、access_month、source_month、cross_month列。存在未解释跨月差异的批次在封存阶段以UNEXPLAINED_CROSS_MONTH拒绝。同一输入重跑复用已有批次不新增结论；重跑失败不写库，旧版本与原证据保留。
