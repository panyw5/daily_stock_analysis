# Analyze Skill - 技术参考文档

## 命令行参数详解

### 基础命令

```bash
# 个股分析
python main.py --stocks 600519,300750,002594

# 大盘复盘
python main.py --market-review

# 历史数据分析
python history_analysis.py --stock 600519
```

### 主程序参数 (main.py)

| 参数                   | 说明                       | 示例                       |
| ---------------------- | -------------------------- | -------------------------- |
| `--stocks`           | 股票代码列表（逗号分隔）   | `--stocks 600519,300750` |
| `--debug`            | 启用调试模式，输出详细日志 | `--debug`                |
| `--dry-run`          | 仅获取数据，不进行 AI 分析 | `--dry-run`              |
| `--no-notify`        | 不发送推送通知             | `--no-notify`            |
| `--workers`          | 并发线程数                 | `--workers 5`            |
| `--market-review`    | 仅运行大盘复盘分析         | `--market-review`        |
| `--no-market-review` | 跳过大盘复盘分析           | `--no-market-review`     |
| `--date`             | 指定分析日期（大盘复盘）   | `--date 20260114`        |

### 历史数据分析参数 (history_analysis.py)

| 参数                   | 说明                       | 示例                       |
| ---------------------- | -------------------------- | -------------------------- |
| `--stock`            | 股票代码（必需，可多个）   | `--stock 600519,000001`  |
| `--period`           | 时间周期（默认1月）        | `--period 3m`            |
| `--start-date`       | 开始日期                   | `--start-date 20260101`  |
| `--end-date`         | 结束日期                   | `--end-date 20260114`    |
| `--no-ai`            | 禁用 AI 分析（默认启用）   | `--no-ai`                |
| `--output`           | 输出文件路径               | `--output report.md`     |

#### 支持的时间周期

- `5d` - 5天
- `1w` - 1周
- `2w` - 2周
- `1m` - 1月（默认）
- `3m` - 3月
- `6m` - 6月
- `1y` - 1年

### 组合使用示例

```bash
# 主程序示例
# ============

# 仅分析个股，不做大盘复盘
python main.py --stocks 600519,300750 --no-market-review

# 调试模式分析
python main.py --stocks 600519 --debug

# 仅大盘复盘
python main.py --market-review

# 查询历史日期的大盘数据
python main.py --market-review --date 20260114

# 历史数据分析示例
# ==================

# 基础使用（默认近1月数据，AI 分析已启用）
python history_analysis.py --stock 600519

# 指定时间周期
python history_analysis.py --stock 600519 --period 3m

# 指定日期范围
python history_analysis.py --stock 600519 --start-date 20260101 --end-date 20260114

# 批量分析多只股票（AI 分析已启用）
python history_analysis.py --stock 600519,000001 --period 1w

# 禁用 AI 分析（仅技术指标）
python history_analysis.py --stock 600519 --no-ai

# 组合使用
python history_analysis.py --stock 600519 --period 3m --output my_report.md
```

## 历史数据分析工具说明

### 功能特性

1. **默认30天数据**：不指定周期时自动拉取近1个月数据
2. **AI 智能分析默认启用**：自动使用 AI 分析器提供专业投资建议
3. **完整技术指标**：
   - 均线：MA5、MA10、MA20、MA60
   - MACD：DIF、DEA、MACD、金叉/死叉信号
   - RSI：14日相对强弱指标、超买/超卖状态
   - 乖离率：相对各均线的偏离程度
   - 成交量：量比、5日均量
4. **趋势分析**：多头/空头/震荡判断
5. **批量分析**：支持多股票同时分析
6. **自动报告**：生成 Markdown 格式报告

### 报告内容

生成的报告包含：

1. **基本信息**：分析日期、数据周期、数据条数
2. **最新行情**：收盘价、涨跌幅
3. **🤖 AI 智能分析**（启用 --ai 时）：
   - 操作建议（买入/观望/卖出）
   - 核心结论
   - 买卖点位
   - 风险提示
   - 利好因素
4. **均线分析**：MA5/10/20/60、趋势判断、乖离率
5. **MACD 指标**：DIF、DEA、MACD、金叉/死叉信号
6. **RSI 指标**：RSI(14)、超买/超卖/正常状态
7. **成交量分析**：最新成交量、5日均量、量比
8. **价格统计**：最高价、最低价、振幅、平均价

### 使用场景

- **日常监控**：快速查看近期走势和技术指标
- **深度分析**：使用 3月/6月周期查看中长期趋势
- **AI 辅助决策**：启用 AI 分析获取专业投资建议
- **批量筛选**：同时分析多只股票，快速筛选机会
- **历史回测**：指定日期范围，回顾历史走势

## 文件结构

```
daily_stock_analysis/
├── main.py                 # 主程序入口
├── history_analysis.py     # 历史数据分析工具（新增）
├── analyzer.py             # AI 分析器
├── market_analyzer.py      # 大盘复盘分析
├── notification.py         # 消息推送
├── data/                   # 数据库目录
│   └── stock_analysis.db   # SQLite 数据库
├── logs/                   # 日志目录
│   ├── stock_analysis_YYYYMMDD.log       # 常规日志
│   └── stock_analysis_debug_YYYYMMDD.log # 调试日志
└── reports/                # 报告目录
    ├── report_YYYYMMDD.md                # 个股分析报告
    ├── market_review_YYYYMMDD.md         # 大盘复盘报告
    └── history_STOCKCODE_TIMESTAMP.md    # 历史数据分析报告（新增）
```

## 错误处理指南

