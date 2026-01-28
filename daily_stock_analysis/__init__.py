# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 核心包
===================================

导出核心 API 供外部使用
"""

# 导出服务层 API
from .services import analyze_stock, analyze_stocks, perform_market_review

# 导出核心类型
from .analyzer import GeminiAnalyzer, AnalysisResult
from .config import get_config, Config
from .enums import ReportType

__all__ = [
    # 服务层
    "analyze_stock",
    "analyze_stocks",
    "perform_market_review",
    # 核心类型
    "GeminiAnalyzer",
    "AnalysisResult",
    "get_config",
    "Config",
    "ReportType",
]
