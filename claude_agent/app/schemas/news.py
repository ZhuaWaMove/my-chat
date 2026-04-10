from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# FeedSource Schemas
class FeedSourceBase(BaseModel):
    name: str = Field(..., max_length=200)
    url: str = Field(..., max_length=500)
    source_type: str = Field(..., max_length=50)
    category_id: Optional[int] = None
    is_active: bool = True
    fetch_interval_minutes: int = Field(60, ge=1, le=1440)  # 1分钟到24小时
    config: Optional[Dict[str, Any]] = None


class FeedSourceCreate(FeedSourceBase):
    pass


class FeedSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    url: Optional[str] = Field(None, max_length=500)
    source_type: Optional[str] = Field(None, max_length=50)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    fetch_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    config: Optional[Dict[str, Any]] = None


class FeedSource(FeedSourceBase):
    id: int
    last_fetched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# FeedItem Schemas
class FeedItemBase(BaseModel):
    title: str = Field(..., max_length=500)
    link: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[datetime] = None
    author: Optional[str] = Field(None, max_length=200)
    raw_data: Optional[Dict[str, Any]] = None


class FeedItemCreate(FeedItemBase):
    feed_source_id: int


class FeedItemUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    link: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[datetime] = None
    author: Optional[str] = Field(None, max_length=200)
    raw_data: Optional[Dict[str, Any]] = None


class FeedItem(FeedItemBase):
    id: int
    feed_source_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ProcessedArticle Schemas
class ProcessedArticleBase(BaseModel):
    title: str = Field(..., max_length=500)
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    sentiment: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    processed_content: Optional[str] = None
    processing_status: str = Field(..., max_length=50)


class ProcessedArticleCreate(ProcessedArticleBase):
    feed_item_id: int
    category_id: Optional[int] = None


class ProcessedArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    sentiment: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    processed_content: Optional[str] = None
    processing_status: Optional[str] = Field(None, max_length=50)
    category_id: Optional[int] = None


class ProcessedArticle(ProcessedArticleBase):
    id: int
    feed_item_id: int
    category_id: Optional[int] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# TimelineEvent Schemas
class TimelineEventBase(BaseModel):
    event_date: datetime
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    event_type: str = Field(..., max_length=100)
    importance: int = Field(1, ge=1, le=5)
    event_metadata: Optional[Dict[str, Any]] = None


class TimelineEventCreate(TimelineEventBase):
    processed_article_id: int


class TimelineEventUpdate(BaseModel):
    event_date: Optional[datetime] = None
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    event_type: Optional[str] = Field(None, max_length=100)
    importance: Optional[int] = Field(None, ge=1, le=5)
    event_metadata: Optional[Dict[str, Any]] = None


class TimelineEvent(TimelineEventBase):
    id: int
    processed_article_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# API Response Schemas
class TimelineResponse(BaseModel):
    events: List[TimelineEvent]
    total: int
    page: int
    limit: int


class SearchResponse(BaseModel):
    articles: List[ProcessedArticle]
    total: int
    page: int
    limit: int