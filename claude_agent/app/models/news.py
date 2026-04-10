from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Category(Base):
    """信息分类模型"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    feed_sources = relationship("FeedSource", back_populates="category")
    processed_articles = relationship("ProcessedArticle", back_populates="category")


class FeedSource(Base):
    """信源配置模型"""
    __tablename__ = "feed_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False, default="rss")  # rss, api, web
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    fetch_interval_minutes = Column(Integer, default=60)  # 默认60分钟抓取一次
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    config = Column(JSON, nullable=True)  # 插件特定配置
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="feed_sources")
    feed_items = relationship("FeedItem", back_populates="feed_source")


class FeedItem(Base):
    """原始信息项"""
    __tablename__ = "feed_items"

    id = Column(Integer, primary_key=True, index=True)
    feed_source_id = Column(Integer, ForeignKey("feed_sources.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    author = Column(String(200), nullable=True)
    raw_data = Column(JSON, nullable=True)  # 原始数据，用于调试
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    feed_source = relationship("FeedSource", back_populates="feed_items")
    processed_article = relationship("ProcessedArticle", uselist=False, back_populates="feed_item")


class ProcessedArticle(Base):
    """处理后的文章"""
    __tablename__ = "processed_articles"

    id = Column(Integer, primary_key=True, index=True)
    feed_item_id = Column(Integer, ForeignKey("feed_items.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)  # 关键点列表
    sentiment = Column(String(50), nullable=True)  # positive, negative, neutral
    tags = Column(JSON, nullable=True)  # 标签列表
    processed_content = Column(Text, nullable=True)  # AI处理后的内容
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    feed_item = relationship("FeedItem", back_populates="processed_article")
    category = relationship("Category", back_populates="processed_articles")
    timeline_events = relationship("TimelineEvent", back_populates="processed_article")


class TimelineEvent(Base):
    """时间线事件"""
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    processed_article_id = Column(Integer, ForeignKey("processed_articles.id"), nullable=False, index=True)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False, default="news")  # news, alert, milestone, etc.
    importance = Column(Integer, default=1)  # 1-5，重要性等级
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    processed_article = relationship("ProcessedArticle", back_populates="timeline_events")