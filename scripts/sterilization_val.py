#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sterilization_val.py — 灭菌与清洁验证计算器
============================================
覆盖医疗器械灭菌/清洁验证的常用工程计算（零依赖，仅标准库）：

  --eo        EO 灭菌 BI 存活分数与过度杀灭判据（ISO 11135 思路）
  --f0        湿热灭菌 F0 累积（ISO 17665 思路，z=10°C, Tref=121.1°C）
  --dose      辐照灭菌 ISO 11137 Method 1 VDmax 剂量设定
  --clean     清洁验证残留限值（PDE/单位面积法 + 10 ppm 经验法对照）
  --endotoxin 细菌内毒素限值（K/M 法，K 按给药途径）

诚实边界：计算模型按公开标准通用公式整理；落地产品须用已验证的
D 值 / z 值 / 生物负载数据，并以官方标准文本复核（TO_BE_VERIFIED 占位）。
"""
from __future__ import annotations
import argparse
import math
import sys

# 细菌内毒素 K 值（EU/kg/h，按给药途径）——中国药典 2025 通则 1143 / USP <85> /
# EP 2.6.14 一致口径（2026-10-12 复核）：注射剂（静脉/肌内/皮下等非鞘内途径）K=5，
# 仅鞘内/椎管内为 0.2。历史勘误：im/sc 曾误载 10.0（放大 2 倍热原限值），已修正。
ENDPOTOXIN_K = {
    "iv": 5.0,        # 静脉
    "intrathecal": 0.2,  # 椎管内/鞘内（最严）
    "im": 5.0,        # 肌肉（注射剂口径，非静脉）
    "sc": 5.0,        # 皮下（注射剂口径，非静脉）
    "implant": 5.0,   # 植入类（按注射剂口径保守取值）
}

SAL_DEFAULT = 1e-6  # 无菌保证水平默认 10^-6


def eo_survival(n0: float, d_value: float, t_min: float) -> dict:
    """EO：BI 存活分数 N = N0 × 10^(-t/D)。

    判据口径（2026-10-13 领域复审修正）：SAL 是无菌保证水平，指单个器械上
    **期望存活微生物数 ≤ 10^-6（绝对口径）**，不是「6 log 削减」——二者仅在
    N0=1 时相等。故本工具分别给出：绝对存活数 N（按 N≤1e-6 判 SAL）与相对
    N0 的 log 削减（仅参考；达 10^-6 所需削减 = log10(N0)+6）。
    """
    if n0 <= 0:
        raise ValueError("--n0（初始 BI 数）须 > 0")
    if d_value <= 0:
        raise ValueError("--d（D 值）须 > 0")
    if t_min < 0:
        raise ValueError("--t（暴露时间）须 ≥ 0")
    n = n0 * (10 ** (-t_min / d_value))
    log_red = t_min / d_value  # 真·log 削减 = log10(N0) - log10(N)
    need_log = math.log10(n0) + 6.0
    return {
        "N0": n0, "D(min)": d_value, "t(min)": t_min,
        "存活数 N(CFU/器械)": n,
        "log 削减(相对 N0)": round(log_red, 2),
        "达 SAL 10^-6 所需 log 削减": round(need_log, 2),
        "SAL 判据(N≤1e-6)": "PASS" if n <= 1e-6 else f"BLOCK（N={n:.3e} > 1e-6）",
    }


def f0_accumulate(segments: list[tuple[float, float]], z: float = 10.0,
                  tref: float = 121.1) -> dict:
    """湿热：F0 = Σ Δt × 10^((T-Tref)/z)。segments = [(温度°C, 分钟), ...]"""
    if z <= 0:
        raise ValueError("--z（z 值）须 > 0")
    total = sum(dt * (10 ** ((t - tref) / z)) for t, dt in segments)
    return {
        "segments": [f"{t}°C×{dt}min" for t, dt in segments],
        "z(°C)": z, "Tref(°C)": tref,
        "F0(min)": round(total, 2),
        "判据": "PASS" if total >= 8.0 else "WARN（< 8 min，需按负载与产品论证）",
    }


def dose_vdmax(n0: float, d10: float, sal: float = SAL_DEFAULT) -> dict:
    """辐照：简化剂量估算 D = D10 × log10(N0/SAL)（生物负载 + 6 log 口径）。

    诚实边界（2026-10-13 领域复审修正）：本值**不是** ISO 11137-2 的 Method 1
    或 VDmax 结论。Method 1 为「生物负载法」剂量设定（验证 SAL 10^-2、100 样本）；
    VDmax 为「证实 15/17.5/25 kGy 预定剂量」（验证 SAL 10^-1、10 样本、N0≤1000）。
    二者均需实验与标准抗性分布，本工具仅给粗算参考，勿据以放行。
    """
    if n0 <= 0:
        raise ValueError("--bioburden（生物负载 N0）须 > 0")
    if d10 <= 0:
        raise ValueError("--d10 须 > 0")
    if not (0 < sal < 1):
        raise ValueError("--sal 须在 (0, 1) 区间（SAL 为概率，默认 1e-6）")
    vd = d10 * math.log10(n0 / sal)
    return {
        "生物负载 N0(CFU)": n0, "D10(kGy)": d10, "SAL": sal,
        "估算剂量(kGy)": round(vd, 2),
        "说明": "简化估算 D=D10×log10(N0/SAL)。ISO 11137-2 Method 1（生物负载法）与 "
                "VDmax（15/17.5/25 kGy 预定剂量证实）为另一套需实验的方法，本值非其结论。",
    }


def clean_limit_pde(noael_mg_kg: float, body_kg: float, sf: float,
                    mdd_mg: float, area_cm2: float, recovery: float = 0.5) -> dict:
    """清洁验证：PDE → 单位面积擦拭限值（µg/cm²）。recovery = 擦拭回收率。

    口径说明（2026-10-12 复审修订）：
    - 限值按「全部 MDD 均经该设备接触」的保守口径（100% 占比）计算；
      mdd_mg 仅作记录，不引入占比假设（缺总 MDD 数据，不臆造折算系数）。
    - 10 ppm 经验法为 mg/kg（质量比）口径，与 µg/cm² 量纲不同，**不可直接比较**，
      仅作粗筛参考；以 PDE 法结果为准。
    - 回收率修正方向：测得值 = 实际残留 × recovery，故限值按 recovery 折算
      （回收率 50% 时测得限值为理论限值的一半）。
    """
    if sf <= 0:
        raise ValueError("--sf（安全因子）须 > 0")
    if area_cm2 <= 0:
        raise ValueError("--area（接触面积）须 > 0")
    if not (0 < recovery <= 1):
        raise ValueError("--recovery（擦拭回收率）须在 (0, 1] 区间")
    if noael_mg_kg < 0 or mdd_mg < 0 or body_kg <= 0:
        raise ValueError("NOAEL/MDD 须 ≥ 0 且体重须 > 0")
    pde_mg = noael_mg_kg * body_kg / sf
    # 测得限值(µg/cm²) = PDE × 1000 / 面积 × 回收率（保守 100% MDD 口径）
    limit_ug_cm2 = pde_mg * 1000 / area_cm2 * recovery
    ppm10 = 10.0  # ppm 经验限值（mg/kg 口径，PDA TR29 常用默认；仅粗筛参考）
    return {
        "PDE(mg/日)": round(pde_mg, 4),
        "体重(kg)": body_kg, "安全因子 SF": sf,
        "最大日剂量 MDD(mg)": mdd_mg, "接触面积(cm²)": area_cm2,
        "擦拭回收率": recovery,
        "擦拭限值(µg/cm²/日)": round(limit_ug_cm2, 4),
        "10ppm 经验法(mg/kg)": ppm10,
        "判据": "PASS（PDE 法；10 ppm 经验法为 mg/kg 口径，仅粗筛参考，不直接比较）",
        "口径说明": "PDE(mg/日)=NOAEL×体重/SF，为速率；本工具按「PDE 全部经该设备接触」"
                    "的保守口径直接摊到面积 → µg/(cm²·日)。标准 MACO 法为 "
                    "MACO=PDE×MBS/MDD 再除共用面积（需下一产品最小批量 MBS 与其最大日剂量 MDD），"
                    "本值未做批量折算，偏保守、非标准 MACO 值。"
                    "回收率修正方向：测得限值 = 理论限值 × recovery。",
    }


def endotoxin_limit(route: str, dose_ml_kg_h: float) -> dict:
    """内毒素：L = K / M。K 按给药途径（EU/kg/h），M = 最大剂量 mL/kg/h。"""
    k = ENDPOTOXIN_K.get(route)
    if k is None:
        raise ValueError(f"未知途径: {route}（可选 {sorted(ENDPOTOXIN_K)}）")
    if dose_ml_kg_h <= 0:
        raise ValueError("M 须 > 0")
    limit = k / dose_ml_kg_h
    return {
        "途径": route, "K(EU/kg/h)": k, "M(mL/kg/h)": dose_ml_kg_h,
        "内毒素限值(EU/mL)": round(limit, 3),
    }


def _parse_segments(s: str) -> list[tuple[float, float]]:
    """解析 'T:min,T:min'。非法输入转 ValueError（2026-10-12 压力测试修复）。"""
    segs = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"--f0 片段 '{part}' 须为「温度:分钟」，如 121.5:10")
        t, dtm = part.split(":", 1)
        try:
            segs.append((float(t), float(dtm)))
        except ValueError:
            raise ValueError(f"--f0 片段 '{part}' 含非数值")
    if not segs:
        raise ValueError("--f0 序列为空")
    return segs


def _fmt(title: str, d: dict) -> str:
    lines = [f"### {title}"]
    for k, v in d.items():
        lines.append(f"  - {k}: {v}")
    return "\n".join(lines)


def _demo() -> int:
    print("灭菌/清洁验证计算器 · 演示（数据为示例，非真实产品参数）\n")
    print(_fmt("EO 灭菌（BI 存活）", eo_survival(n0=1e5, d_value=2.8, t_min=4.0)))
    print(_fmt("湿热灭菌 F0", f0_accumulate([(121.5, 10.0), (118.0, 5.0)])))
    print(_fmt("辐照剂量估算（简化，非 ISO 11137-2 结论）", dose_vdmax(n0=100, d10=2.0)))
    print(_fmt("清洁验证限值（PDE 法，保守口径）",
               clean_limit_pde(noael_mg_kg=10, body_kg=70, sf=100, mdd_mg=50,
                               area_cm2=250)))
    print(_fmt("内毒素限值（K/M）", endotoxin_limit("iv", 0.5)))
    print("\n[demo] 计算模型按公开标准通用公式整理；SAL 为绝对口径(N≤1e-6)，"
          "辐照为简化估算；产品落地须以官方标准文本复核。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="灭菌/清洁验证计算器")
    ap.add_argument("--demo", action="store_true", help="跑内置演示")
    ap.add_argument("--selftest", action="store_true", help="跑内置自测（断言 + 负对照 + xfail）")
    ap.add_argument("--eo", action="store_true", help="EO BI 存活计算")
    ap.add_argument("--n0", type=float, default=1e5, help="初始 BI 数")
    ap.add_argument("--d", type=float, default=2.8, help="D 值（分钟）")
    ap.add_argument("--t", type=float, default=4.0, help="暴露时间（分钟）")
    ap.add_argument("--f0", help="湿热温度-时间序列，如 '121.5:10,118:5'")
    ap.add_argument("--z", type=float, default=10.0, help="z 值（°C）")
    ap.add_argument("--dose", action="store_true", help="辐照 VDmax 计算")
    ap.add_argument("--bioburden", type=float, default=100, help="生物负载 N0")
    ap.add_argument("--d10", type=float, default=2.0, help="D10（kGy）")
    ap.add_argument("--sal", type=float, default=SAL_DEFAULT, help="SAL，默认 1e-6")
    ap.add_argument("--clean", action="store_true", help="清洁验证 PDE 限值")
    ap.add_argument("--noael", type=float, default=10, help="NOAEL（mg/kg/日）")
    ap.add_argument("--body", type=float, default=70, help="体重（kg）")
    ap.add_argument("--sf", type=float, default=100, help="安全因子")
    ap.add_argument("--mdd", type=float, default=50, help="最大日剂量（mg）")
    ap.add_argument("--area", type=float, default=250, help="接触面积（cm²）")
    ap.add_argument("--recovery", type=float, default=0.5, help="擦拭回收率")
    ap.add_argument("--endotoxin", action="store_true", help="内毒素 K/M 限值")
    ap.add_argument("--route", default="iv", help="给药途径（iv/intrathecal/im/sc/implant）")
    ap.add_argument("--m", type=float, default=0.5, help="M：最大剂量 mL/kg/h")
    args = ap.parse_args()
    if getattr(args, "selftest", False):
        return _selftest()

    if args.demo:
        return _demo()
    try:
        if args.eo:
            print(_fmt("EO 灭菌（BI 存活）", eo_survival(args.n0, args.d, args.t)))
            return 0
        if args.f0:
            print(_fmt("湿热灭菌 F0", f0_accumulate(_parse_segments(args.f0), args.z)))
            return 0
        if args.dose:
            print(_fmt("辐照剂量设定", dose_vdmax(args.bioburden, args.d10, args.sal)))
            return 0
        if args.clean:
            print(_fmt("清洁验证限值", clean_limit_pde(args.noael, args.body, args.sf,
                                                      args.mdd, args.area, args.recovery)))
            return 0
        if args.endotoxin:
            print(_fmt("内毒素限值", endotoxin_limit(args.route, args.m)))
            return 0
    except ValueError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 2
    ap.print_help()
    return 2


# ==================== 内置自测（--selftest） ====================
# 由 conformance 补丁于 2026-10-14 生成（生成器 v2）。
# 特性：端到端 CLI 调用 + 内容断言 + 负对照 + xfail（已知缺陷显式标注，不掩盖）。
_SELFTEST_CASES = [(['--demo'], 0, ['F0', 'SAL'], [], None), (['--f0', '121.5:10,118:5', '--z', '10'], 0, ['13.41'], [], None), (['--eo', '--n0', '100000', '--d', '2.8', '--t', '4'], 0, ['3727.59'], [], None), (['--endotoxin', '--route', 'iv', '--m', '0.5'], 0, ['10.0'], [], None), (['--dose', '--bioburden', '100', '--d10', '2.0', '--sal', '1e-6'], 0, ['16.0'], [], None), (['--eo', '--n0', '0'], 2, [], [], None)]


def _selftest() -> int:
    import os as _os
    import subprocess as _sp
    _here = _os.path.dirname(_os.path.abspath(__file__))
    # 仓库根：脚本位于 <repo>/scripts/ 时取上一级；否则取脚本所在目录
    _root = _os.path.dirname(_here) if _os.path.basename(_here) == "scripts" else _here
    _script = _os.path.abspath(__file__)
    _fail, _xfail, _n = [], [], 0
    for _case in _SELFTEST_CASES:
        _args, _rc, _must, _mustnot = _case[0], _case[1], _case[2], _case[3]
        _reason = _case[4] if len(_case) > 4 else None
        _n += 1
        _p = _sp.run([sys.executable, _script] + _args, capture_output=True, cwd=_root)
        _out = _p.stdout.decode("utf-8", "replace")
        _bad = []
        if _p.returncode != _rc:
            _bad.append(f"rc={_p.returncode} 期望 {_rc}")
        for _m in _must:
            if _m not in _out:
                _bad.append(f"输出缺少 {_m!r}")
        for _m in _mustnot:
            if _m in _out:
                _bad.append(f"输出含禁止内容 {_m!r}")
        if _rc == 0 and not _out.strip():
            _bad.append("rc=0 但输出为空（假绿）")
        if _bad:
            if _reason:
                _xfail.append(f"xfail args={_args}：{'；'.join(_bad)} ← 已知缺陷：{_reason}")
            else:
                _fail.append(f"args={_args}：{'；'.join(_bad)}")
    # 通用负对照：未知参数必须非零
    _n += 1
    _p = _sp.run([sys.executable, _script, "--__nonexistent_flag__"], capture_output=True, cwd=_root)
    if _p.returncode == 0:
        _fail.append("负对照失败：未知参数竟返回 0")
    for _x in _xfail:
        print("[selftest][xfail] " + _x)
    if _fail:
        print(f"[selftest] FAILED {len(_fail)}/{_n}")
        for _f in _fail:
            print("  - " + _f)
        return 1
    print(f"[selftest] PASS {_n - len(_xfail)}/{_n}（含负对照；xfail {len(_xfail)} 项为已知缺陷）")
    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
