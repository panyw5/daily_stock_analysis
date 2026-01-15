# -*- coding: utf-8 -*-
"""
===================================
股票历史数据分析工具
===================================

功能：
1. 获取指定时间段的股票历史数据
2. 计算技术指标（均线、MACD、RSI等）
3. 生成分析报告
4. 支持多种时间周期（5日、1周、1月、3月、6月、1年）

使用方式：
    python history_analysis.py --stock 600519 --period 1m
    python history_analysis.py --stock 600519 --start-date 20260101 --end-date 20260114
"""

import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd

from data_provider.akshare_fetcher import AkshareFetcher
from analyzer import GeminiAnalyzer
from config import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HistoryAnalyzer:
    """历史数据分析器"""

    def __init__(self, enable_ai: bool = False):
        """
        初始化分析器

        Args:
            enable_ai: 是否启用 AI 分析（默认关闭）
        """
        self.config = get_config()
        self.fetcher = AkshareFetcher()
        self.enable_ai = enable_ai

        # 初始化 AI 分析器
        if enable_ai:
            if self.config.gemini_api_key:
                self.ai_analyzer = GeminiAnalyzer(api_key=self.config.gemini_api_key)
                logger.info("AI 分析器已启用")
            else:
                logger.warning("未配置 Gemini API Key，AI 分析功能将被禁用")
                self.enable_ai = False
                self.ai_analyzer = None
        else:
            self.ai_analyzer = None

    def normalize_date(self, date_str: str) -> str:
        """
        标准化日期格式

        Args:
            date_str: 日期字符串，支持 YYYYMMDD 或 YYYY-MM-DD

        Returns:
            YYYY-MM-DD 格式的日期字符串
        """
        if not date_str:
            return None
        date_str = date_str.replace('-', '')
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    def parse_period(self, period: str, end_date: Optional[str] = None) -> tuple[str, str]:
        """
        解析时间周期

        Args:
            period: 时间周期（5d, 1w, 2w, 1m, 3m, 6m, 1y）
            end_date: 结束日期（可选，默认今天）

        Returns:
            (start_date, end_date): 开始日期和结束日期
        """
        period_map = {
            '5d': 5,
            '1w': 7,
            '2w': 14,
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1y': 365
        }

        days = period_map.get(period, 30)

        if end_date:
            end_dt = datetime.strptime(self.normalize_date(end_date), '%Y-%m-%d')
        else:
            end_dt = datetime.now()

        start_dt = end_dt - timedelta(days=days * 2)  # 乘以2以确保有足够的交易日
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')

        return start_date, end_date

    def get_stock_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取股票历史数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            period: 时间周期（可选）

        Returns:
            包含历史数据的 DataFrame
        """
        # 解析日期范围
        if period:
            start_date, end_date = self.parse_period(period, end_date)
        else:
            if start_date:
                start_date = self.normalize_date(start_date)
            if end_date:
                end_date = self.normalize_date(end_date)
            else:
                end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"获取 {stock_code} 的历史数据: {start_date} ~ {end_date}")

        # 使用 AkshareFetcher 获取数据
        df = self.fetcher.get_daily_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )

        if df is None or df.empty:
            logger.error(f"未获取到 {stock_code} 的数据")
            return None

        logger.info(f"成功获取 {len(df)} 条数据")
        return df

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            df: 原始数据 DataFrame

        Returns:
            包含技术指标的 DataFrame
        """
        # 计算均线
        if 'close' in df.columns:
            df['MA5'] = df['close'].rolling(window=5, min_periods=1).mean()
            df['MA10'] = df['close'].rolling(window=10, min_periods=1).mean()
            df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()
            df['MA60'] = df['close'].rolling(window=60, min_periods=1).mean()

        # 计算 EMA12 和 EMA26 用于 MACD
        if 'close' in df.columns:
            df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['DIF'] = df['EMA12'] - df['EMA26']
            df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
            df['MACD'] = (df['DIF'] - df['DEA']) * 2

        # 计算 RSI
        if 'close' in df.columns:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

        return df

    def analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析趋势

        Args:
            df: 包含技术指标的 DataFrame

        Returns:
            趋势分析结果
        """
        if df is None or df.empty:
            return {}

        latest = df.iloc[-1]
        result = {
            'date': latest['date'],
            'close': latest['close'],
            'change_pct': ((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100) if len(df) > 1 else 0,
        }

        # 均线分析
        if all(col in latest for col in ['MA5', 'MA10', 'MA20', 'MA60']):
            result['ma5'] = latest['MA5']
            result['ma10'] = latest['MA10']
            result['ma20'] = latest['MA20']
            result['ma60'] = latest['MA60']

            # 判断多头排列
            if latest['MA5'] > latest['MA10'] > latest['MA20']:
                result['trend'] = '多头排列'
            elif latest['MA5'] < latest['MA10'] < latest['MA20']:
                result['trend'] = '空头排列'
            else:
                result['trend'] = '震荡'

            # 计算乖离率
            result['bias_ma5'] = (latest['close'] - latest['MA5']) / latest['MA5'] * 100
            result['bias_ma10'] = (latest['close'] - latest['MA10']) / latest['MA10'] * 100
            result['bias_ma20'] = (latest['close'] - latest['MA20']) / latest['MA20'] * 100

        # MACD 分析
        if 'MACD' in latest:
            result['macd'] = latest['MACD']
            result['dif'] = latest['DIF']
            result['dea'] = latest['DEA']
            result['macd_signal'] = 'MACD金叉' if latest['DIF'] > latest['DEA'] else 'MACD死叉'

        # RSI 分析
        if 'RSI' in latest:
            result['rsi'] = latest['RSI']
            if latest['RSI'] > 70:
                result['rsi_signal'] = '超买'
            elif latest['RSI'] < 30:
                result['rsi_signal'] = '超卖'
            else:
                result['rsi_signal'] = '正常'

        # 成交量分析
        if 'volume' in df.columns:
            avg_volume = df['volume'].tail(5).mean()
            result['volume'] = latest['volume']
            result['avg_volume_5d'] = avg_volume
            result['volume_ratio'] = latest['volume'] / avg_volume if avg_volume > 0 else 0

        return result

    def get_ai_analysis(self, stock_code: str, analysis: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
        """
        使用 AI 分析器生成分析报告

        Args:
            stock_code: 股票代码
            analysis: 技术分析结果
            df: 原始数据

        Returns:
            AI 分析报告文本
        """
        if not self.enable_ai or not self.ai_analyzer:
            return None

        try:
            # 构建分析上下文
            context = f"""