### 常见错误及解决方案

#### 1. API Key 未配置

**错误信息**: `WARNING | 提示：未配置 Gemini API Key` 或 `AI 分析功能将被禁用`

**解决方案**:

系统支持 Gemini API 和 OpenAI API（包括 OpenAI 兼容 API），可以配置其中任意一个：

```bash
# 方法1: 配置 Gemini API Key
echo "GEMINI_API_KEY=your_key_here" >> .env

# 方法2: 配置 OpenAI API Key
echo "OPENAI_API_KEY=your_key_here" >> .env

# 方法3: 使用 OpenAI 兼容 API（如 DeepSeek、通义千问等）
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "OPENAI_BASE_URL=http://127.0.0.1:3000/v1" >> .env
echo "OPENAI_MODEL=claude-sonnet-4.5" >> .env
```

**说明**：
- 系统会优先使用 Gemini API
- 如果 Gemini API 未配置或失败，会自动切换到 OpenAI API
- 支持所有 OpenAI 格式的 API

#### 2. 网络超时

**错误信息**: `获取数据失败: timeout`

**解决方案**:

- 检查网络连接
- 如果在国内，可能需要配置代理
- 增加超时时间（修改 `config.py`）

#### 3. 股票代码无效

**错误信息**: `获取数据为空`

**解决方案**:

- 确认股票代码格式正确（6位数字）
- 检查股票是否已退市或停牌
- 使用 A 股代码（不支持港股、美股）

#### 4. 数据库锁定

**错误信息**: `database is locked`

**解决方案**:

- 等待其他进程完成
- 删除 `data/stock_analysis.db-journal` 文件
- 重启程序

## 技术指标说明

### 均线系统 (MA)

- **MA5**: 5日移动平均线，代表短期趋势
- **MA10**: 10日移动平均线，代表中短期趋势
- **MA20**: 20日移动平均线，代表中期趋势

**多头排列**: MA5 > MA10 > MA20，趋势向上
**空头排列**: MA5 < MA10 < MA20，趋势向下

### 乖离率 (BIAS)

- 计算公式: `(当前价 - MA) / MA × 100%`
- 安全区间: -5% ~ +5%
- 超过 5%: 追高风险，不建议买入
- 低于 -5%: 超跌，可能反弹

### 量比

- 计算公式: `当前成交量 / 过去5日平均成交量`
- < 0.5: 极度萎缩
- 0.5 ~ 0.8: 明显萎缩
- 0.8 ~ 1.2: 正常
- 1.2 ~ 2.0: 温和放量
- 2.0 ~ 3.0: 明显放量
- > 3.0: 巨量
  >

### 筹码分布

- **获利比例**: 当前价格以下的筹码占比
- **平均成本**: 所有筹码的平均买入价格
- **集中度**: 筹码的分散程度（越低越集中）

## 性能优化建议

### 1. 并发控制

- 默认并发数: 3
- 建议范围: 2-5
- 过高可能触发反爬机制

### 2. 缓存策略

- 数据库自动缓存历史数据
- 同一天重复分析会使用缓存
- 使用 `--force-refresh` 强制刷新（需要修改代码添加此参数）

### 3. API 调用优化

- 优先使用 AkShare（免费）
- Tushare 作为备选（需要 Token）
- 搜索服务可选（Tavily/SerpAPI）

## 扩展功能开发指南

### 添加新的股票名称映射

编辑 `analyzer.py` 中的 `STOCK_NAME_MAP`:

```python
STOCK_NAME_MAP = {
    '600519': '贵州茅台',
    '300750': '宁德时代',
    '002594': '比亚迪',
    # 添加新的映射
    '000858': '五粮液',
}
```

### 自定义分析策略

修改 `analyzer.py` 中的 `ANALYSIS_PROMPT`:

```python
ANALYSIS_PROMPT = """
你的自定义分析策略...
"""
```

### 添加新的通知渠道

编辑 `notification.py`，实现新的通知类:

```python
class CustomNotifier:
    def send(self, message):
        # 实现你的通知逻辑
        pass
```

## 常见问题 FAQ

### Q1: 为什么分析结果和实际走势不一致？

A: AI 分析基于历史数据和技术指标，无法预测突发事件和政策变化。建议结合基本面和消息面综合判断。

### Q2: 可以分析港股和美股吗？

A: 目前仅支持 A 股。港股和美股需要不同的数据源和 API。

### Q3: 分析报告可以导出为 PDF 吗？

A: 报告默认为 Markdown 格式。可以使用 Pandoc 等工具转换为 PDF。

### Q4: 如何提高分析准确度？

A:

- 配置搜索服务（Tavily/SerpAPI）获取新闻情报
- 使用更强大的 AI 模型（如 GPT-4）
- 结合多个技术指标综合判断

### Q5: 可以自动交易吗？

A: 本系统仅提供分析建议，不支持自动交易。强烈建议人工审核后再操作。

## 更新日志

### v1.1.0 (2026-01-15)

- ✅ 优化 SKILL.md 结构
- ✅ 增加分层报告展示
- ✅ 增加错误处理指南
- ✅ 增加常见股票代码映射
- ✅ 增加交互式问答

### v1.0.0 (2026-01-10)

- 🎉 初始版本发布
- 支持多股票批量分析
- 支持大盘复盘
- 支持多种通知渠道

## 贡献指南

欢迎提交 Issue 和 Pull Request！

详见项目主 README.md 的贡献指南部分。

## 许可证

MIT License

---

**最后更新**: 2026-01-15
**维护者**: Claude Code Skill Team
