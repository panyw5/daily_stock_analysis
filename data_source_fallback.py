#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源降级策略实现
优先级: TuShare (P0) → Baostock (P0备用) → AkShare (P2补充)
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSourceFallback:
    """数据源降级策略管理器"""

    def __init__(self, tushare_token: Optional[str] = None):
        self.tushare_token = tushare_token
        self.tushare_api = None
        self.baostock_logged_in = False

        if tushare_token:
            try:
                import tushare as ts

                ts.set_token(tushare_token)
                self.tushare_api = ts.pro_api()
                logger.info("✅ TuShare 初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ TuShare 初始化失败: {e}")

    def _login_baostock(self) -> bool:
        """登录 Baostock"""
        if self.baostock_logged_in:
            return True

        try:
            import baostock as bs

            lg = bs.login()
            if lg.error_code == "0":
                self.baostock_logged_in = True
                logger.info("✅ Baostock 登录成功")
                return True
            else:
                logger.warning(f"⚠️ Baostock 登录失败: {lg.error_msg}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Baostock 登录异常: {e}")
            return False

    def _logout_baostock(self):
        """登出 Baostock"""
        if self.baostock_logged_in:
            try:
                import baostock as bs

                bs.logout()
                self.baostock_logged_in = False
                logger.info("✅ Baostock 登出成功")
            except:
                pass

    def get_daily_data(
        self, stock_code: str, start_date: str, end_date: str, adjust: str = "qfq"
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """
        获取日线历史数据（带降级策略）

        Args:
            stock_code: 股票代码（如 '600519'）
            start_date: 开始日期（格式：'20240101' 或 '2024-01-01'）
            end_date: 结束日期（格式：'20240101' 或 '2024-01-01'）
            adjust: 复权方式（'qfq'前复权, 'hfq'后复权, ''不复权）

        Returns:
            (DataFrame, 数据源名称) 或 (None, 错误信息)
        """
        start_date_dash = start_date.replace("-", "")
        end_date_dash = end_date.replace("-", "")
        start_date_hyphen = (
            f"{start_date_dash[:4]}-{start_date_dash[4:6]}-{start_date_dash[6:]}"
        )
        end_date_hyphen = (
            f"{end_date_dash[:4]}-{end_date_dash[4:6]}-{end_date_dash[6:]}"
        )

        logger.info(
            f"📊 获取 {stock_code} 日线数据: {start_date_hyphen} ~ {end_date_hyphen}"
        )

        if self.tushare_api:
            try:
                logger.info("🔄 尝试使用 TuShare (P0主力)...")
                ts_code = self._convert_to_tushare_code(stock_code)
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=start_date_dash,
                    end_date=end_date_dash,
                    fields="ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
                )

                if df is not None and not df.empty:
                    df = df.rename(
                        columns={
                            "trade_date": "date",
                            "ts_code": "code",
                            "pre_close": "preclose",
                            "vol": "volume",
                            "pct_chg": "pctChg",
                        }
                    )
                    logger.info(f"✅ TuShare 成功获取 {len(df)} 条数据")
                    return df, "TuShare"
            except Exception as e:
                logger.warning(f"⚠️ TuShare 失败: {e}")

        if self._login_baostock():
            try:
                logger.info("🔄 尝试使用 Baostock (P0备用)...")
                import baostock as bs

                bs_code = self._convert_to_baostock_code(stock_code)
                adjustflag = "2" if adjust == "qfq" else "1" if adjust == "hfq" else "3"

                rs = bs.query_history_k_data_plus(
                    bs_code,
                    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                    start_date=start_date_hyphen,
                    end_date=end_date_hyphen,
                    frequency="d",
                    adjustflag=adjustflag,
                )

                if rs.error_code == "0":
                    data_list = []
                    while (rs.error_code == "0") & rs.next():
                        data_list.append(rs.get_row_data())

                    df = pd.DataFrame(data_list, columns=rs.fields)

                    if not df.empty:
                        logger.info(f"✅ Baostock 成功获取 {len(df)} 条数据")
                        return df, "Baostock"
            except Exception as e:
                logger.warning(f"⚠️ Baostock 失败: {e}")

        try:
            logger.info("🔄 尝试使用 AkShare (P2补充，不推荐)...")
            import akshare as ak

            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date_dash,
                end_date=end_date_dash,
                adjust=adjust,
            )

            if df is not None and not df.empty:
                logger.info(f"✅ AkShare 成功获取 {len(df)} 条数据")
                return df, "AkShare"
        except Exception as e:
            logger.warning(f"⚠️ AkShare 失败: {e}")

        logger.error("❌ 所有数据源均失败")
        return None, "所有数据源均失败"

    def get_financial_data(
        self, stock_code: str, year: int, quarter: int
    ) -> Tuple[Optional[dict], str]:
        """
        获取财务数据（带降级策略）

        Args:
            stock_code: 股票代码（如 '600519'）
            year: 年份（如 2024）
            quarter: 季度（1-4）

        Returns:
            (dict包含三张表, 数据源名称) 或 (None, 错误信息)
        """
        logger.info(f"📊 获取 {stock_code} 财务数据: {year}Q{quarter}")

        if self._login_baostock():
            try:
                logger.info("🔄 尝试使用 Baostock (P0主力)...")
                import baostock as bs

                bs_code = self._convert_to_baostock_code(stock_code)

                rs_profit = bs.query_profit_data(
                    code=bs_code, year=year, quarter=quarter
                )
                rs_balance = bs.query_balance_data(
                    code=bs_code, year=year, quarter=quarter
                )
                rs_cash = bs.query_cash_flow_data(
                    code=bs_code, year=year, quarter=quarter
                )

                result = {}

                if rs_profit.error_code == "0":
                    data_list = []
                    while (rs_profit.error_code == "0") & rs_profit.next():
                        data_list.append(rs_profit.get_row_data())
                    result["profit"] = pd.DataFrame(data_list, columns=rs_profit.fields)

                if rs_balance.error_code == "0":
                    data_list = []
                    while (rs_balance.error_code == "0") & rs_balance.next():
                        data_list.append(rs_balance.get_row_data())
                    result["balance"] = pd.DataFrame(
                        data_list, columns=rs_balance.fields
                    )

                if rs_cash.error_code == "0":
                    data_list = []
                    while (rs_cash.error_code == "0") & rs_cash.next():
                        data_list.append(rs_cash.get_row_data())
                    result["cashflow"] = pd.DataFrame(data_list, columns=rs_cash.fields)

                if result:
                    logger.info(f"✅ Baostock 成功获取财务数据")
                    return result, "Baostock"
            except Exception as e:
                logger.warning(f"⚠️ Baostock 失败: {e}")

        try:
            logger.info("🔄 尝试使用 AkShare 新浪接口 (P2备用)...")
            import akshare as ak

            sina_code = (
                f"sh{stock_code}" if stock_code.startswith("6") else f"sz{stock_code}"
            )

            result = {
                "balance": ak.stock_financial_report_sina(
                    stock=sina_code, symbol="资产负债表"
                ),
                "profit": ak.stock_financial_report_sina(
                    stock=sina_code, symbol="利润表"
                ),
                "cashflow": ak.stock_financial_report_sina(
                    stock=sina_code, symbol="现金流量表"
                ),
            }

            logger.info(f"✅ AkShare 成功获取财务数据")
            return result, "AkShare"
        except Exception as e:
            logger.warning(f"⚠️ AkShare 失败: {e}")

        logger.error("❌ 所有数据源均失败")
        return None, "所有数据源均失败"

    def _convert_to_tushare_code(self, stock_code: str) -> str:
        """转换为 TuShare 代码格式"""
        if "." in stock_code:
            return stock_code

        if stock_code.startswith("6"):
            return f"{stock_code}.SH"
        elif stock_code.startswith("0") or stock_code.startswith("3"):
            return f"{stock_code}.SZ"
        elif stock_code.startswith("8") or stock_code.startswith("4"):
            return f"{stock_code}.BJ"
        else:
            return f"{stock_code}.SH"

    def _convert_to_baostock_code(self, stock_code: str) -> str:
        """转换为 Baostock 代码格式"""
        if "." in stock_code:
            parts = stock_code.split(".")
            return f"{parts[1].lower()}.{parts[0]}"

        if stock_code.startswith("6"):
            return f"sh.{stock_code}"
        elif stock_code.startswith("0") or stock_code.startswith("3"):
            return f"sz.{stock_code}"
        elif stock_code.startswith("8") or stock_code.startswith("4"):
            return f"bj.{stock_code}"
        else:
            return f"sh.{stock_code}"

    def __del__(self):
        """析构函数，确保登出 Baostock"""
        self._logout_baostock()


def demo_usage():
    """使用示例"""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    tushare_token = os.getenv("TUSHARE_TOKEN")

    fetcher = DataSourceFallback(tushare_token=tushare_token)

    print("\n" + "=" * 60)
    print("示例 1: 获取日线历史数据")
    print("=" * 60)
    df, source = fetcher.get_daily_data(
        stock_code="600519", start_date="20240101", end_date="20241231", adjust="qfq"
    )

    if df is not None:
        print(f"\n✅ 数据源: {source}")
        print(f"数据量: {len(df)} 条")
        print(f"\n最新5条数据:")
        print(df.head())
    else:
        print(f"\n❌ 获取失败: {source}")

    print("\n" + "=" * 60)
    print("示例 2: 获取财务数据")
    print("=" * 60)
    data, source = fetcher.get_financial_data(stock_code="600519", year=2024, quarter=3)

    if data is not None:
        print(f"\n✅ 数据源: {source}")
        print(f"包含报表: {list(data.keys())}")
        for name, df in data.items():
            print(f"\n{name}: {len(df)} 条记录")
    else:
        print(f"\n❌ 获取失败: {source}")


if __name__ == "__main__":
    demo_usage()