股票代码: {stock_code}
分析周期: {df.iloc[0]['date']} ~ {df.iloc[-1]['date']}
数据条数: {len(df)} 条

最新行情:
- 收盘价: {analysis.get('close', 0):.2f} 元
- 涨跌幅: {analysis.get('change_pct', 0):+.2f}%

均线分析:
- MA5: {analysis.get('ma5', 0):.2f} 元
- MA10: {analysis.get('ma10', 0):.2f} 元
- MA20: {analysis.get('ma20', 0):.2f} 元
- MA60: {analysis.get('ma60', 0):.2f} 元
- 趋势: {analysis.get('trend', 'N/A')}
- MA5 乖离率: {analysis.get('bias_ma5', 0):+.2f}%
- MA10 乖离率: {analysis.get('bias_ma10', 0):+.2f}%
- MA20 乖离率: {analysis.get('bias_ma20', 0):+.2f}%

MACD 指标:
- DIF: {analysis.get('dif', 0):.2f}
- DEA: {analysis.get('dea', 0):.2f}
- MACD: {analysis.get('macd', 0):.2f}
- 信号: {analysis.get('macd_signal', 'N/A')}

RSI 指标:
- RSI(14): {analysis.get('rsi', 0):.2f}
- 状态: {analysis.get('rsi_signal', 'N/A')}

成交量分析:
- 最新成交量: {analysis.get('volume', 0):,.0f} 手
- 5日均量: {analysis.get('avg_volume_5d', 0):,.0f} 手
- 量比: {analysis.get('volume_ratio', 0):.2f}

价格统计:
- 最高价: {df['high'].max():.2f} 元
- 最低价: {df['low'].min():.2f} 元
- 振幅: {((df['high'].max() - df['low'].min()) / df['low'].min() * 100):.2f}%
- 平均价: {df['close'].mean():.2f} 元
"""

            logger.info(f"正在使用 AI 分析器分析 {stock_code}...")
            # 调用 AI 分析器
            ai_result = self.ai_analyzer.analyze(context, news_context="")

            if ai_result and hasattr(ai_result, 'dashboard'):
                return ai_result.dashboard
            else:
                logger.warning("AI 分析器返回结果为空")
                return None

        except Exception as e:
            logger.error(f"AI 分析失败: {e}")
            return None

    def generate_report(self, stock_code: str, analysis: Dict[str, Any], df: pd.DataFrame, ai_analysis: Optional[str] = None) -> str:
        """
        生成分析报告

        Args:
            stock_code: 股票代码
            analysis: 分析结果
            df: 原始数据

        Returns:
            Markdown 格式的报告
        """
        report = f"""# 📊 {stock_code} 历史数据分析报告

## 基本信息
- **分析日期**: {analysis.get('date', 'N/A')}
- **数据周期**: {df.iloc[0]['date']} ~ {df.iloc[-1]['date']}
- **数据条数**: {len(df)} 条

## 最新行情
- **收盘价**: {analysis.get('close', 0):.2f} 元
- **涨跌幅**: {analysis.get('change_pct', 0):+.2f}%

"""

        # 添加 AI 分析结果
        if ai_analysis:
            report += f"""## 🤖 AI 智能分析

