# AGENTS.md · sterilization-validation

> 机器可发现入口（AI 编码代理 / Codex / Claude / Cursor）。单一事实源：本文件。

## 这是什么
医疗器械灭菌与清洁验证的常用计算器：EO 灭菌 BI 存活分数与过度杀灭法判据、湿热灭菌 F0 累积、辐照灭菌 ISO 11137 Method 1 VDmax 剂量设定、清洁验证残留限值（PDE/单位面积法/10 ppm 经验法）、细菌内毒素限值（K/M 法）。覆盖骨科植入物清洁验证/内毒素检验的真实工程场景。

## 运行
```bash
python scripts/sterilization_val.py --demo
python scripts/sterilization_val.py --help
```

## 扩展契约（lgd-skeleton/1.0）
- **一切即插件**：仅依赖声明式 `module.json`，零配置。
- **按需装（lazy）**：仅 triggers 命中时加载。
- **可嵌套（nested）**：可被 `medical-ai-toolkit` 总入口路由。
- **扩展点**：`plugins/`(新增计算模型：在 MODELS 注册表加一个函数即可。)

## 红线
纯技术贡献，不含商业营销；MedXpert 仅作为贡献者署名（@stevenzhao07）。
