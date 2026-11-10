"""
动态题库（v4）：每次随机替换金额、机构、子网编号和项目名，防止矿工背答案。
所有材料均为自编教学文本，人名、机构与数字不对应任何真实事件。
其中一类模板故意不写领投机构，用来检查矿工是否遵守“缺失字段填空值”的约定。
"""

import random
from typing import Any, Dict

FIELDS = ["项目名称", "融资金额", "领投机构", "子网编号"]


def generate_dynamic_task(rng: random.Random | None = None) -> Dict[str, Any]:
    r = rng or random
    amount = r.choice(["1500万美元", "2800万美元", "4200万美元", "6000万美元"])
    investor = r.choice(["Northwind Capital", "Lakeside Ventures", "Blue Harbor Fund", "Orchid Labs"])
    subnet_id = r.choice(["7号", "19号", "33号", "58号"])
    project = r.choice(["Atlas", "Beacon", "Cobalt", "Delta"])
    task_id = f"task_{r.randint(1000, 9999)}"

    templates = [
        (
            f"【教学快讯】Bittensor 生态项目 {project} 宣布完成 {amount} 战略轮融资。"
            f"本轮融资由 {investor} 领投。项目位于 {subnet_id} 子网，团队表示资金将用于扩充算力节点。",
            {"项目名称": project, "融资金额": amount, "领投机构": investor, "子网编号": subnet_id},
        ),
        (
            f"【教学周报】算力网络 {project}（{subnet_id} 子网）公布季度数据。"
            f"本季度完成 {amount} 新一轮融资，领投方为 {investor}，新资金主要用于数据中心建设。",
            {"项目名称": project, "融资金额": amount, "领投机构": investor, "子网编号": subnet_id},
        ),
        (
            f"【教学简讯】{project} 团队透露已完成 {amount} 融资，但未披露投资方名单。"
            f"该项目目前运行在 {subnet_id} 子网。",
            {"项目名称": project, "融资金额": amount, "领投机构": "", "子网编号": subnet_id},
        ),
    ]
    raw_text, truth = r.choice(templates)
    return {"task_id": task_id, "raw_text": raw_text, "required_fields": list(FIELDS), "ground_truth": truth}
