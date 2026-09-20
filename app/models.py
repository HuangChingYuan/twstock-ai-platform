"""
自建台股資料庫 schema (Slide 06)：
Stock / Price / Revenue / Financial / Institutional / News / MOPS / Indicators / AIAnalysis / Backtest
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True)
    stock_id = Column(String(10), unique=True, index=True, nullable=False)  # e.g. "2330"
    name = Column(String(50))
    market = Column(String(10))  # TWSE / TPEX
    industry = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship("Price", back_populates="stock", cascade="all, delete-orphan")
    revenues = relationship("Revenue", back_populates="stock", cascade="all, delete-orphan")
    financials = relationship("Financial", back_populates="stock", cascade="all, delete-orphan")
    institutional = relationship("Institutional", back_populates="stock", cascade="all, delete-orphan")
    news = relationship("News", back_populates="stock", cascade="all, delete-orphan")
    mops = relationship("MOPS", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("Indicator", back_populates="stock", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="stock", cascade="all, delete-orphan")
    backtests = relationship("BacktestResult", back_populates="stock", cascade="all, delete-orphan")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_price_stock_date"),)

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    stock = relationship("Stock", back_populates="prices")


class Revenue(Base):
    __tablename__ = "revenues"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_revenue_stock_date"),)

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)  # 月營收所屬月份 (以當月最後一天表示)
    revenue = Column(Float)
    revenue_yoy = Column(Float)   # 營收年增率 %
    revenue_mom = Column(Float)   # 營收月增率 %

    stock = relationship("Stock", back_populates="revenues")


class Financial(Base):
    __tablename__ = "financials"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_financial_stock_date"),)

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)  # 財報所屬季度結束日
    eps = Column(Float)
    roe = Column(Float)
    roa = Column(Float)
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    per = Column(Float)
    pbr = Column(Float)
    free_cash_flow = Column(Float, nullable=True)

    stock = relationship("Stock", back_populates="financials")


class Institutional(Base):
    __tablename__ = "institutional"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_inst_stock_date"),)

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    foreign_investors = Column(Float, default=0)   # 外資買賣超 (股)
    investment_trust = Column(Float, default=0)    # 投信買賣超 (股)
    dealer = Column(Float, default=0)               # 自營商買賣超 (股)

    stock = relationship("Stock", back_populates="institutional")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    published_at = Column(DateTime)
    title = Column(String(255))
    source = Column(String(100))
    url = Column(String(500))
    sentiment = Column(Float, nullable=True)  # -1 ~ 1，由 NLP/LLM 產生
    summary = Column(Text, nullable=True)

    stock = relationship("Stock", back_populates="news")


class MOPS(Base):
    __tablename__ = "mops_announcements"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date)
    subject = Column(String(255))
    category = Column(String(100), nullable=True)  # 財報 / 重訊 / 股利 ...
    url = Column(String(500), nullable=True)

    stock = relationship("Stock", back_populates="mops")


class Indicator(Base):
    __tablename__ = "indicators"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_indicator_stock_date"),)

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    ma5 = Column(Float)
    ma20 = Column(Float)
    ma60 = Column(Float)
    rsi14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_hist = Column(Float)
    k = Column(Float)
    d = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    atr14 = Column(Float)
    technical_score = Column(Float, nullable=True)

    stock = relationship("Stock", back_populates="indicators")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    technical_score = Column(Float)
    fundamental_score = Column(Float)
    news_score = Column(Float)
    overall_score = Column(Float)
    view = Column(String(10))          # 偏多 / 中立 / 偏空
    reasons = Column(Text)             # JSON list
    risks = Column(Text)               # JSON list
    report_text = Column(Text)         # LLM 產出的完整報告文字

    stock = relationship("Stock", back_populates="ai_analyses")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    strategy_name = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    total_return = Column(Float)
    win_rate = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    trade_count = Column(Integer)
    equity_curve_json = Column(Text)  # JSON: [{date, equity}]

    stock = relationship("Stock", back_populates="backtests")
