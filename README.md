# sterilization-validation

> **Contributed by [@stevenzhao07](https://github.com/stevenzhao07) · Affiliation: MedXpert (medical-device RA & regulatory consultancy) · Pure technical input, no commercial promotion.**

医疗器械灭菌与清洁验证的常用计算器：EO 灭菌 BI 存活分数与过度杀灭法判据、湿热灭菌 F0 累积、辐照灭菌 ISO 11137 Method 1 VDmax 剂量设定、清洁验证残留限值（PDE/单位面积法/10 ppm 经验法）、细菌内毒素限值（K/M 法）。覆盖骨科植入物清洁验证/内毒素检验的真实工程场景。

这是 MedXpert 把"医疗 AI 信任"方法论工程化落地的可插拔模块之一——把抽象的合规要求变成一条可重复运行的命令或参考实现。方法论四要素（白话版）：**治理守护者 XCGS** ＝ 为 AI 留下可核验的治理证据；**立法者 A³ Laws** ＝ 给自主系统划权限 / 监督 / 追责三条硬边界；**护照官 AI 护照** ＝ 为模型签发可追溯的身份凭证；**人机共存** ＝ 明确人类与 AI 的分工与兜底。

---

## 可插拔模块契约（lgd-skeleton/1.0）

本仓库是一个 **`lgd-skeleton/1.0` 可插拔模块**：

- **一切即插件**：仅依赖声明式 `module.json`，零配置；
- **按需装（lazy）**：仅 triggers 命中时加载；
- **可嵌套（nested）**：可被 `medical-ai-toolkit` 总入口路由发现；
- **扩展点**：`plugins/`(新增计算模型：在 MODELS 注册表加一个函数即可。)。

机器可发现入口：`AGENTS.md` · `CLAUDE.md` · `llms.txt`。

## 特性

- EO：BI 存活分数 N=N0×10^(-t/D)，半周期过度杀灭 6 log 判据（SAL 10^-6）
- 湿热：F0=Δt×10^((T-121.1)/z) 逐段累积，支持温度-时间序列输入
- 辐照：ISO 11137 Method 1 VDmax=D10×log10(N0/SAL)，支持自定义生物负载
- 清洁验证：PDE→单位面积擦拭限值 / 冲洗限值 + 10 ppm 经验法对照
- 内毒素：K/M 法限值（K 按给药途径：静脉 5、椎管内 0.2 EU/kg/h）

## 内容说明

计算模型依据公开标准的通用公式整理（ISO 11135/11137/17665、PDA TR29 清洁验证思路、药典细菌内毒素检查法）。落地具体产品须结合已验证的 D 值/z 值/生物负载数据与官方文本复核。

## 使用

```bash
python scripts/sterilization_val.py --demo
python scripts/sterilization_val.py --f0 121.5:10,118:5
python scripts/sterilization_val.py --eo --d 2.8 --t 4
python scripts/sterilization_val.py --endotoxin --route iv --m 0.5
```

> 内毒素限值用 `--m`（M：最大剂量 mL/kg/h）；`--dose` 是辐照 VDmax 开关，不取值。

## 免责声明

本工具为工程计算参考实现，**不构成医疗或法规建议**。所有输出须由合格专业人员结合官方标准文本与产品具体数据（已验证的 D 值/z 值/生物负载/NOAEL 等）复核后使用；安全关键判定（无菌保证、热原限值、清洁残留）以官方标准与注册申报文件为准。

## 快速开始（30 秒）

```bash
git clone https://github.com/stevenzhao07/sterilization-validation.git && cd sterilization-validation
python scripts/sterilization_val.py --demo
```

> 想参与或遇到问题？[提 Issue](https://github.com/stevenzhao07/sterilization-validation/issues) · 完整《AI 参与指南》见 [medical-ai-toolkit](https://github.com/stevenzhao07/medical-ai-toolkit)。

## 路由（总入口）

本模块由 **[medical-ai-toolkit](https://github.com/stevenzhao07/medical-ai-toolkit)** 作为 `lgd-skeleton/1.0` 总入口自动路由发现。

## 关联模块

- [manufacturing-gmp](https://github.com/stevenzhao07/manufacturing-gmp)
- [biocompatibility-iso10993](https://github.com/stevenzhao07/biocompatibility-iso10993)
- [design-controls-toolkit](https://github.com/stevenzhao07/design-controls-toolkit)

## 许可

Apache-2.0 — 见 [LICENSE](./LICENSE)。

## 关联（方法论来源）

- 理念溯源：个人专家关于医疗 AI 信任与治理的公开方法论（个人观点，不构成标准）
- 同账号系列：见 `medical-ai-toolkit` 导航
