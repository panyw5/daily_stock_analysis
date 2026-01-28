# AI Agent Guide: daily_stock_analysis

This document provides essential context and instructions for AI agents working on the `daily_stock_analysis` project.

## 🏗 Project Architecture

The project follows a layered architecture to separate concerns:

1.  **Entry Points (Root Directory)**:
    *   `main.py`: The primary CLI entry point for scheduled or manual analysis runs.
    *   `webui.py`: Entry point for the local Web management interface.
    *   `history_analysis.py`: Independent CLI tool for deep historical data analysis.

2.  **Service Layer (`daily_stock_analysis/services.py`)**:
    *   The high-level API for all business logic.
    *   Functions: `analyze_stock()`, `analyze_stocks()`, `perform_market_review()`.
    *   **Agent Rule**: Always prefer using these service functions when adding new features to the Web or Bot layers.

3.  **Core Logic (`daily_stock_analysis/core/`)**:
    *   `pipeline.py`: Orchestrates the flow (Data Fetch -> Search -> AI Analysis -> Storage -> Notification).
    *   `market_review.py`: Logic for daily market summary.

4.  **Data Providers (`data_provider/`)**:
    *   Abstracts data fetching (AkShare, Tushare, Baostock, etc.).
    *   `base.py`: Defines the `BaseFetcher` interface.
    *   **Agent Rule**: When adding a new data source, inherit from `BaseFetcher` and register it in `DataFetcherManager`.

5.  **Analyzers & Search (`daily_stock_analysis/`)**:
    *   `analyzer.py`: AI model integration (Gemini, OpenAI compatible).
    *   `search_service.py`: Parallel news searching from multiple sources (Exa, Tavily, etc.).
    *   `stock_analyzer.py`: Technical indicator calculations using Pandas.

6.  **Interfaces**:
    *   `bot/`: Dispatchers and handlers for platforms (Telegram, DingTalk, Feishu).
    *   `web/`: Server-side logic for the WebUI.

## 🛠 Key Operations for Agents

### How to Run Analysis
*   Standard: `python main.py`
*   History Tool: `python history_analysis.py --stock 600519 --period 1m`
*   WebUI: `python webui.py`

### How to Import Core Features
Always use absolute imports from the package root:
```python
from daily_stock_analysis import analyze_stock, get_config, AnalysisResult
```

### Configuration Management
*   Configs are handled in `daily_stock_analysis/config.py`.
*   Settings are loaded from `.env`.
*   **Agent Rule**: Do not hardcode credentials. Use `get_config()`.

## 🚦 Coding Standards & Patterns

1.  **Strict Typing**: Use Python type hints everywhere.
2.  **Documentation**: All new functions must include docstrings in Chinese (matching existing style).
3.  **Logging**: Use the system logger from `logging.getLogger(__name__)`. Do not use `print()`.
4.  **Async/Parallel**: Search operations must remain parallel to avoid blocking.
5.  **No Refactor during Fix**: If fixing a bug, keep changes minimal. Refactor as a separate task.

## 🔍 Common Modification Tasks

*   **Adding an AI Model**: Modify `daily_stock_analysis/analyzer.py`.
*   **Adding a News Source**: Modify `daily_stock_analysis/search_service.py`.
*   **Modifying Notification Templates**: Check `daily_stock_analysis/notification.py`.
*   **Adding Technical Indicators**: Edit `daily_stock_analysis/stock_analyzer.py`.

## 📂 Directory Map
*   `data/`: SQLite database location.
*   `logs/`: Runtime logs (auto-rotated).
*   `reports/`: Generated Markdown reports.
*   `docs/`: Detailed project documentation and guides.
