#!/usr/bin/env python3
"""
Day 5 配套工具：Yuma 共识权重聚合与防异常打分模拟器
功能：
1. 在终端直观演示：3 个验证者（不同 Stake 质押权重）给 5 个矿工打分，
   当验证者 A 故意给作弊小号 Miner_5 打满分（1.0）而其他验证者打 0 分时，
   Yuma 共识如何通过加权中位数裁剪（Clipping）削弱异常高分，并惩罚验证者 A 的分红。
2. 自动在同目录下生成带 Excel 公式的 `day05_yuma_simulator.xlsx` 供学员用 Excel 动手修改。
"""

import os
from typing import List, Dict

MINERS = ["Miner_1 (优质)", "Miner_2 (主力)", "Miner_3 (普通)", "Miner_4 (慢节点)", "Miner_5 (作弊小号)"]

VALIDATORS = [
    {"name": "Validator_A (异常打分/试图刷分)", "stake": 0.20},
    {"name": "Validator_B (正常评测节点 1)", "stake": 0.45},
    {"name": "Validator_C (正常评测节点 2)", "stake": 0.35},
]

# 正常情况下的打分 vs 验证者 A 异常偏袒 Miner_5 的打分
WEIGHT_MATRIX_NORMAL = [
    [0.35, 0.30, 0.20, 0.15, 0.00],  # Validator A 正常打分
    [0.40, 0.30, 0.20, 0.10, 0.00],  # Validator B
    [0.35, 0.35, 0.20, 0.10, 0.00],  # Validator C
]

WEIGHT_MATRIX_ANOMALY = [
    [0.00, 0.00, 0.00, 0.00, 1.00],  # Validator A 极端异常：全给作弊小号 Miner_5 打满分 1.0！
    [0.40, 0.30, 0.20, 0.10, 0.00],  # Validator B 正常打分
    [0.35, 0.35, 0.20, 0.10, 0.00],  # Validator C 正常打分
]


def compute_weighted_consensus(stakes: List[float], weights_for_miner: List[float], kappa: float = 0.5) -> float:
    """
    计算单个矿工的 Yuma 共识截断阈值 (Weighted Median / Consensus Threshold)：
    按验证者对矿工的打分从高到低排序，累加验证者 Stake，当累计 Stake 超过 kappa (50%) 时的打分即为共识上限。
    任何高于该上限的异常打分都会被直接 Clipping（削顶）！
    """
    pairs = sorted(zip(weights_for_miner, stakes), key=lambda x: x[0], reverse=True)
    cum_stake = 0.0
    for w, s in pairs:
        cum_stake += s
        if cum_stake >= kappa:
            return w
    return pairs[-1][0]


def run_yuma_simulation(matrix: List[List[float]]) -> Dict:
    stakes = [v["stake"] for v in VALIDATORS]
    num_vals = len(VALIDATORS)
    num_miners = len(MINERS)

    # 1. 行归一化（确保每个验证者给出的总权重之和为 1）
    norm_matrix = []
    for row in matrix:
        s = sum(row)
        norm_matrix.append([w / s if s > 0 else 0.0 for w in row])

    # 2. 计算每个矿工的简单加权平均（如果不做 Yuma 裁剪会被刷走多少分）
    naive_avg = [
        sum(stakes[v] * norm_matrix[v][m] for v in range(num_vals))
        for m in range(num_miners)
    ]

    # 3. 计算每个矿工的 Yuma 共识阈值 (Consensus Threshold)
    consensus_threshold = [
        compute_weighted_consensus(stakes, [norm_matrix[v][m] for v in range(num_vals)], kappa=0.5)
        for m in range(num_miners)
    ]

    # 4. 裁剪异常权重：Clipped_W[v][m] = min(W[v][m], Consensus_Threshold[m])
    clipped_matrix = [
        [min(norm_matrix[v][m], consensus_threshold[m]) for m in range(num_miners)]
        for v in range(num_vals)
    ]

    # 5. 计算裁剪后的矿工最终激励 (Incentive)
    raw_incentive = [
        sum(stakes[v] * clipped_matrix[v][m] for v in range(num_vals))
        for m in range(num_miners)
    ]
    total_inc = sum(raw_incentive)
    incentives = [x / total_inc if total_inc > 0 else 0.0 for x in raw_incentive]

    # 6. 计算每个验证者的共识对齐率 (Validator Trust / vTrust) 與分红比例 (Dividends)
    # vTrust = 裁剪后保留的有效权重之和 / 原始提交权重之和
    v_trust = [sum(clipped_matrix[v]) / sum(norm_matrix[v]) for v in range(num_vals)]
    raw_dividends = [stakes[v] * v_trust[v] for v in range(num_vals)]
    total_div = sum(raw_dividends)
    dividends = [d / total_div if total_div > 0 else 0.0 for d in raw_dividends]

    return {
        "norm_matrix": norm_matrix,
        "naive_avg": naive_avg,
        "consensus_threshold": consensus_threshold,
        "clipped_matrix": clipped_matrix,
        "incentives": incentives,
        "v_trust": v_trust,
        "dividends": dividends,
    }


