# -*- coding: utf-8 -*-
"""
===================================
数据源策略层 - 包初始化
===================================

本包实现策略模式管理多个数据源，实现：
1. 统一的数据获取接口
2. 自动故障切换
3. 防封禁流控策略

数据源优先级（根据 2026-01-29 测试结果优化）：

【配置了 TUSHARE_TOKEN 时】- 推荐配置
1. TushareFetcher (Priority 0) - 🔥 主力数据源（100% 可用，120积分）
2. BaostockFetcher (Priority 0) - 🔥 备用数据源（100% 可用，完全免费）
3. EfinanceFetcher (Priority 1) - 实时行情专用
4. AkshareFetcher (Priority 2) - ⚠️ 仅用于财务数据和资金流向（东方财富接口不可用）
5. YfinanceFetcher (Priority 4) - 美股专用

【未配置 TUSHARE_TOKEN 时】
1. BaostockFetcher (Priority 0) - 🔥 主力数据源（100% 可用，完全免费）
2. EfinanceFetcher (Priority 1) - 实时行情专用
3. AkshareFetcher (Priority 2) - ⚠️ 仅用于财务数据和资金流向
4. TushareFetcher (Priority 3) - 不可用（需要 Token）
5. YfinanceFetcher (Priority 4) - 美股专用

测试结果摘要（2026-01-29）：
- TuShare (120积分): 100% 可用 ⭐⭐⭐⭐⭐
- Baostock: 100% 可用 ⭐⭐⭐⭐⭐
- AkShare: 40% 可用（东方财富接口故障）⭐⭐
- 详见: reports/interface_test_final_report.md

提示：优先级数字越小越优先，同优先级按初始化顺序排列
"""

from .base import BaseFetcher, DataFetcherManager
from .efinance_fetcher import EfinanceFetcher
from .akshare_fetcher import AkshareFetcher
from .tushare_fetcher import TushareFetcher
from .baostock_fetcher import BaostockFetcher
from .yfinance_fetcher import YfinanceFetcher

__all__ = [
    "BaseFetcher",
    "DataFetcherManager",
    "EfinanceFetcher",
    "AkshareFetcher",
    "TushareFetcher",
    "BaostockFetcher",
    "YfinanceFetcher",
]
