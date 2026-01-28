# README 更新建议

## 在 "数据来源" 部分添加

### 当前内容（第26-31行）：
```markdown
### 📊 数据来源
- **行情数据**: AkShare（免费）、Tushare、Baostock、YFinance
- **新闻搜索**: Tavily、Exa、SerpAPI、Bocha
- **AI 分析**: 
  - 主力：Google Gemini（gemini-3-flash-preview）—— [免费获取](https://aistudio.google.com/)
  - 备选：应大家要求，也支持了OpenAI 兼容 API（DeepSeek、通义千问、Moonshot 等）
```

### 建议更新为：
```markdown
### 📊 数据来源
- **行情数据**: AkShare（免费）、Tushare、Baostock、YFinance
- **新闻搜索**: 
  - 主力：华尔街见闻 7x24 快讯（**完全免费，无需配置**）
  - 备选：Tavily、Exa、SerpAPI、Bocha
- **AI 分析**: 
  - 主力：Google Gemini（gemini-3-flash-preview）—— [免费获取](https://aistudio.google.com/)
  - 备选：应大家要求，也支持了OpenAI 兼容 API（DeepSeek、通义千问、Moonshot 等）
```

---

## 在 "功能特性" 部分添加

### 在第24行后添加：
```markdown
- **🆓 免费新闻源** - 华尔街见闻 7x24 实时快讯，无需 API Key
```

---

## 在 "其他配置" 表格中更新

### 当前内容（第91行）：
```markdown
| `TAVILY_API_KEYS` | [Tavily](https://tavily.com/) 搜索 API（新闻搜索） | 推荐 |
```

### 建议更新为：
```markdown
| `TAVILY_API_KEYS` | [Tavily](https://tavily.com/) 搜索 API（备用新闻搜索） | 可选 |
```

### 在第91行前添加说明：
```markdown
> 💡 **新闻搜索说明**：系统已内置华尔街见闻 7x24 快讯（完全免费），无需配置任何 API Key 即可获取实时财经新闻。以下搜索引擎作为备选，可选配置。
```

---

## 在 Roadmap 部分更新

### 在 "数据源扩展" 部分（第228行）添加：
```markdown
### 📊 数据源扩展
- [x] AkShare（免费）
- [x] Tushare Pro
- [x] Baostock
- [x] YFinance
- [x] 华尔街见闻（7x24 快讯，免费）
```

---

## 可选：添加新的章节

### 在 "配置说明" 后添加：

```markdown
## 🆓 免费资源说明

本项目致力于降低使用门槛，提供多种免费资源：

### 完全免费（无需配置）
- ✅ **华尔街见闻** - 7x24 实时财经快讯，系统已内置
- ✅ **AkShare** - 免费行情数据接口

### 免费额度（需注册）
- 🔑 **Google Gemini** - 免费 API，个人使用完全够用
- 🔑 **Tavily** - 1000次/月免费搜索
- 🔑 **SerpAPI** - 100次/月免费搜索

### 推荐配置
对于个人用户，推荐以下最小配置即可正常使用：
1. 注册 Google Gemini API（免费）
2. 使用华尔街见闻获取新闻（无需配置）
3. 配置一个通知渠道（企业微信/飞书/Telegram）

**总成本：0 元** 🎉
```

---

## 完整的更新位置总结

1. **第26-31行** - 更新数据来源说明
2. **第24行后** - 添加免费新闻源特性
3. **第91行前** - 添加新闻搜索说明
4. **第228行** - 更新数据源扩展列表
5. **可选** - 添加免费资源说明章节

---

## 实施建议

可以选择以下方式之一：

### 方式一：最小更新
只更新 "数据来源" 部分，说明华尔街见闻已集成。

### 方式二：完整更新
按照上述所有建议更新 README，让用户更清楚地了解免费资源。

### 方式三：渐进更新
先更新核心部分（数据来源、功能特性），后续再添加详细说明。

---

**建议采用方式二（完整更新）**，这样可以：
- 突出项目的零成本优势
- 降低新用户的使用门槛
- 提升项目的吸引力
