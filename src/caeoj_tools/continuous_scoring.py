"""Explicit author-side migration to the release's continuous NRMSE scoring.

This module never reads or rewrites solver outputs or reference arrays.  It
inherits the previous absolute scale; the migration is not a calibration.
"""
from __future__ import annotations

from copy import deepcopy
import math
from typing import Any

SCORING = {"metric": "max_nrmse", "full_credit": 0.05, "zero_credit": 0.10}


def convert_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """Convert one old numerical rule, retaining weights and pressure offsets."""
    if "metric" not in rule:
        raise ValueError("Continuous scoring migration requires a numerical leaf")
    metric = rule["metric"]
    if metric == "nrmse":
        floor = rule["scale_floor"]
    elif metric in {"pointwise", "violation_fraction"}:
        floor = rule["atol"]
    elif metric == "max_abs":
        floor = rule["limit"]
    else:
        raise ValueError(f"No inherited scale for metric {metric!r}")
    if (not isinstance(floor, (int, float)) or isinstance(floor, bool) or
            not math.isfinite(floor) or floor <= 0):
        raise ValueError(f"Expected a positive inherited scale floor: {floor!r}")
    result = {"metric": "nrmse", "time": "per_time", "components": "per_component",
              "scale_floor": floor, "limit": 0.05}
    for key in ("weight_field", "reference_offset"):
        if key in rule:
            result[key] = deepcopy(rule[key])
    return result


def convert_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """Migrate a v1/v2 policy without introducing a runtime scoring fallback."""
    result = deepcopy(policy)
    if result["version"] == 1:
        result["fields"] = {name: convert_rule(rule)
                            for name, rule in result["fields"].items()}
    elif result["version"] == 2:
        if "default" in result:
            result["default"] = convert_rule(result["default"])
        for spec in result.get("quantities", {}).values():
            spec["rule"] = convert_rule(spec["rule"])
    else:
        raise ValueError("Unsupported numerical policy version")
    return result


def convert_grading(config: dict[str, Any]) -> dict[str, Any]:
    """Migrate an explicit outer case grading object (never chapter 0)."""
    result = deepcopy(config)
    result["scoring"] = deepcopy(SCORING)
    for check in result["checks"]:
        if "policy" in check:
            check["policy"] = convert_policy(check["policy"])
        elif "rule" in check:
            check["rule"] = convert_rule(check["rule"])
        else:
            raise ValueError(f"Unsupported evaluator migration: {check['evaluator']}")
    return result


def scoring_text(policy: dict[str, Any], *, normalization: str = "") -> str:
    """Render the public formula and the task's explicit inherited scale table."""
    if policy["version"] == 1:
        entries = [(name, "该输出声明的单位", rule) for name, rule in policy["fields"].items()]
        label = "输出字段"
    else:
        entries = [(name, spec["unit"], spec["rule"])
                   for name, spec in policy["quantities"].items()]
        label = "quantity"
    if any(rule["metric"] != "nrmse" for _, _, rule in entries):
        raise ValueError("Render only an explicitly migrated policy")
    weights = {rule.get("weight_field") for _, _, rule in entries}
    if weights == {None}:
        weight_text = "空间位置采用等点权重 `w_i=1`；这是对请求观测位置的误差评价，不推断网格体积或积分权重。单个整体观测也使用该规则。"
    elif len(weights) == 1 and None not in weights:
        weight_text = f"空间权重使用输入中显式声明的 `{next(iter(weights))}` 字段，按 IDs 对齐；只参与评分，无需在输出中复制。"
    else:
        raise ValueError("Mixed spatial weights require an explicit public description")
    offset = any("reference_offset" in rule for _, _, rule in entries)
    baseline = ("压力的参考尺度使用 `r_i-pressure_reference` 计算 RMS，`pressure_reference` 取输入公开参数；误差分子仍是原始绝对静压的 `a_i-r_i`，不对候选平移或去均值。其他量按其原值计算。"
                if offset else "除 DATA 明确声明的评分变换外，候选和参考均按规定表示直接比较，不平移、去均值、拟合比例或对齐场。")
    table = f"| {label} | scale_floor | 单位 |\n|---|---|---|\n"
    table += "".join(f"| `{name}` | {rule['scale_floor']:g} | `{unit}` |\n"
                     for name, unit, rule in entries)
    return ("对每个请求输出物理量、每个标量分量和每个请求时刻，分别沿空间位置计算加权归一化均方根误差：\n\n"
            "`e = sqrt(sum_i(w_i*(a_i-r_i)^2)/sum_i(w_i)) / max(sqrt(sum_i(w_i*r_i^2)/sum_i(w_i)), scale_floor)`。\n\n"
            "`a_i` 为提交值，`r_i` 为参考值；采用下述已声明的评分变换或参考尺度偏置时，按对应定义代入。不同物理量、分量或时刻不拼接、不取平均。"
            "本例的 `total NRMSE` 定义为这些 `e` 的最大值 `E=max(e)`，全部请求时刻均参与，包括初始帧；全部观测位置均参与，包括边界及零值。\n\n"
            "每例连续得分：`E <= 0.05` 得 1 分；`0.05 < E < 0.10` 得 `(0.10-E)/0.05` 分；`E >= 0.10` 得 0 分。"
            "题目 reward 为全部正式 case 得分的算术平均值，不按字段数量或空间点数量给 case 加权。\n\n"
            f"{weight_text}\n\n{baseline}\n\n" + (f"{normalization}\n\n" if normalization else "") +
            "`scale_floor` 是与本输出同单位的正数下限，防止零参考或很小的参考导致除零或尺度失控。本题明确采用：\n\n" + table +
            "\nIDs、时间轴、shape、dtype 和有限值要求仍须严格满足；整数及布尔输出精确比较。程序失败、超时、超资源、缺失或非法输出得 0 分；输入、参考或评价基础设施错误不算考生失分。守恒、低残差和正常退出不替代目标观测准确性。\n")
