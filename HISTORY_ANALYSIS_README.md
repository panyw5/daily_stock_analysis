# 历史数据分析工具使用指南

## 📊 功能概述

`history_analysis.py` 是一个独立的股票历史数据分析工具，提供完整的技术分析和可选的 AI 智能分析功能。

### 核心特性

- ✅ **默认30天数据**：不指定周期时自动拉取近1个月数据
- ✅ **AI 智能分析默认启用**：自动使用 AI 分析器提供专业投资建议
- ✅ **多种时间周期**：支持 5日、1周、2周、1月、3月、6月、1年
- ✅ **完整技术指标**：均线、MACD、RSI、乖离率、成交量分析
- ✅ **批量分析**：支持多股票同时分析
- ✅ **自动报告生成**：Markdown 格式，包含 AI 分析结果

## 💻 快速开始

### 基础使用

```bash
# 分析单只股票（默认近1月数据，AI 分析已启用）
python history_analysis.py --stock 600519

# 指定时间周期
python history_analysis.py --stock 600519 --period 3m

# 指定日期范围
python history_analysis.py --stock 600519 --start-date 20260101 --end-date 20260114
```

### 禁用 AI 分析

```bash
# 如果不需要 AI 分析，可以使用 --no-ai 参数
python history_analysis.py --stock 600519 --no-ai
```

### 批量分析

```bash
# 同时分析多只股票（默认启用 AI）
python history_analysis.py --stock 600519,000001,300750 --period 1w

# 批量分析并禁用 AI
python history_analysis.py --stock 600519,000001 --no-ai
```

## 📋 命令行参数

| 参数             | 说明                     | 示例                      | 默认值   |
| ---------------- | ------------------------ | ------------------------- | -------- |
| `--stock`      | 股票代码（必需，可多个） | `--stock 600519,000001` | -        |
| `--period`     | 时间周期                 | `--period 3m`           | `1m`   |
| `--start-date` | 开始日期                 | `--start-date 20260101` | -        |
| `--end-date`   | 结束日期                 | `--end-date 20260114`   | 今天     |
| `--no-ai`      | 禁用 AI 分析             | `--no-ai`               | 启用     |
| `--output`     | 输出文件路径             | `--output report.md`    | 自动生成 |

### 支持的时间周期

- `5d` - 5天
- `1w` - 1周
- `2w` - 2周
- `1m` - 1月（默认）
- `3m` - 3月
- `6m` - 6月
- `1y` - 1年

## 📊 报告内容

生成的报告包含以下内容：

### 1. 基本信息

- 分析日期
- 数据周期
- 数据条数

### 2. 最新行情

- 收盘价
- 涨跌幅

### 3. 🤖 AI 智能分析（启用 --ai 时）

- 操作建议（买入/观望/卖出）
- 核心结论
- 买卖点位
- 风险提示
- 利好因素

### 4. 均线分析

- MA5、MA10、MA20、MA60
- 趋势判断（多头/空头/震荡）
- 乖离率

### 5. MACD 指标

- DIF、DEA、MACD
- 金叉/死叉信号

### 6. RSI 指标

- RSI(14)
- 超买/超卖/正常状态

### 7. 成交量分析

- 最新成交量
- 5日均量
- 量比

### 8. 价格统计

- 最高价、最低价
- 振幅、平均价

## 🎯 使用场景

### 日常监控

快速查看近期走势和技术指标

```bash
python history_analysis.py --stock 600519
```

### 深度分析

使用 3月/6月周期查看中长期趋势（AI 分析已启用）

```bash
python history_analysis.py --stock 600519 --period 3m
```

### 批量筛选

同时分析多只股票，快速筛选机会（AI 分析已启用）

```bash
python history_analysis.py --stock 600519,000001,300750 --period 1w
```

### 历史回测

指定日期范围，回顾历史走势

```bash
python history_analysis.py --stock 600519 --start-date 20250101 --end-date 20251231
```