def export_excel(filepath: str):
    """生成带原生 Excel 公式的 day05_yuma_simulator.xlsx"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        return False

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Yuma共识模拟器"

    header_fill = PatternFill("solid", fgColor="FFE866")
    gray_fill = PatternFill("solid", fgColor="F5F5F5")
    alert_fill = PatternFill("solid", fgColor="FFD6D6")
    bold_font = Font(bold=True, name="Arial")
    thin_border = Border(
        left=Side(style="thin", color="D4D4D4"),
        right=Side(style="thin", color="D4D4D4"),
        top=Side(style="thin", color="D4D4D4"),
        bottom=Side(style="thin", color="D4D4D4"),
    )

    ws["A1"] = "Bittensor Day 5：Yuma 共识防异常刷分模拟器（可直接在黄框修改验证者打分）"
    ws["A1"].font = Font(bold=True, size=13)

    # 表 1：原始打分矩阵
    headers = ["验证者节点", "质押占比 (Stake)"] + MINERS + ["行总和", "验证者对齐度 (vTrust)", "最终分红占比 (Dividends)"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = bold_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center")

    for r_idx, val in enumerate(VALIDATORS, start=4):
        ws.cell(row=r_idx, column=1, value=val["name"]).border = thin_border
        s_cell = ws.cell(row=r_idx, column=2, value=val["stake"])
        s_cell.number_format = "0.0%"
        s_cell.border = thin_border

        for m_idx in range(len(MINERS)):
            c = ws.cell(row=r_idx, column=3 + m_idx, value=WEIGHT_MATRIX_ANOMALY[r_idx - 4][m_idx])
            c.number_format = "0.00"
            c.border = thin_border
            if r_idx == 4 and m_idx == 4:
                c.fill = alert_fill

        # 行总和、vTrust、Dividends 公式
        ws.cell(row=r_idx, column=8, value=f"=SUM(C{r_idx}:G{r_idx})").number_format = "0.00"
        ws.cell(row=r_idx, column=9, value=f"=SUM(C{r_idx+8}:G{r_idx+8})/H{r_idx}").number_format = "0.0%"
        ws.cell(row=r_idx, column=10, value=f"=(B{r_idx}*I{r_idx})/SUMPRODUCT($B$4:$B$6,$I$4:$I$6)").number_format = "0.0%"

    # 第 7 行：如果不做 Yuma 裁剪的普通加权得分
    ws.cell(row=7, column=1, value="【无Yuma保护】简单加权得分").font = bold_font
    ws.cell(row=7, column=2, value="=SUM(B4:B6)").number_format = "0.0%"
    for m_idx in range(len(MINERS)):
        col_let = chr(ord("C") + m_idx)
        c = ws.cell(row=7, column=3 + m_idx, value=f"=SUMPRODUCT($B$4:$B$6,{col_let}4:{col_let}6)")
        c.number_format = "0.0%"
        c.fill = gray_fill

    # 第 8 行：Yuma 共识上限阈值（按 B4:B6 质押权重与 H4:H6 行归一化计算的精确 50% 加权中位数）
    ws.cell(row=8, column=1, value="【Yuma共识】多数派截断阈值 (Consensus)").font = bold_font
    for m_idx in range(len(MINERS)):
        col_let = chr(ord("C") + m_idx)
        c = ws.cell(
            row=8,
            column=3 + m_idx,
            value=(
                f"=IF($B$4>=0.5,{col_let}4/$H$4,"
                f"IF($B$5>=0.5,{col_let}5/$H$5,"
                f"IF($B$6>=0.5,{col_let}6/$H$6,"
                f"MEDIAN({col_let}4/$H$4,{col_let}5/$H$5,{col_let}6/$H$6))))"
            ),
        )
        c.number_format = "0.00"
        c.fill = header_fill
        c.font = bold_font

    # 表 2：Yuma 裁剪后矩阵 (Row 11–15)
    ws.cell(row=10, column=1, value="▼ 下表为经过 Yuma 共识自动削顶（Clipping）后的有效权重矩阵：").font = bold_font
    for r_idx, val in enumerate(VALIDATORS, start=12):
        orig_r = r_idx - 8
        ws.cell(row=r_idx, column=1, value=f"{val['name']} (裁剪后)").border = thin_border
        ws.cell(row=r_idx, column=2, value=f"=B{orig_r}").number_format = "0.0%"
        for m_idx in range(len(MINERS)):
            col_let = chr(ord("C") + m_idx)
            c = ws.cell(row=r_idx, column=3 + m_idx, value=f"=MIN({col_let}{orig_r}/$H${orig_r},{col_let}$8)")
            c.number_format = "0.00"
            c.border = thin_border

    # 第 15 行：最终矿工激励 (Incentive)
    ws.cell(row=15, column=1, value="【Yuma最终分配】矿工激励占比 (Incentive)").font = bold_font
    for m_idx in range(len(MINERS)):
        col_let = chr(ord("C") + m_idx)
        c = ws.cell(
            row=15,
            column=3 + m_idx,
            value=f"=SUMPRODUCT($B$12:$B$14,{col_let}12:{col_let}14)/SUMPRODUCT($B$12:$B$14,C12:C14+D12:D14+E12:E14+F12:F14+G12:G14)",
        )
        c.number_format = "0.0%"
        c.fill = header_fill
        c.font = bold_font

    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 22

    wb.save(filepath)
    return True


def main():
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "day05_yuma_simulator.xlsx")
    res = run_yuma_simulation(WEIGHT_MATRIX_ANOMALY)

    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()
        console.print(
            Panel.fit(
                "[bold yellow]Bittensor Day 5：Yuma 共识（Yuma Consensus）异常权重削弱演示[/bold yellow]\n"
                "场景：3 个验证者给 5 个矿工打分。其中 [bold red]Validator_A (占 20% 质押)[/bold red] 试图作弊，\n"
                "把所有权重 [bold red]1.00[/bold red] 全打给了自己的作弊小号 [bold red]Miner_5[/bold red]，而另外两个诚实验证者给 Miner_5 打了 0 分。",
                border_style="yellow",
            )
        )

        t_miner = Table(title="📊 第一部分：矿工权重裁剪对比（看 Miner_5 的作弊高分如何被削掉）", show_lines=True)
        t_miner.add_column("矿工节点", style="bold cyan")
        t_miner.add_column("Val_A 打分\n(Stake 20%)", justify="right")
        t_miner.add_column("Val_B 打分\n(Stake 45%)", justify="right")
        t_miner.add_column("Val_C 打分\n(Stake 35%)", justify="right")
        t_miner.add_column("若无 Yuma 保护\n(简单加权结果)", justify="right", style="red")
        t_miner.add_column("Yuma 共识上限\n(Consensus 阈值)", justify="right", style="yellow")
        t_miner.add_column("Yuma 裁剪后最终激励\n(Final Incentive)", justify="right", style="bold green")

        for m_idx, m_name in enumerate(MINERS):
            w_a = res["norm_matrix"][0][m_idx]
            w_b = res["norm_matrix"][1][m_idx]
            w_c = res["norm_matrix"][2][m_idx]
            t_miner.add_row(
                m_name,
                f"[bold red]{w_a:.2f}[/bold red]" if w_a > 0.5 else f"{w_a:.2f}",
                f"{w_b:.2f}",
                f"{w_c:.2f}",
                f"{res['naive_avg'][m_idx]*100:.1f}%",
                f"{res['consensus_threshold'][m_idx]:.2f}",
                f"{res['incentives'][m_idx]*100:.1f}%",
            )
        console.print(t_miner)

        t_val = Table(title="⚖️ 第二部分：验证者自身受到的经济惩罚（偏离共识导致 vTrust 与分红归零）", show_lines=True)
        t_val.add_column("验证者节点", style="bold")
        t_val.add_column("质押权重 (Stake)", justify="right")
        t_val.add_column("裁剪后保留权重比 (vTrust)", justify="right")
        t_val.add_column("最终拿到的验证者分红 (Dividends)", justify="right", style="bold green")

        for v_idx, val in enumerate(VALIDATORS):
            vt = res["v_trust"][v_idx]
            div = res["dividends"][v_idx]
            style = "bold red" if vt < 0.5 else "green"
            t_val.add_row(
                val["name"],
                f"{val['stake']*100:.0f}%",
                f"[{style}]{vt*100:.1f}%[/{style}]",
                f"[{style}]{div*100:.1f}%[/{style}]",
            )
        console.print(t_val)
    except ImportError:
        print("=" * 86)
        print("Bittensor Day 5：Yuma 共识（Yuma Consensus）异常权重削弱演示")
        print("场景：Validator_A (Stake 20%) 试图给作弊小号 Miner_5 打满分 1.00，其余验证者打 0.00")
        print("=" * 86)
        print(f"{'矿工节点':<18} | {'Val_A':>6} | {'Val_B':>6} | {'Val_C':>6} | {'无Yuma加权':>10} | {'Yuma阈值':>8} | {'最终激励(Incentive)':>16}")
        print("-" * 86)
        for m_idx, m_name in enumerate(MINERS):
            print(
                f"{m_name:<18} | {res['norm_matrix'][0][m_idx]:>6.2f} | {res['norm_matrix'][1][m_idx]:>6.2f} | "
                f"{res['norm_matrix'][2][m_idx]:>6.2f} | {res['naive_avg'][m_idx]*100:>9.1f}% | "
                f"{res['consensus_threshold'][m_idx]:>8.2f} | {res['incentives'][m_idx]*100:>15.1f}%"
            )
        print("\n【验证者分红惩罚对比】")
        for v_idx, val in enumerate(VALIDATORS):
            print(
                f"• {val['name']:<26} | Stake: {val['stake']*100:>4.0f}% | "
                f"vTrust(对齐率): {res['v_trust'][v_idx]*100:>5.1f}% | 最终分红(Dividends): {res['dividends'][v_idx]*100:>5.1f}%"
            )

    if export_excel(excel_path):
        print(f"\n✅ 已同步生成可交互 Excel 模拟表：{excel_path}")
    else:
        csv_path = excel_path.replace(".xlsx", ".csv")
        with open(csv_path, "w", encoding="utf-8-sig") as f:
            f.write("矿工节点,Val_A(20%),Val_B(45%),Val_C(35%),无Yuma简单加权,Yuma共识阈值,Yuma最终Incentive\n")
            for m_idx, m_name in enumerate(MINERS):
                f.write(
                    f"{m_name},{res['norm_matrix'][0][m_idx]:.2f},{res['norm_matrix'][1][m_idx]:.2f},"
                    f"{res['norm_matrix'][2][m_idx]:.2f},{res['naive_avg'][m_idx]*100:.1f}%,"
                    f"{res['consensus_threshold'][m_idx]:.2f},{res['incentives'][m_idx]*100:.1f}%\n"
                )
        print(f"\n✅ 已同步生成表格文件：{csv_path}（可直接用 Excel 打开截图交作业！）")


if __name__ == "__main__":
    main()
