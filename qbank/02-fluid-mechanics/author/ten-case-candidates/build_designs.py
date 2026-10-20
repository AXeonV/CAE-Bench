"""Build an explicit inventory and per-task scenario proposals, without running jobs.

No HF writes, selection changes or numerical validation occur here.
Only fully specified entries can be submitted to the separate native runner.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from scenarios import FAMILIES, family_for
from coverage import matrix, representation_targets

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CHAPTER = ROOT / "qbank/02-fluid-mechanics"
BATCH = "chapter02-ten-20261020"
HF_REVISION = "d46b17a03d444646157e1e2fe4b4f00587dc5d89"
EXCLUDED = {"newtonian-incompressible-steady-2d", "newtonian-incompressible-steady-3d"}

SOURCES = {
    "openfoam": {
        "url": "https://gitlab.com/openfoam/core/openfoam",
        "version": "OpenCFD v2512",
        "image_id": "sha256:d6e27c56bb5f598bc93597fdf671d6e9d06534b1851885f1b093e3cc627ea67e",
        "role": "现成求解器出处；本批几何/工况为作者设计，不声称为原教程数据",
    },
    "basilisk": {"url": "https://basilisk.fr/src/navier-stokes/centered.h", "version": "2026.10.18-snapshot-de851a91", "image_id": "sha256:906dc955c1b156196abcd087463cec6d3a4fbca76465d7aa21486dde84621ad9"},
    "elmer": {"url": "https://github.com/ElmerCSC/elmerfem", "image_id": "sha256:49e9458cc3b1ea3d7e7383c32056af59b0f718e74b0f30adbe3e1bccc0e7b059"},
    "clawpack": {"url": "https://www.clawpack.org/gallery/", "image_id": "sha256:9553e81044dfb139789f41e711f890689d72632ea00e851f3c021d38af84bc3f"},
    "piclas": {"url": "https://piclas.readthedocs.io/en/stable/userguide/features-and-models/DSMC.html", "version": "4.3.0", "image_id": "sha256:a6b6097c8ff0493c5d9e8e8ba98e954be23dd98940c2267ca31f2759dddbea0a"},
}


def sha(p):
    # Authoring files are UTF-8 text. Fingerprints must survive Windows checkout
    # CRLF conversion and match the LF blobs retained in Git/Titan snapshots.
    return hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def native_prescription(i, dimension):
    """Ten different transient closed-cavity experiments, fully fixed in SI."""
    length = [[1,1,1], [1,2,1], [3,1,1], [1,1,1], [1,1,1],
              [1,1,1], [2,1,1], [1,1,1], [1,1,1], [1,1,1]][i]
    cells = [[24,24,12], [24,40,12], [60,20,12], [24,24,12], [24,24,12],
             [24,24,12], [40,20,12], [30,30,12], [24,24,12], [24,24,12]][i]
    if dimension == 2:
        length = length[:2] + [0.02]
        cells = cells[:2] + [1]
    end = 0.4 if i == 1 else 0.3 if i in (8,9) else 0.2
    history = [[0,0],[0.05,1],[end,1]]
    if i == 8: history = [[0,0],[0.05,1],[0.10,1],[0.15,0],[end,0]]
    if i == 9: history = [[0,0],[0.05,1],[0.10,1],[0.15,-1],[end,-1]]
    wall_velocity = {"top_left":[1,0,0], "top_right":[1,0,0]}
    if i == 3: wall_velocity["bottom"] = [-1,0,0]
    if i == 4: wall_velocity["bottom"] = [1,0,0]
    if i == 5: wall_velocity["right"] = [0,0,0.5] if dimension == 3 else [0,0.5,0]
    if i == 6: wall_velocity["top_right"] = [-1,0,0]
    return {
        "spatial_dimension": dimension,
        "length_m": length,
        "target_cells_xyz": cells,
        "obstacle_xy_fraction": [0.4,0.6,0.3,0.5] if i == 7 else None,
        "obstacle_through_z": i == 7,
        "density_kg_m3": 1.0,
        "dynamic_viscosity_Pa_s": 0.01,
        "temperature_K": 300.0,
        "pressure": {"representation":"gauge", "reference_pressure_Pa":101325.0,
                     "gauge":"volume_mean", "gauge_value_Pa":0.0},
        "time_interval_s": [0.0, end],
        "initial_velocity_m_s": [0,0,0][:dimension],
        "wall_velocity_vectors_m_s": wall_velocity,
        "wall_speed_multiplier_linear_table": history,
        "other_boundaries": "no_slip",
        "body_acceleration_m_s2": [0,0,0][:dimension],
        "output_times_s": [round(end*x,12) for x in (0.25,0.5,0.75,1)],
        "outputs": ["velocity","pressure"],
        "output_support": "each supplied fluid cell; physical cell average",
        "native_solver": "icoFoam",
        "native_dt_s": 0.0005,
        "native_time_scheme": "Euler",
        "native_turbulence": "none",
        "status": "numerically_specified_not_computed_not_validated",
    }


def candidate_sources(family):
    if family in ("kinetic_gas",): return ["piclas"]
    if family.startswith("shallow") or family in ("wetdry", "two_layer"): return ["clawpack","basilisk"]
    if family in ("liquid_film","gas_film","thermal_film","nonnewtonian_film"): return ["elmer"]
    if family in ("free_surface","immiscible","capillary"): return ["basilisk","openfoam"]
    return ["openfoam","elmer"]


def risks(family, slug):
    common = ["未做数值验证、网格加密或独立交叉验证；不得称为已验证case"]
    extra = {
        "closed_flow": ["闭腔压力按流体单元体积均值转换到Pa；二维仅空方向为empty"],
        "generalized_flow": ["逐项匹配四种流变律的参数化与剪切率截断；禁止用近似同名模型代替"],
        "isothermal_compressible": ["保持真正等温状态关系；不运行能量方程后仅覆盖输出温度", "核对非零体黏度及封闭质量约束"],
        "euler_equilibrium": ["只允许等熵u=0平衡；采样体力必须保持保守，不能通过任意采样引入旋度"],
        "euler_transient": ["仅封闭滑移绝热壁；不得以开边界激波管直接替换"],
        "lowmach_energy": ["核对温度幂律mu/k、Boussinesq体力及黏性耗散；未确认前不得提交求解"],
        "compressible_energy": ["核对热完全理想气体、独立体黏度、压缩功和黏性耗散"],
        "turbulent_flow": ["模型专有状态不得伪装成题目额外输入", "统计题必须按DATA离散等权样本构造均值和协方差"],
        "free_surface": ["必须是一流体自由表面；有小但非零气体密度/黏度的两流体近似不是精确相同工况"],
        "immiscible": ["确认两流体动量、零表面张力和物理相平均转全单元平均"],
        "capillary": ["匹配非零物理Navier滑移长度及穿a相静态接触角；不能使用网格滑移代替"],
        "dispersed": ["本题为Euler含率和表观相通量，不是随意离散颗粒轨迹", "分别匹配单向/双向、相应应力、线性拖曳及dense拥挤压强闭合"],
        "exchange": ["同时匹配两温、两浓度、相体积加权守恒和分配系数1"],
        "evaporation": ["匹配尖锐界面质量率、法向速度跳跃、反冲牵引和完整焓跳跃；Lee体积源不能替换"],
        "boiling": ["匹配指定Lee型体积质量率、非零速度散度及混合焓；不使用壁面沸腾经验闭合"],
        "cavitation": ["匹配DATA压力线性质量率；Schnerr–Sauer/Merkle/Kunz默认模型不可按同名直接代入"],
        "melting": ["匹配线性糊状区、有限阻力系数与epsilon及全域常黏度；相变率为物质导数"],
        "liquid_film": ["匹配Elrod–Adams质量守恒空化；不能负压截断"],
        "gas_film": ["必须是可压缩Reynolds薄膜模型而非完整Navier–Stokes近似"],
        "thermal_film": ["匹配跨隙均温能量、两项耗散和2H壁换热，不用跨隙热模型替代"],
        "nonnewtonian_film": ["须解Carreau局部跨隙BVP；不能代入有效牛顿黏度"],
        "shallow_steady": ["全湿且真正定常；储槽采用特征Riemann连接，线性摩擦不能换Manning"],
        "shallow_transient": ["全湿、线性摩擦、节点点值与有限体积均值需明确转换"],
        "wetdry": ["干区严格按DATA定义；不把内部干湿阈值变成物理输入"],
        "two_layer": ["匹配两个独立层的质量/动量、床摩擦和层间摩擦；保持光滑全湿双曲稳定范围"],
        "slip_gas": ["核对硬球mu(T)、等温/含热方程、Navier滑移及热跳跃；存在储槽开边界"],
        "kinetic_gas": ["transition用硬球碰撞而非BGK；free-molecular禁碰撞", "核对Maxwell混合反射、半空间储槽、粒子统计和完整三维速度分布"],
        "viscoelastic": ["匹配Oldroyd-B、无额外应力扩散、构象SPD和Azz=1；不能只生成速度压力"],
        "thixotropic": ["匹配线性结构黏度与build/break动力学；不以默认不同触变律替代"],
    }.get(family, [])
    if slug == "thermal-viscoelastic": extra += ["热耗散必须含构象自由能松弛项，不是全部聚合物应力功"]
    if slug == "thermal-generalized-newtonian": extra += ["按DATA的指数温移Carreau律；不沿用2.2幂律温度模型", "本题无Boussinesq温胀；工况中的热对流仅由机械驱动产生"]
    return common + extra


def analysis_kind(section,slug):
    if "statistics" in slug:return "discrete_statistics"
    if "steady" in slug or section.startswith("2.10-") or slug in ("liquid-lubrication","nonnewtonian-film"):
        return "steady"
    if "rans" in slug and "urans" not in slug:return "steady"
    return "transient"


def resolve_scenario(family,index,slug,kind,drive,coverage):
    """Resolve generic steady/transient branches before writing per-question proposals."""
    steady=kind=="steady"
    if family=="generalized_flow" and index==7:
        drive="Carreau、相向分段壁速" if steady else "Carreau、分段线性壁速脉冲和相容物理初速度"
    if family=="generalized_flow" and index==9:
        drive="截断幂律、稳态不等速多壁驱动" if steady else "截断幂律、非零相容物理初速度和多壁驱动"
    if family=="isothermal_compressible" and index==8:
        drive="理想气体、非零体黏度、空间非均匀入口密度和完整储槽牵引出口" if steady else "理想气体、非零体黏度、相容非均匀初密度与速度/密度入口、完整储槽牵引出口"
    if family in ("lowmach_energy","compressible_energy") and index==9:
        drive="多分区冷热壁和机械驱动，无物理初态" if steady else "分段线性壁温脉冲、相容物理初态和机械驱动"
    if family=="compressible_energy" and index==8:
        drive="独立非零体黏度、壁面驱动及冷热壁" if steady else "独立非零体黏度、相容低幅声学初态和热壁"
    if family=="turbulent_flow" and index==9:
        if steady:drive="多分区非均匀壁速，无物理初态"
        elif kind=="discrete_statistics":drive="完整非零散度零瞬时初速度和分段线性壁速；按DATA明确等权样本窗口"
        else:drive="脉冲壁速、公开平均初速度及不同正k/积分长度尺度的空间初态"
    if family=="viscoelastic":
        if index==7:drive="不等速反向壁、无物理初态" if steady else "非单位SPD构象初态与不等速反向壁；二维Azz恒为1"
        if index==8:drive="三段顶壁的定常驱动" if steady else "壁速撤去后的弹性松弛，保留物理构象初态"
        if index==9:drive="偏心内孔附近的不等速定常壁驱动" if steady else "分段线性壁速反转，保留物理构象与速度初态"
    return drive,coverage


def main():
    records = []
    for p in CHAPTER.glob("*/*/instruction.md"):
        if p.parent.name in EXCLUDED: continue
        task_dir = p.parent
        number = re.match(r"#\s+(\d+\.\d+\.\d+)",p.read_text(encoding="utf-8")).group(1)
        slug,section = task_dir.name,task_dir.parent.name
        family = family_for(section,slug)
        kind = analysis_kind(section,slug)
        data = (task_dir/"DATA.md").read_text(encoding="utf-8")
        model = re.findall(r"fluid-[a-z0-9-]+-v1", data)
        dim = 3 if slug.endswith("3d") or slug in ("thermal-generalized-newtonian","transition-gas","free-molecular") else 2
        entries = []
        for i,(key,title,drive,coverage) in enumerate(FAMILIES[family]):
            drive,coverage=resolve_scenario(family,i,slug,kind,drive,coverage)
            entry = {
                "design_id": f"ch02-{number.replace('.','-')}-{i+1:02d}-{key}",
                "title":title, "driving_and_state":drive, "difference_and_coverage":coverage,
                "spatial_dimension":dim,
                "geometry_note": "3D题必须采用有限深度及真实端壁/非平面场，不能仅把2D结果挤出" if dim == 3 else "全局xy；薄膜/浅水是实际水平面积，其他二维积分按DATA",
                "provenance": {"case_conditions":"author-designed proposal", "candidate_solver_sources":candidate_sources(family), "producer_compatibility":"not_yet_established"},
                "status":"scenario_proposal_not_numerically_frozen",
                "remaining_before_execution":["确定数值几何、全部SI物性和初边值", "确认现成生产者与本题闭合及边界等价", "生成自包含problem.json、mesh.msh、input.h5和原生求解器配置"],
            }
            if slug == "thermal-viscoelastic":
                entry["thermal_design"] = "初始T和全部壁温均300K；从起点以后按分段线性历史将两片相对壁分别升/降至305K/295K，其余壁300K。入口例同步给定入口温度；所有热边界按DATA完整分区。避开多迹角点的点观测。温度移位同时作用于两黏度及松弛时间。"
            if "statistics" in slug:
                entry["statistics_design"] = "按本题DATA明确统计起止与等步长样本；同一单元先空间平均，再做等权样本统计；数值窗口尚待工况冻结，不能报告为已有统计参考。"
            if family == "capillary":
                entry["contact_angle_proposal_rad"] = [1.5707963267948966,1.0471975511965976,2.0943951023931953,0.7853981633974483,1.0471975511965976,1.5707963267948966,1.5707963267948966,2.0943951023931953,1.0471975511965976,1.5707963267948966][i]
                if i in (5,6): entry["material_design"] = "分别选择高黏度对比的毛细阻尼及有明显密度对比的重力/毛细竞争；数值比例随物理滑移长度、毛细时间和Bond数共同冻结，不能仅改变数值凑例。"
            if family == "nonnewtonian_film" and i in (1,2):
                entry["rheology_coverage_design"] = "选定间隙、压差、壁速与Carreau时间常数，使跨隙局部lambda*gamma覆盖低剪切、过渡及高剪切区；完整BVP生产后才能确认实际覆盖，不以名义剪切率代替。"
            if family == "euler_equilibrium" and i in (3,9):
                entry["entropy_inventory_design"] = "独立指定等熵参考密度与总体平均密度，不将两者设为隐含同值；二者连同保守势和温度范围一起冻结。"
            if family == "shallow_steady" and i==5:
                entry["regime_design"] = "采用上游全入射超临界储槽控制的光滑全湿扩张分支，排除边界未确定的水跃分支；稳态不是任意末帧。"
            if slug in ("newtonian-incompressible-transient-2d","newtonian-incompressible-transient-3d") and i in (0,8,9):
                entry["prescription"] = native_prescription(i,dim)
                entry["status"] = "numerically_specified_pending_native_adapter"
                entry["provenance"]["producer_compatibility"] = "icoFoam constant-density laminar incompressible transient; closed fixed no-slip walls"
                entry["provenance"]["candidate_solver_sources"] = ["openfoam"]
                entry["remaining_before_execution"] = ["生成自包含输入和原生配置；完成映射代码后实际执行"]
            entries.append(entry)
        record = {
            "batch":BATCH, "question":number, "task":slug,
            "question_path":task_dir.relative_to(ROOT).as_posix(),
            "model":model[0] if model else "cfd-2.1",
            "family":family,
            "analysis_kind":kind,
            "document_sha256": {f:sha(task_dir/f) for f in ("instruction.md","DATA.md","author/grading-template.json")},
            "document_hash_format":"sha256_of_utf8_text_with_lf_newlines",
            "hf_baseline":{"repo":"jimzhouzzy2006/CAE-Bench-OJ","revision":HF_REVISION,"pool_cases":0},
            "target_pool_size":10, "proposed_cases":entries,
            "limitations_and_model_checks":risks(family,slug),
            "coverage_matrix":matrix(family,entries,slug),
            "coverage_state":"design_targets_only_not_verified",
            "representation_coverage_targets":representation_targets(section,dim),
        }
        dest=task_dir/"author"/BATCH/"design.json"
        write(dest,record)
        records.append({"question":number,"path":dest.relative_to(ROOT).as_posix(),"family":family,"cases":len(entries), "numerically_specified":sum("prescription" in e for e in entries),"coverage_targets":len(record["coverage_matrix"]),"unassigned_targets":sum(not x["assigned_design_ids"] for x in record["coverage_matrix"]),"sha256":sha(dest)})
    records.sort(key=lambda r:tuple(map(int,r["question"].split('.'))))
    assert len(records)==63 and sum(r["cases"] for r in records)==630
    index = {
        "batch":BATCH, "base_git_commit":"1740d71a86bcb9260b3b3fdde7feb6ab28ed2735",
        "branch":"cases/chapter-02-ten-reference-candidates",
        "text_hash_format":"sha256_of_utf8_text_with_lf_newlines",
        "excluded_questions":["2.1.1","2.1.3"], "hf_read_revision":HF_REVISION,
        "scope":{"questions":63,"scenario_proposals":630,"numerically_specified":sum(r["numerically_specified"] for r in records),"computed":0,"validated":0},
        "policy":{"all_designs_before_batch_execution":True,"numerical_validation":False,"hf_writes":False,"formal_selection_changes":False,"benchmark":False,"custom_physics_extensions":False,"unmatched_producers":"hold_and_search_existing_implementation"},
        "sources":SOURCES,"questions":records,
    }
    write(HERE/"index.json",index)
    lines=["# 第二章每题十例：设计草案清单", "", "排除2.1.1、2.1.3。以下是630项工况提案，不是630个已制作输入，更不是已计算参考。", "", "数值参数、现成生产者匹配和转换尚未完成的条目明确暂缓。全部工况完成设计前不启动批量计算；不恢复旧FOAMBench任务。", "", "| 题号 | 工况族 | 草案 | 数值参数已固定 | 逐例设计 |", "|---|---|---:|---:|---|"]
    for r in records:
        rel=Path(r["path"]).relative_to("qbank/02-fluid-mechanics").as_posix()
        lines.append(f"| {r['question']} | {r['family']} | {r['cases']} | {r['numerically_specified']} | [design.json](../../{rel}) |")
    (HERE/"CATALOG.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    coverage_lines=["# 考察内容与工况覆盖矩阵", "", "以下均为设计目标，尚无实现或数值覆盖证据。每项对应的具体design ID在各题design.json中；空列表就是设计缺口，不能算已覆盖。", "", "| 题号 | 工况族 | 目标项 | 尚未分配 | 设计 |", "|---|---|---:|---:|---|"]
    for r in records:
        rel=Path(r["path"]).relative_to("qbank/02-fluid-mechanics").as_posix()
        coverage_lines.append(f"| {r['question']} | {r['family']} | {r['coverage_targets']} | {r['unassigned_targets']} | [矩阵](../../{rel}) |")
    coverage_lines += ["", "## 逐题设计分配", "", "所有条目仍是planned状态；特别是剪切率区间、马赫数、无回流、全湿、双曲稳定等条件，后续必须由具体输入与生产者记录支撑，不能由本表直接宣称满足。", ""]
    all_cases=["# 第二章630项工况草案", "", "这是设计草案，尚未全部固定数值或生成输入，不是已计算case清单。", ""]
    for r in records:
        rec=__import__('json').loads((ROOT/r["path"]).read_text(encoding="utf-8"))
        coverage_lines += [f"### {r['question']} {rec['task']}", "", "| 考察内容 | 分配至草案序号 | 状态 |", "|---|---|---|"]
        entries=rec["proposed_cases"];numbers={e["design_id"]:i+1 for i,e in enumerate(entries)}
        for item in rec["coverage_matrix"]:
            coverage_lines.append(f"| {item['requirement']} | {', '.join(str(numbers[k]) for k in item['assigned_design_ids']) or '缺口'} | {item['status']} |")
        coverage_lines.append("")
        all_cases += [f"## {r['question']} {rec['task']}", "", "| 序号 | ID | 几何 | 驱动与状态 | 有效差异/考查目标 |", "|---|---|---|---|---|"]
        for i,e in enumerate(entries):
            all_cases.append(f"| {i+1} | {e['design_id']} | {e['title']} | {e['driving_and_state']} | {e['difference_and_coverage']} |")
        all_cases.append("")
    (HERE/"COVERAGE.md").write_text("\n".join(coverage_lines).rstrip()+"\n",encoding="utf-8",newline="\n")
    (HERE/"ALL-CASES.md").write_text("\n".join(all_cases).rstrip()+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(index["scope"]))


if __name__=="__main__": main()
