# -*- coding: utf-8 -*-
"""
===================================
大盘复盘分析模块
===================================

职责：
1. 获取大盘指数数据（上证、深证、创业板）
2. 搜索市场新闻形成复盘情报
3. 使用大模型生成每日大盘复盘报告
"""

import logging
import re
import requests
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

import akshare as ak
import pandas as pd

from config import get_config
from search_service import SearchService

logger = logging.getLogger(__name__)


def _fetch_qq_index_data(codes: List[str]) -> Dict[str, Dict]:
    """
    直接从腾讯接口获取指数数据（AkShare 备用方案）
    
    腾讯接口格式: v_sh000001="1~上证指数~000001~价格~昨收~开盘~成交量~...~涨跌额~涨跌幅~最高~最低~..."
    """
    result = {}
    code_map = {
        '000001': 'sh000001',
        '399001': 'sz399001', 
        '399006': 'sz399006',
        '000688': 'sh000688',
        '000016': 'sh000016',
        '000300': 'sh000300',
    }
    
    qq_codes = [code_map[c] for c in codes if c in code_map]
    if not qq_codes:
        return result
        
    try:
        url = f"https://qt.gtimg.cn/q={','.join(qq_codes)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'gbk'
        
        for line in resp.text.strip().split(';'):
            if not line.strip():
                continue
            match = re.match(r'v_(\w+)="(.+)"', line.strip())
            if match:
                qq_code = match.group(1)
                data = match.group(2).split('~')
                if len(data) >= 45:
                    std_code = qq_code[2:]
                    result[std_code] = {
                        'name': data[1],
                        'current': float(data[3]) if data[3] else 0,
                        'prev_close': float(data[4]) if data[4] else 0,
                        'open': float(data[5]) if data[5] else 0,
                        'volume': float(data[6]) if data[6] else 0,
                        'change': float(data[31]) if data[31] else 0,
                        'change_pct': float(data[32]) if data[32] else 0,
                        'high': float(data[33]) if data[33] else 0,
                        'low': float(data[34]) if data[34] else 0,
                    }
    except Exception as e:
        logger.warning(f"[大盘] 腾讯直连接口失败: {e}")
    
    return result


@dataclass
class MarketIndex:
    """大盘指数数据"""
    code: str                    # 指数代码
    name: str                    # 指数名称
    current: float = 0.0         # 当前点位
    change: float = 0.0          # 涨跌点数
    change_pct: float = 0.0      # 涨跌幅(%)
    open: float = 0.0            # 开盘点位
    high: float = 0.0            # 最高点位
    low: float = 0.0             # 最低点位
    prev_close: float = 0.0      # 昨收点位
    volume: float = 0.0          # 成交量（手）
    amount: float = 0.0          # 成交额（元）
    amplitude: float = 0.0       # 振幅(%)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'current': self.current,
            'change': self.change,
            'change_pct': self.change_pct,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            'amount': self.amount,
            'amplitude': self.amplitude,
        }


@dataclass
class MarketOverview:
    """市场概览数据"""
    date: str                           # 日期
    indices: List[MarketIndex] = field(default_factory=list)  # 主要指数
    up_count: int = 0                   # 上涨家数
    down_count: int = 0                 # 下跌家数
    flat_count: int = 0                 # 平盘家数
    limit_up_count: int = 0             # 涨停家数
    limit_down_count: int = 0           # 跌停家数
    total_amount: float = 0.0           # 两市成交额（亿元）
    north_flow: float = 0.0             # 北向资金净流入（亿元）
    
    # 板块涨幅榜
    top_sectors: List[Dict] = field(default_factory=list)     # 涨幅前5板块
    bottom_sectors: List[Dict] = field(default_factory=list)  # 跌幅前5板块