### 仅技术分析

如果只需要技术指标，不需要 AI 分析

```bash
python history_analysis.py --stock 600519 --no-ai
```

## ⚙️ 配置 AI 分析

AI 分析功能默认启用。要使用 AI 分析，需要配置 Gemini API Key 或 OpenAI API Key（支持 OpenAI 兼容 API）：

### 方法1：配置 Gemini API Key

```bash
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### 方法2：配置 OpenAI API Key

```bash
# OpenAI 官方 API
echo "OPENAI_API_KEY=your_key_here" >> .env

# 或使用 OpenAI 兼容 API（如 DeepSeek、通义千问等）
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "OPENAI_BASE_URL=http://127.0.0.1:3000/v1" >> .env
echo "OPENAI_MODEL=claude-sonnet-4.5" >> .env
```

**说明**：

- 系统会优先使用 Gemini API
- 如果 Gemini API 未配置或失败，会自动切换到 OpenAI API
- 支持所有 OpenAI 格式的 API（OpenAI、DeepSeek、通义千问、Moonshot 等）

## 📁 输出文件

报告默认保存在 `reports/` 目录下：

```
reports/
└── history_STOCKCODE_TIMESTAMP.md
```

例如：`reports/history_600519_20260115_093303.md`

## 🔧 技术指标说明

### 均线（MA）

- **MA5**：5日均线，短期趋势
- **MA10**：10日均线，中短期趋势
- **MA20**：20日均线，中期趋势
- **MA60**：60日均线，长期趋势

### 趋势判断

- **多头排列**：MA5 > MA10 > MA20
- **空头排列**：MA5 < MA10 < MA20
- **震荡**：其他情况

### 乖离率

衡量股价偏离均线的程度：

- **< 2%**：最佳买点区间
- **2-5%**：可小仓介入
- **> 5%**：严禁追高

### MACD

- **金叉**：DIF 上穿 DEA，看涨信号
- **死叉**：DIF 下穿 DEA，看跌信号

### RSI

- **> 70**：超买，可能回调
- **< 30**：超卖，可能反弹
- **30-70**：正常区间

### 量比

当日成交量与5日均量的比值：

- **> 1.5**：放量
- **< 0.8**：缩量
- **0.8-1.5**：正常

## 💡 使用建议

1. **日常使用**：直接运行 `python history_analysis.py --stock 600519` 即可获取近1月分析
2. **深度分析**：使用 `--period 3m` 或 `--period 6m` 查看更长周期
3. **AI 辅助**：配置 Gemini API Key 后使用 `--ai` 参数获取专业投资建议
4. **批量监控**：使用逗号分隔多个股票代码进行批量分析

## ⚠️ 注意事项

1. **数据来源**：使用 akshare 获取数据，可能受网络影响
2. **AI 分析**：需要配置 Gemini API Key，否则只提供技术指标分析
3. **投资风险**：分析结果仅供参考，不构成投资建议
4. **数据延迟**：历史数据可能有延迟，请以实际交易数据为准

## 🆚 与主程序的区别

| 特性     | main.py        | history_analysis.py |
| -------- | -------------- | ------------------- |
| 用途     | 日常分析和监控 | 历史数据分析和回测  |
| 数据范围 | 最近30天       | 可指定任意时间段    |
| AI 分析  | 默认启用       | 需要 --ai 参数      |
| 批量分析 | 支持           | 支持                |
| 报告格式 | 决策仪表盘     | 技术分析报告        |
| 数据库   | 使用           | 不使用              |
| 通知推送 | 支持           | 不支持              |

## 📞 获取帮助

查看完整的命令行帮助：

```bash
python history_analysis.py --help
```

## 🔗 相关文档

- [主程序使用指南](README.md)
- [技术参考文档](.claude/skills/analyze/REFERENCE.md)
- [配置说明](CONFIG.md)
