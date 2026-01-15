# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 存储层
===================================

职责：
1. 管理 SQLite 数据库连接（单例模式）
2. 定义 ORM 数据模型
3. 提供数据存取接口
4. 实现智能更新逻辑（断点续传）
"""

import logging
import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Date,
    DateTime,
    Integer,
    Text,
    Boolean,
    Index,
    UniqueConstraint,
    select,
    and_,
    desc,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session,
)
from sqlalchemy.exc import IntegrityError

from config import get_config

logger = logging.getLogger(__name__)

# SQLAlchemy ORM 基类
Base = declarative_base()


# === 数据模型定义 ===

class StockDaily(Base):
    """
    股票日线数据模型
    
    存储每日行情数据和计算的技术指标
    支持多股票、多日期的唯一约束
    """
    __tablename__ = 'stock_daily'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 股票代码（如 600519, 000001）
    code = Column(String(10), nullable=False, index=True)
    
    # 交易日期
    date = Column(Date, nullable=False, index=True)
    
    # OHLC 数据
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    
    # 成交数据
    volume = Column(Float)  # 成交量（股）
    amount = Column(Float)  # 成交额（元）
    pct_chg = Column(Float)  # 涨跌幅（%）
    
    # 技术指标
    ma5 = Column(Float)
    ma10 = Column(Float)
    ma20 = Column(Float)
    volume_ratio = Column(Float)  # 量比
    
    # 数据来源
    data_source = Column(String(50))  # 记录数据来源（如 AkshareFetcher）
    
    # 更新时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 唯一约束：同一股票同一日期只能有一条数据
    __table_args__ = (
        UniqueConstraint('code', 'date', name='uix_code_date'),
        Index('ix_code_date', 'code', 'date'),
    )
    
    def __repr__(self):
        return f"<StockDaily(code={self.code}, date={self.date}, close={self.close})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'date': self.date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'pct_chg': self.pct_chg,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'volume_ratio': self.volume_ratio,
            'data_source': self.data_source,
        }


class StockAnalysisResult(Base):
    """股票分析结果表"""
    __tablename__ = 'stock_analysis_result'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 股票信息
    code = Column(String(10), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    analysis_date = Column(Date, nullable=False, index=True)
    
    # 核心指标（独立字段，便于查询）
    sentiment_score = Column(Integer)  # 0-100
    trend_prediction = Column(String(20))  # 强烈看多/看多/震荡/看空/强烈看空
    operation_advice = Column(String(20))  # 买入/加仓/持有/减仓/卖出/观望
    confidence_level = Column(String(10))  # 高/中/低
    
    # 详细分析（JSON格式）
    dashboard = Column(Text)  # 决策仪表盘（JSON）
    trend_analysis = Column(Text)  # 走势分析
    technical_analysis = Column(Text)  # 技术面分析
    fundamental_analysis = Column(Text)  # 基本面分析
    news_summary = Column(Text)  # 新闻摘要
    analysis_summary = Column(Text)  # 综合分析摘要
    key_points = Column(Text)  # 核心看点
    risk_warning = Column(Text)  # 风险提示
    
    # 元数据
    search_performed = Column(Boolean, default=False)
    data_sources = Column(String(200))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('code', 'analysis_date', name='uix_analysis_code_date'),
        Index('ix_analysis_code_date', 'code', 'analysis_date'),
        Index('ix_analysis_score', 'sentiment_score'),
    )
    
    def __repr__(self):
        return f"<StockAnalysisResult(code={self.code}, date={self.analysis_date}, advice={self.operation_advice})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'analysis_date': self.analysis_date,
            'sentiment_score': self.sentiment_score,
            'trend_prediction': self.trend_prediction,
            'operation_advice': self.operation_advice,
            'confidence_level': self.confidence_level,
            'dashboard': json.loads(self.dashboard) if self.dashboard else None,
            'trend_analysis': self.trend_analysis,
            'technical_analysis': self.technical_analysis,
            'fundamental_analysis': self.fundamental_analysis,
            'news_summary': self.news_summary,
            'analysis_summary': self.analysis_summary,
            'key_points': self.key_points,
            'risk_warning': self.risk_warning,
            'search_performed': self.search_performed,
            'data_sources': self.data_sources,
        }


class MarketOverviewModel(Base):
    """大盘概览表"""
    __tablename__ = 'market_overview'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 日期（唯一）
    date = Column(Date, nullable=False, unique=True, index=True)
    
    # 市场统计
    up_count = Column(Integer)
    down_count = Column(Integer)
    flat_count = Column(Integer)
    limit_up_count = Column(Integer)
    limit_down_count = Column(Integer)
    total_amount = Column(Float)  # 两市成交额（亿元）
    north_flow = Column(Float)  # 北向资金（亿元）
    
    # 复杂结构（JSON格式）
    indices = Column(Text)  # 主要指数列表（JSON）
    top_sectors = Column(Text)  # 涨幅前5板块（JSON）
    bottom_sectors = Column(Text)  # 跌幅前5板块（JSON）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<MarketOverviewModel(date={self.date}, up={self.up_count}, down={self.down_count})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'date': self.date,
            'up_count': self.up_count,
            'down_count': self.down_count,
            'flat_count': self.flat_count,
            'limit_up_count': self.limit_up_count,
            'limit_down_count': self.limit_down_count,
            'total_amount': self.total_amount,
            'north_flow': self.north_flow,
            'indices': json.loads(self.indices) if self.indices else [],
            'top_sectors': json.loads(self.top_sectors) if self.top_sectors else [],
            'bottom_sectors': json.loads(self.bottom_sectors) if self.bottom_sectors else [],
        }


class DatabaseManager:
    """
    数据库管理器 - 单例模式
    
    职责：
    1. 管理数据库连接池
    2. 提供 Session 上下文管理
    3. 封装数据存取操作
    """
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_url: 数据库连接 URL（可选，默认从配置读取）
        """
        if self._initialized:
            return
        
        if db_url is None:
            config = get_config()
            db_url = config.get_db_url()
        
        # 创建数据库引擎
        self._engine = create_engine(
            db_url,
            echo=False,  # 设为 True 可查看 SQL 语句
            pool_pre_ping=True,  # 连接健康检查
        )
        
        # 创建 Session 工厂
        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )
        
        # 创建所有表
        Base.metadata.create_all(self._engine)
        
        self._initialized = True
        logger.info(f"数据库初始化完成: {db_url}")
    
    @classmethod
    def get_instance(cls) -> 'DatabaseManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance is not None:
            cls._instance._engine.dispose()
            cls._instance = None
    
    def get_session(self) -> Session:
        """
        获取数据库 Session
        
        使用示例:
            with db.get_session() as session:
                # 执行查询
                session.commit()  # 如果需要
        """
        session = self._SessionLocal()
        try:
            return session
        except Exception:
            session.close()
            raise
    
    def has_today_data(self, code: str, target_date: Optional[date] = None) -> bool:
        """
        检查是否已有指定日期的数据
        
        用于断点续传逻辑：如果已有数据则跳过网络请求
        
        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）
            
        Returns:
            是否存在数据
        """
        if target_date is None:
            target_date = date.today()
        
        with self.get_session() as session:
            result = session.execute(
                select(StockDaily).where(
                    and_(
                        StockDaily.code == code,
                        StockDaily.date == target_date
                    )
                )
            ).scalar_one_or_none()
            
            return result is not None
    
    def get_latest_data(
        self, 
        code: str, 
        days: int = 2
    ) -> List[StockDaily]:
        """
        获取最近 N 天的数据
        
        用于计算"相比昨日"的变化
        
        Args:
            code: 股票代码
            days: 获取天数
            
        Returns:
            StockDaily 对象列表（按日期降序）
        """
        with self.get_session() as session:
            results = session.execute(
                select(StockDaily)
                .where(StockDaily.code == code)
                .order_by(desc(StockDaily.date))
                .limit(days)
            ).scalars().all()
            
            return list(results)
    
    def get_data_range(
        self, 
        code: str, 
        start_date: date, 
        end_date: date
    ) -> List[StockDaily]:
        """
        获取指定日期范围的数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            StockDaily 对象列表
        """
        with self.get_session() as session:
            results = session.execute(
                select(StockDaily)
                .where(
                    and_(
                        StockDaily.code == code,
                        StockDaily.date >= start_date,
                        StockDaily.date <= end_date
                    )
                )
                .order_by(StockDaily.date)
            ).scalars().all()
            
            return list(results)
    
    def save_daily_data(
        self, 
        df: pd.DataFrame, 
        code: str,
        data_source: str = "Unknown"
    ) -> int:
        """
        保存日线数据到数据库
        
        策略：
        - 使用 UPSERT 逻辑（存在则更新，不存在则插入）
        - 跳过已存在的数据，避免重复
        
        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            data_source: 数据来源名称
            
        Returns:
            新增/更新的记录数
        """
        if df is None or df.empty:
            logger.warning(f"保存数据为空，跳过 {code}")
            return 0
        
        saved_count = 0
        
        with self.get_session() as session:
            try:
                for _, row in df.iterrows():
                    # 解析日期
                    row_date = row.get('date')
                    if isinstance(row_date, str):
                        row_date = datetime.strptime(row_date, '%Y-%m-%d').date()
                    elif isinstance(row_date, datetime):
                        row_date = row_date.date()
                    elif isinstance(row_date, pd.Timestamp):
                        row_date = row_date.date()
                    
                    # 检查是否已存在
                    existing = session.execute(
                        select(StockDaily).where(
                            and_(
                                StockDaily.code == code,
                                StockDaily.date == row_date
                            )
                        )
                    ).scalar_one_or_none()
                    
                    if existing:
                        # 更新现有记录
                        existing.open = row.get('open')
                        existing.high = row.get('high')
                        existing.low = row.get('low')
                        existing.close = row.get('close')
                        existing.volume = row.get('volume')
                        existing.amount = row.get('amount')
                        existing.pct_chg = row.get('pct_chg')
                        existing.ma5 = row.get('ma5')
                        existing.ma10 = row.get('ma10')
                        existing.ma20 = row.get('ma20')
                        existing.volume_ratio = row.get('volume_ratio')
                        existing.data_source = data_source
                        existing.updated_at = datetime.now()
                    else:
                        # 创建新记录
                        record = StockDaily(
                            code=code,
                            date=row_date,
                            open=row.get('open'),
                            high=row.get('high'),
                            low=row.get('low'),
                            close=row.get('close'),
                            volume=row.get('volume'),
                            amount=row.get('amount'),
                            pct_chg=row.get('pct_chg'),
                            ma5=row.get('ma5'),
                            ma10=row.get('ma10'),
                            ma20=row.get('ma20'),
                            volume_ratio=row.get('volume_ratio'),
                            data_source=data_source,
                        )
                        session.add(record)
                        saved_count += 1
                
                session.commit()
                logger.info(f"保存 {code} 数据成功，新增 {saved_count} 条")
                
            except Exception as e:
                session.rollback()
                logger.error(f"保存 {code} 数据失败: {e}")
                raise
        
        return saved_count
    
    def get_analysis_context(
        self, 
        code: str,
        target_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取分析所需的上下文数据
        
        返回今日数据 + 昨日数据的对比信息
        
        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）
            
        Returns:
            包含今日数据、昨日对比等信息的字典
        """
        if target_date is None:
            target_date = date.today()
        
        # 获取最近2天数据
        recent_data = self.get_latest_data(code, days=2)
        
        if not recent_data:
            logger.warning(f"未找到 {code} 的数据")
            return None
        
        today_data = recent_data[0]
        yesterday_data = recent_data[1] if len(recent_data) > 1 else None
        
        context = {
            'code': code,
            'date': today_data.date.isoformat(),
            'today': today_data.to_dict(),
        }
        
        if yesterday_data:
            context['yesterday'] = yesterday_data.to_dict()
            
            # 计算相比昨日的变化
            if yesterday_data.volume and yesterday_data.volume > 0:
                context['volume_change_ratio'] = round(
                    today_data.volume / yesterday_data.volume, 2
                )
            
            if yesterday_data.close and yesterday_data.close > 0:
                context['price_change_ratio'] = round(
                    (today_data.close - yesterday_data.close) / yesterday_data.close * 100, 2
                )
            
            # 均线形态判断
            context['ma_status'] = self._analyze_ma_status(today_data)
        
        return context
    
    def _analyze_ma_status(self, data: StockDaily) -> str:
        """
        分析均线形态
        
        判断条件：
        - 多头排列：close > ma5 > ma10 > ma20
        - 空头排列：close < ma5 < ma10 < ma20
        - 震荡整理：其他情况
        """
        close = data.close or 0
        ma5 = data.ma5 or 0
        ma10 = data.ma10 or 0
        ma20 = data.ma20 or 0
        
        if close > ma5 > ma10 > ma20 > 0:
            return "多头排列 📈"
        elif close < ma5 < ma10 < ma20 and ma20 > 0:
            return "空头排列 📉"
        elif close > ma5 and ma5 > ma10:
            return "短期向好 🔼"
        elif close < ma5 and ma5 < ma10:
            return "短期走弱 🔽"
        else:
            return "震荡整理 ↔️"
    
    def save_analysis_result(
        self,
        result,  # AnalysisResult 对象
        analysis_date: date
    ) -> bool:
        """
        保存个股分析结果到数据库
        
        策略：
        - 只保存成功的分析（result.success == True）
        - 使用UPSERT逻辑（存在则更新）
        - dashboard字段转换为JSON字符串
        
        Args:
            result: AnalysisResult对象
            analysis_date: 分析日期
            
        Returns:
            是否保存成功
        """
        if not result.success:
            logger.debug(f"跳过保存失败的分析结果: {result.code}")
            return False
        
        with self.get_session() as session:
            try:
                existing = session.execute(
                    select(StockAnalysisResult).where(
                        and_(
                            StockAnalysisResult.code == result.code,
                            StockAnalysisResult.analysis_date == analysis_date
                        )
                    )
                ).scalar_one_or_none()
                
                dashboard_json = json.dumps(result.dashboard, ensure_ascii=False) if result.dashboard else None
                
                if existing:
                    existing.name = result.name
                    existing.sentiment_score = result.sentiment_score
                    existing.trend_prediction = result.trend_prediction
                    existing.operation_advice = result.operation_advice
                    existing.confidence_level = result.confidence_level
                    existing.dashboard = dashboard_json
                    existing.trend_analysis = result.trend_analysis
                    existing.technical_analysis = result.technical_analysis
                    existing.fundamental_analysis = result.fundamental_analysis
                    existing.news_summary = result.news_summary
                    existing.analysis_summary = result.analysis_summary
                    existing.key_points = result.key_points
                    existing.risk_warning = result.risk_warning
                    existing.search_performed = result.search_performed
                    existing.data_sources = result.data_sources
                    logger.debug(f"更新分析结果: {result.code}")
                else:
                    record = StockAnalysisResult(
                        code=result.code,
                        name=result.name,
                        analysis_date=analysis_date,
                        sentiment_score=result.sentiment_score,
                        trend_prediction=result.trend_prediction,
                        operation_advice=result.operation_advice,
                        confidence_level=result.confidence_level,
                        dashboard=dashboard_json,
                        trend_analysis=result.trend_analysis,
                        technical_analysis=result.technical_analysis,
                        fundamental_analysis=result.fundamental_analysis,
                        news_summary=result.news_summary,
                        analysis_summary=result.analysis_summary,
                        key_points=result.key_points,
                        risk_warning=result.risk_warning,
                        search_performed=result.search_performed,
                        data_sources=result.data_sources,
                    )
                    session.add(record)
                    logger.debug(f"新增分析结果: {result.code}")
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"保存分析结果失败 {result.code}: {e}")
                return False
    
    def save_market_overview(
        self,
        overview  # MarketOverview 对象
    ) -> bool:
        """
        保存大盘数据到数据库
        
        策略：
        - 使用UPSERT逻辑（存在则更新）
        - indices, top_sectors, bottom_sectors转换为JSON字符串
        
        Args:
            overview: MarketOverview对象
            
        Returns:
            是否保存成功
        """
        with self.get_session() as session:
            try:
                if isinstance(overview.date, str):
                    overview_date = datetime.strptime(overview.date, '%Y-%m-%d').date()
                else:
                    overview_date = overview.date
                
                existing = session.execute(
                    select(MarketOverviewModel).where(
                        MarketOverviewModel.date == overview_date
                    )
                ).scalar_one_or_none()
                
                indices_json = json.dumps(
                    [{'code': idx.code, 'name': idx.name, 'close': idx.close, 'pct_chg': idx.pct_chg} 
                     for idx in overview.indices],
                    ensure_ascii=False
                ) if overview.indices else None
                
                top_sectors_json = json.dumps(overview.top_sectors, ensure_ascii=False) if overview.top_sectors else None
                bottom_sectors_json = json.dumps(overview.bottom_sectors, ensure_ascii=False) if overview.bottom_sectors else None
                
                if existing:
                    existing.up_count = overview.up_count
                    existing.down_count = overview.down_count
                    existing.flat_count = overview.flat_count
                    existing.limit_up_count = overview.limit_up_count
                    existing.limit_down_count = overview.limit_down_count
                    existing.total_amount = overview.total_amount
                    existing.north_flow = overview.north_flow
                    existing.indices = indices_json
                    existing.top_sectors = top_sectors_json
                    existing.bottom_sectors = bottom_sectors_json
                    existing.updated_at = datetime.now()
                    logger.debug(f"更新大盘数据: {overview_date}")
                else:
                    record = MarketOverviewModel(
                        date=overview_date,
                        up_count=overview.up_count,
                        down_count=overview.down_count,
                        flat_count=overview.flat_count,
                        limit_up_count=overview.limit_up_count,
                        limit_down_count=overview.limit_down_count,
                        total_amount=overview.total_amount,
                        north_flow=overview.north_flow,
                        indices=indices_json,
                        top_sectors=top_sectors_json,
                        bottom_sectors=bottom_sectors_json,
                    )
                    session.add(record)
                    logger.debug(f"新增大盘数据: {overview_date}")
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"保存大盘数据失败: {e}")
                return False


# 便捷函数
def get_db() -> DatabaseManager:
    """获取数据库管理器实例的快捷方式"""
    return DatabaseManager.get_instance()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    db = get_db()
    
    print("=== 数据库测试 ===")
    print(f"数据库初始化成功")
    
    # 测试检查今日数据
    has_data = db.has_today_data('600519')
    print(f"茅台今日是否有数据: {has_data}")
    
    # 测试保存数据
    test_df = pd.DataFrame({
        'date': [date.today()],
        'open': [1800.0],
        'high': [1850.0],
        'low': [1780.0],
        'close': [1820.0],
        'volume': [10000000],
        'amount': [18200000000],
        'pct_chg': [1.5],
        'ma5': [1810.0],
        'ma10': [1800.0],
        'ma20': [1790.0],
        'volume_ratio': [1.2],
    })
    
    saved = db.save_daily_data(test_df, '600519', 'TestSource')
    print(f"保存测试数据: {saved} 条")
    
    # 测试获取上下文
    context = db.get_analysis_context('600519')
    print(f"分析上下文: {context}")