class MarketAnalyzer:
    """
    大盘复盘分析器
    
    功能：
    1. 获取大盘指数实时行情
    2. 获取市场涨跌统计
    3. 获取板块涨跌榜
    4. 搜索市场新闻
    5. 生成大盘复盘报告
    """
    
    # 主要指数代码
    MAIN_INDICES = {
        '000001': '上证指数',
        '399001': '深证成指',
        '399006': '创业板指',
        '000688': '科创50',
        '000016': '上证50',
        '000300': '沪深300',
    }
    
    def __init__(self, search_service: Optional[SearchService] = None, analyzer=None):
        """
        初始化大盘分析器
        
        Args:
            search_service: 搜索服务实例
            analyzer: AI分析器实例（用于调用LLM）
        """
        self.config = get_config()
        self.search_service = search_service
        self.analyzer = analyzer
        
    def get_market_overview(self, target_date: Optional[str] = None) -> MarketOverview:
        """
        获取市场概览数据

        Args:
            target_date: 目标日期，格式：YYYYMMDD 或 YYYY-MM-DD（可选，默认为今天）

        Returns:
            MarketOverview: 市场概览数据对象
        """
        # 标准化日期格式
        if target_date:
            # 移除可能的连字符
            date_str = target_date.replace('-', '')
            # 转换为 YYYY-MM-DD 格式
            if len(date_str) == 8:
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                formatted_date = target_date
        else:
            formatted_date = datetime.now().strftime('%Y-%m-%d')

        overview = MarketOverview(date=formatted_date)

        # 1. 获取主要指数行情
        overview.indices = self._get_main_indices(target_date=target_date)

        # 2. 获取涨跌统计
        self._get_market_statistics(overview)

        # 3. 获取板块涨跌榜
        self._get_sector_rankings(overview)

        # 4. 获取北向资金（可选）
        self._get_north_flow(overview)

        return overview
    
    def _get_main_indices(self, target_date: Optional[str] = None) -> List[MarketIndex]:
        """
        获取主要指数行情

        Args:
            target_date: 目标日期，格式：YYYYMMDD 或 YYYY-MM-DD（可选，默认为今天实时数据）

        Returns:
            指数列表
        """
        indices = []

        try:
            if target_date:
                # 获取历史数据
                logger.info(f"[大盘] 获取 {target_date} 的历史指数数据...")
                # 标准化日期格式为 YYYYMMDD
                date_str = target_date.replace('-', '')

                for code, name in self.MAIN_INDICES.items():
                    try:
                        # 使用 akshare 获取指数历史数据
                        df = ak.stock_zh_index_daily(symbol=f"sh{code}" if code.startswith('0') else f"sz{code}")

                        if df is not None and not df.empty:
                            # 查找指定日期的数据
                            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y%m%d')
                            target_row = df[df['date'] == date_str]

                            if not target_row.empty:
                                row = target_row.iloc[0]
                                # 获取前一交易日数据用于计算涨跌
                                row_idx = df[df['date'] == date_str].index[0]
                                if row_idx > 0:
                                    prev_row = df.iloc[row_idx - 1]
                                    prev_close = float(prev_row.get('close', 0) or 0)
                                else:
                                    prev_close = float(row.get('close', 0) or 0)

                                current_price = float(row.get('close', 0) or 0)
                                change = current_price - prev_close
                                change_pct = (change / prev_close * 100) if prev_close > 0 else 0

                                index = MarketIndex(
                                    code=code,
                                    name=name,
                                    current=current_price,
                                    change=change,
                                    change_pct=change_pct,
                                    open=float(row.get('open', 0) or 0),
                                    high=float(row.get('high', 0) or 0),
                                    low=float(row.get('low', 0) or 0),
                                    prev_close=prev_close,
                                    volume=float(row.get('volume', 0) or 0),
                                    amount=float(row.get('amount', 0) or 0),
                                )
                                # 计算振幅
                                if index.prev_close > 0:
                                    index.amplitude = (index.high - index.low) / index.prev_close * 100
                                indices.append(index)
                            else:
                                logger.warning(f"[大盘] 未找到 {name}({code}) 在 {target_date} 的数据")
                    except Exception as e:
                        logger.warning(f"[大盘] 获取 {name}({code}) 历史数据失败: {e}")
                        continue

            else:
                # 获取实时数据
                logger.info("[大盘] 获取主要指数实时行情...")

                # 优先使用东方财富数据源，失败则回退到新浪
                df = None
                data_source = None
                
                # 尝试东方财富数据源
                try:
                    df = ak.stock_zh_index_spot_em()
                    if df is not None and not df.empty:
                        data_source = 'eastmoney'
                        logger.info("[大盘] 使用东方财富数据源获取指数行情")
                except Exception as e:
                    logger.warning(f"[大盘] 东方财富数据源失败: {e}，尝试新浪数据源...")
                
                # 回退到新浪数据源
                if df is None or df.empty:
                    try:
                        df = ak.stock_zh_index_spot_sina()
                        if df is not None and not df.empty:
                            data_source = 'sina'
                            logger.info("[大盘] 使用新浪数据源获取指数行情")
                    except Exception as e:
                        logger.warning(f"[大盘] 新浪数据源也失败: {e}，尝试腾讯直连...")
                
                # 最终回退：腾讯直连接口
                if df is None or df.empty:
                    qq_data = _fetch_qq_index_data(list(self.MAIN_INDICES.keys()))
                    if qq_data:
                        logger.info("[大盘] 使用腾讯直连接口获取指数行情")
                        for code, name in self.MAIN_INDICES.items():
                            if code in qq_data:
                                d = qq_data[code]
                                idx = MarketIndex(
                                    code=code,
                                    name=name,
                                    current=d['current'],
                                    change=d['change'],
                                    change_pct=d['change_pct'],
                                    open=d['open'],
                                    high=d['high'],
                                    low=d['low'],
                                    prev_close=d['prev_close'],
                                    volume=d['volume'],
                                )
                                if idx.prev_close > 0:
                                    idx.amplitude = (idx.high - idx.low) / idx.prev_close * 100
                                indices.append(idx)
                        logger.info(f"[大盘] 获取到 {len(indices)} 个指数行情")
                        return indices

                if df is not None and not df.empty:
                    # 新浪数据源的代码格式不同，需要映射
                    sina_code_map = {
                        '000001': 'sh000001',
                        '399001': 'sz399001',
                        '399006': 'sz399006',
                        '000688': 'sh000688',
                        '000016': 'sh000016',
                        '000300': 'sh000300',
                    }
                    
                    for code, name in self.MAIN_INDICES.items():
                        row = None
                        
                        if data_source == 'eastmoney':
                            # 东方财富格式
                            row = df[df['代码'] == code]
                            if row.empty:
                                row = df[df['代码'].str.contains(code)]
                        elif data_source == 'sina':
                            # 新浪格式：代码带前缀如 sh000001
                            sina_code = sina_code_map.get(code)
                            if sina_code:
                                row = df[df['代码'] == sina_code]

                        if row is not None and not row.empty:
                            row = row.iloc[0]
                            
                            index: Optional[MarketIndex] = None
                            if data_source == 'eastmoney':
                                index = MarketIndex(
                                    code=code,
                                    name=name,
                                    current=float(row.get('最新价', 0) or 0),
                                    change=float(row.get('涨跌额', 0) or 0),
                                    change_pct=float(row.get('涨跌幅', 0) or 0),
                                    open=float(row.get('今开', 0) or 0),
                                    high=float(row.get('最高', 0) or 0),
                                    low=float(row.get('最低', 0) or 0),
                                    prev_close=float(row.get('昨收', 0) or 0),
                                    volume=float(row.get('成交量', 0) or 0),
                                    amount=float(row.get('成交额', 0) or 0),
                                )
                            elif data_source == 'sina':
                                current = float(row.get('最新价', 0) or 0)
                                prev_close = float(row.get('昨收', 0) or 0)
                                change = current - prev_close if prev_close > 0 else 0
                                change_pct = float(row.get('涨跌幅', 0) or 0)
                                
                                index = MarketIndex(
                                    code=code,
                                    name=name,
                                    current=current,
                                    change=change,
                                    change_pct=change_pct,
                                    open=float(row.get('今开', 0) or 0),
                                    high=float(row.get('最高', 0) or 0),
                                    low=float(row.get('最低', 0) or 0),
                                    prev_close=prev_close,
                                    volume=float(row.get('成交量', 0) or 0),
                                    amount=float(row.get('成交额', 0) or 0),
                                )
                            
                            if index is not None:
                                if index.prev_close > 0:
                                    index.amplitude = (index.high - index.low) / index.prev_close * 100
                                indices.append(index)

            logger.info(f"[大盘] 获取到 {len(indices)} 个指数行情")

        except Exception as e:
            logger.error(f"[大盘] 获取指数行情失败: {e}")

        return indices
    
    def _get_market_statistics(self, overview: MarketOverview):
        """获取市场涨跌统计"""
        try:
            logger.info("[大盘] 获取市场涨跌统计...")
            
            df = None
            
            try:
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    logger.info("[大盘] 使用东方财富数据源获取涨跌统计")
            except Exception as e:
                logger.warning(f"[大盘] 东方财富数据源失败: {e}，尝试腾讯数据源...")
            
            if df is None or df.empty:
                try:
                    df = ak.stock_zh_a_spot()
                    if df is not None and not df.empty:
                        logger.info("[大盘] 使用腾讯数据源获取涨跌统计")
                except Exception as e:
                    logger.error(f"[大盘] 腾讯数据源也失败: {e}")
            
            if df is not None and not df.empty:
                change_col = '涨跌幅'
                if change_col in df.columns:
                    df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
                    overview.up_count = len(df[df[change_col] > 0])
                    overview.down_count = len(df[df[change_col] < 0])
                    overview.flat_count = len(df[df[change_col] == 0])
                    
                    overview.limit_up_count = len(df[df[change_col] >= 9.9])
                    overview.limit_down_count = len(df[df[change_col] <= -9.9])
                
                amount_col = '成交额'
                if amount_col in df.columns:
                    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
                    overview.total_amount = df[amount_col].sum() / 1e8
                
                logger.info(f"[大盘] 涨:{overview.up_count} 跌:{overview.down_count} 平:{overview.flat_count} "
                          f"涨停:{overview.limit_up_count} 跌停:{overview.limit_down_count} "
                          f"成交额:{overview.total_amount:.0f}亿")
                
        except Exception as e:
            logger.error(f"[大盘] 获取涨跌统计失败: {e}")
    
    def _get_sector_rankings(self, overview: MarketOverview):
        """获取板块涨跌榜"""
        try:
            logger.info("[大盘] 获取板块涨跌榜...")
            
            df = None
            name_col = '板块名称'
            
            try:
                df = ak.stock_board_industry_name_em()
                if df is not None and not df.empty:
                    logger.info("[大盘] 使用东方财富数据源获取板块行情")
            except Exception as e:
                logger.warning(f"[大盘] 东方财富板块数据源失败: {e}，尝试概念板块...")
            
            if df is None or df.empty:
                try:
                    df = ak.stock_board_concept_name_em()
                    name_col = '板块名称'
                    if df is not None and not df.empty:
                        logger.info("[大盘] 使用东方财富概念板块数据源")
                except Exception as e:
                    logger.error(f"[大盘] 概念板块数据源也失败: {e}")
            
            if df is not None and not df.empty:
                change_col = '涨跌幅'
                if change_col in df.columns and name_col in df.columns:
                    df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
                    df = df.dropna(subset=[change_col])
                    
                    top = df.nlargest(5, change_col)
                    overview.top_sectors = [
                        {'name': row[name_col], 'change_pct': row[change_col]}
                        for _, row in top.iterrows()
                    ]
                    
                    bottom = df.nsmallest(5, change_col)
                    overview.bottom_sectors = [
                        {'name': row[name_col], 'change_pct': row[change_col]}
                        for _, row in bottom.iterrows()
                    ]
                    
                    logger.info(f"[大盘] 领涨板块: {[s['name'] for s in overview.top_sectors]}")
                    logger.info(f"[大盘] 领跌板块: {[s['name'] for s in overview.bottom_sectors]}")
                    
        except Exception as e:
            logger.error(f"[大盘] 获取板块涨跌榜失败: {e}")
    
    def _get_north_flow(self, overview: MarketOverview):
        """获取北向资金流入"""
        try:
            logger.info("[大盘] 获取北向资金...")
            
            north_flow_total = 0.0
            
            for symbol in ['沪股通', '深股通']:
                try:
                    df = ak.stock_hsgt_hist_em(symbol=symbol)
                    if df is not None and not df.empty:
                        latest = df.iloc[-1]
                        flow_col = None
                        for col in ['当日资金流入', '当日净流入', '净流入']:
                            if col in df.columns:
                                flow_col = col
                                break
                        if flow_col:
                            flow_value = latest.get(flow_col, 0)
                            if pd.notna(flow_value):
                                north_flow_total += float(flow_value)
                except Exception as e:
                    logger.debug(f"[大盘] 获取 {symbol} 数据失败: {e}")
                    continue
            
            if north_flow_total != 0:
                overview.north_flow = north_flow_total / 1e8
                logger.info(f"[大盘] 北向资金净流入: {overview.north_flow:.2f}亿")
            else:
                logger.warning("[大盘] 未能获取到北向资金数据")
                
        except Exception as e:
            logger.warning(f"[大盘] 获取北向资金失败: {e}")
    
    def search_market_news(self) -> List[Dict]:
        """
        搜索市场新闻
        
        Returns:
            新闻列表
        """
        if not self.search_service:
            logger.warning("[大盘] 搜索服务未配置，跳过新闻搜索")
            return []
        
        all_news = []
        today = datetime.now()
        month_str = f"{today.year}年{today.month}月"
        
        # 多维度搜索
        search_queries = [
            f"A股 大盘 复盘 {month_str}",
            f"股市 行情 分析 今日 {month_str}",
            f"A股 市场 热点 板块 {month_str}",
        ]
        
        try:
            logger.info("[大盘] 开始搜索市场新闻...")
            
            for query in search_queries:
                # 使用 search_stock_news 方法，传入"大盘"作为股票名
                response = self.search_service.search_stock_news(
                    stock_code="market",
                    stock_name="大盘",
                    max_results=3,
                    focus_keywords=query.split()
                )
                if response and response.results:
                    all_news.extend(response.results)
                    logger.info(f"[大盘] 搜索 '{query}' 获取 {len(response.results)} 条结果")
            
            logger.info(f"[大盘] 共获取 {len(all_news)} 条市场新闻")
            
        except Exception as e:
            logger.error(f"[大盘] 搜索市场新闻失败: {e}")
        
        return all_news
    
    def generate_market_review(self, overview: MarketOverview, news: List) -> str:
        """
        使用大模型生成大盘复盘报告
        
        Args:
            overview: 市场概览数据
            news: 市场新闻列表 (SearchResult 对象列表)
            
        Returns:
            大盘复盘报告文本
        """
        if not self.analyzer or not self.analyzer.is_available():
            logger.warning("[大盘] AI分析器未配置或不可用，使用模板生成报告")
            return self._generate_template_review(overview, news)
        
        # 构建 Prompt
        prompt = self._build_review_prompt(overview, news)
        
        try:
            logger.info("[大盘] 调用大模型生成复盘报告...")
            
            generation_config = {
                'temperature': 0.7,
                'max_output_tokens': 2048,
            }
            
            # 根据 analyzer 使用的 API 类型调用
            if self.analyzer._use_openai:
                # 使用 OpenAI 兼容 API
                review = self.analyzer._call_openai_api(prompt, generation_config)
            else:
                # 使用 Gemini API
                response = self.analyzer._model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
                review = response.text.strip() if response and response.text else None
            
            if review:
                logger.info(f"[大盘] 复盘报告生成成功，长度: {len(review)} 字符")
                return review
            else:
                logger.warning("[大盘] 大模型返回为空")
                return self._generate_template_review(overview, news)
                
        except Exception as e:
            logger.error(f"[大盘] 大模型生成复盘报告失败: {e}")
            return self._generate_template_review(overview, news)
    
    def _build_review_prompt(self, overview: MarketOverview, news: List) -> str:
        """构建复盘报告 Prompt"""
        # 指数行情信息（简洁格式，不用emoji）
        indices_text = ""
        for idx in overview.indices:
            direction = "↑" if idx.change_pct > 0 else "↓" if idx.change_pct < 0 else "-"
            indices_text += f"- {idx.name}: {idx.current:.2f} ({direction}{abs(idx.change_pct):.2f}%)\n"
        
        # 板块信息
        top_sectors_text = ", ".join([f"{s['name']}({s['change_pct']:+.2f}%)" for s in overview.top_sectors[:3]])
        bottom_sectors_text = ", ".join([f"{s['name']}({s['change_pct']:+.2f}%)" for s in overview.bottom_sectors[:3]])
        
        # 新闻信息 - 支持 SearchResult 对象或字典
        news_text = ""
        for i, n in enumerate(news[:6], 1):
            # 兼容 SearchResult 对象和字典
            if hasattr(n, 'title'):
                title = n.title[:50] if n.title else ''
                snippet = n.snippet[:100] if n.snippet else ''
            else:
                title = n.get('title', '')[:50]
                snippet = n.get('snippet', '')[:100]
            news_text += f"{i}. {title}\n   {snippet}\n"
        
        prompt = f"""你是一位专业的A股市场分析师，请根据以下数据生成一份简洁的大盘复盘报告。

【重要】输出要求：
- 必须输出纯 Markdown 文本格式
- 禁止输出 JSON 格式
- 禁止输出代码块
- emoji 仅在标题处少量使用（每个标题最多1个）

---

# 今日市场数据

## 日期
{overview.date}

## 主要指数
{indices_text}

## 市场概况
- 上涨: {overview.up_count} 家 | 下跌: {overview.down_count} 家 | 平盘: {overview.flat_count} 家
- 涨停: {overview.limit_up_count} 家 | 跌停: {overview.limit_down_count} 家
- 两市成交额: {overview.total_amount:.0f} 亿元
- 北向资金: {overview.north_flow:+.2f} 亿元

## 板块表现
领涨: {top_sectors_text}
领跌: {bottom_sectors_text}

## 市场新闻
{news_text if news_text else "暂无相关新闻"}

---

# 输出格式模板（请严格按此格式输出）

## 📊 {overview.date} 大盘复盘

### 一、市场总结
（2-3句话概括今日市场整体表现，包括指数涨跌、成交量变化）

### 二、指数点评
（分析上证、深证、创业板等各指数走势特点）

### 三、资金动向
（解读成交额和北向资金流向的含义）

### 四、热点解读
（分析领涨领跌板块背后的逻辑和驱动因素）

### 五、后市展望
（结合当前走势和新闻，给出明日市场预判）

### 六、风险提示
（需要关注的风险点）

---

请直接输出复盘报告内容，不要输出其他说明文字。
"""
        return prompt
    
    def _generate_template_review(self, overview: MarketOverview, news: List) -> str:
        """使用模板生成复盘报告（无大模型时的备选方案）"""
        
        # 判断市场走势
        sh_index = next((idx for idx in overview.indices if idx.code == '000001'), None)
        if sh_index:
            if sh_index.change_pct > 1:
                market_mood = "强势上涨"
            elif sh_index.change_pct > 0:
                market_mood = "小幅上涨"
            elif sh_index.change_pct > -1:
                market_mood = "小幅下跌"
            else:
                market_mood = "明显下跌"
        else:
            market_mood = "震荡整理"
        
        # 指数行情（简洁格式）
        indices_text = ""
        for idx in overview.indices[:4]:
            direction = "↑" if idx.change_pct > 0 else "↓" if idx.change_pct < 0 else "-"
            indices_text += f"- **{idx.name}**: {idx.current:.2f} ({direction}{abs(idx.change_pct):.2f}%)\n"
        
        # 板块信息
        top_text = "、".join([s['name'] for s in overview.top_sectors[:3]])
        bottom_text = "、".join([s['name'] for s in overview.bottom_sectors[:3]])
        
        report = f"""## 📊 {overview.date} 大盘复盘

### 一、市场总结
今日A股市场整体呈现**{market_mood}**态势。

### 二、主要指数
{indices_text}

### 三、涨跌统计
| 指标 | 数值 |
|------|------|
| 上涨家数 | {overview.up_count} |
| 下跌家数 | {overview.down_count} |
| 涨停 | {overview.limit_up_count} |
| 跌停 | {overview.limit_down_count} |
| 两市成交额 | {overview.total_amount:.0f}亿 |
| 北向资金 | {overview.north_flow:+.2f}亿 |

### 四、板块表现
- **领涨**: {top_text}
- **领跌**: {bottom_text}

### 五、风险提示
市场有风险，投资需谨慎。以上数据仅供参考，不构成投资建议。

---
*复盘时间: {datetime.now().strftime('%H:%M')}*
"""
        return report
    
    def run_daily_review(self, target_date: Optional[str] = None) -> str:
        """
        执行每日大盘复盘流程

        Args:
            target_date: 目标日期，格式：YYYYMMDD 或 YYYY-MM-DD（可选，默认为今天）

        Returns:
            复盘报告文本
        """
        logger.info("========== 开始大盘复盘分析 ==========")

        # 1. 获取市场概览
        overview = self.get_market_overview(target_date=target_date)

        # 2. 搜索市场新闻
        news = self.search_market_news()

        # 3. 生成复盘报告
        report = self.generate_market_review(overview, news)

        # 4. 保存大盘数据到数据库
        try:
            from storage import get_db
            db = get_db()
            db.save_market_overview(overview)
            logger.info("✅ 大盘数据已保存到数据库")
        except Exception as e:
            logger.warning(f"⚠️ 保存大盘数据失败: {e}")

        logger.info("========== 大盘复盘分析完成 ==========")
        
        return report


# 测试入口
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    )
    
    analyzer = MarketAnalyzer()
    
    # 测试获取市场概览
    overview = analyzer.get_market_overview()
    print(f"\n=== 市场概览 ===")
    print(f"日期: {overview.date}")
    print(f"指数数量: {len(overview.indices)}")
    for idx in overview.indices:
        print(f"  {idx.name}: {idx.current:.2f} ({idx.change_pct:+.2f}%)")
    print(f"上涨: {overview.up_count} | 下跌: {overview.down_count}")
    print(f"成交额: {overview.total_amount:.0f}亿")
    
    # 测试生成模板报告
    report = analyzer._generate_template_review(overview, [])
    print(f"\n=== 复盘报告 ===")
    print(report)