{ai_analysis}

---

"""

        report += f"""## 均线分析
- **MA5**: {analysis.get('ma5', 0):.2f} 元
- **MA10**: {analysis.get('ma10', 0):.2f} 元
- **MA20**: {analysis.get('ma20', 0):.2f} 元
- **MA60**: {analysis.get('ma60', 0):.2f} 元
- **趋势**: {analysis.get('trend', 'N/A')}

### 乖离率
- **MA5 乖离率**: {analysis.get('bias_ma5', 0):+.2f}%
- **MA10 乖离率**: {analysis.get('bias_ma10', 0):+.2f}%
- **MA20 乖离率**: {analysis.get('bias_ma20', 0):+.2f}%

## MACD 指标
- **DIF**: {analysis.get('dif', 0):.2f}
- **DEA**: {analysis.get('dea', 0):.2f}
- **MACD**: {analysis.get('macd', 0):.2f}
- **信号**: {analysis.get('macd_signal', 'N/A')}

## RSI 指标
- **RSI(14)**: {analysis.get('rsi', 0):.2f}
- **状态**: {analysis.get('rsi_signal', 'N/A')}

## 成交量分析
- **最新成交量**: {analysis.get('volume', 0):,.0f} 手
- **5日均量**: {analysis.get('avg_volume_5d', 0):,.0f} 手
- **量比**: {analysis.get('volume_ratio', 0):.2f}

## 价格统计
- **最高价**: {df['high'].max():.2f} 元
- **最低价**: {df['low'].min():.2f} 元
- **振幅**: {((df['high'].max() - df['low'].min()) / df['low'].min() * 100):.2f}%
- **平均价**: {df['close'].mean():.2f} 元

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report

    def run(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        运行完整的分析流程

        Args:
            stock_code: 股票代码
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            period: 时间周期（可选）
            output_file: 输出文件路径（可选）

        Returns:
            分析报告文本
        """
        logger.info(f"开始分析 {stock_code}")

        # 1. 获取数据
        df = self.get_stock_data(stock_code, start_date, end_date, period)
        if df is None or df.empty:
            logger.error("数据获取失败")
            return None

        # 2. 计算技术指标
        df = self.calculate_technical_indicators(df)

        # 3. 分析趋势
        analysis = self.analyze_trend(df)

        # 4. AI 分析（如果启用）
        ai_analysis = None
        if self.enable_ai:
            ai_analysis = self.get_ai_analysis(stock_code, analysis, df)

        # 5. 生成报告
        report = self.generate_report(stock_code, analysis, df, ai_analysis)

        # 5. 保存报告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存至: {output_file}")
        else:
            # 默认保存到 reports 目录
            import os
            os.makedirs('reports', exist_ok=True)
            filename = f"reports/history_{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存至: {filename}")

        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='股票历史数据分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python history_analysis.py --stock 600519                    # 默认分析近1月数据（AI 分析已启用）
  python history_analysis.py --stock 600519 --period 3m        # 分析近3月数据
  python history_analysis.py --stock 600519 --start-date 20260101 --end-date 20260114
  python history_analysis.py --stock 600519,000001 --period 1w # 批量分析
  python history_analysis.py --stock 600519 --no-ai            # 禁用 AI 分析
        '''
    )

    parser.add_argument(
        '--stock',
        type=str,
        required=True,
        help='股票代码，多个代码用逗号分隔'
    )

    parser.add_argument(
        '--period',
        type=str,
        default='1m',  # 默认1个月
        choices=['5d', '1w', '2w', '1m', '3m', '6m', '1y'],
        help='时间周期：5d(5天), 1w(1周), 2w(2周), 1m(1月，默认), 3m(3月), 6m(6月), 1y(1年)'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='开始日期，格式：YYYYMMDD 或 YYYY-MM-DD'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='结束日期，格式：YYYYMMDD 或 YYYY-MM-DD（默认今天）'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='输出文件路径（可选）'
    )

    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='禁用 AI 分析（默认启用）'
    )

    args = parser.parse_args()

    # 解析股票代码列表
    stock_codes = [code.strip() for code in args.stock.split(',') if code.strip()]

    # 创建分析器（默认启用 AI，除非指定 --no-ai）
    analyzer = HistoryAnalyzer(enable_ai=not args.no_ai)

    # 分析每只股票
    for stock_code in stock_codes:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"分析股票: {stock_code}")
            logger.info(f"{'='*60}")

            report = analyzer.run(
                stock_code=stock_code,
                start_date=args.start_date,
                end_date=args.end_date,
                period=args.period,
                output_file=args.output
            )

            if report:
                print("\n" + "="*80)
                print(report)
                print("="*80 + "\n")

        except Exception as e:
            logger.error(f"分析 {stock_code} 失败: {e}", exc_info=True)
            continue


if __name__ == "__main__":
    main()
