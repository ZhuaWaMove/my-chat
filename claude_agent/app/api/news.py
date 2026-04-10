from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.news import (
    TimelineResponse,
    FeedSource,
    FeedSourceCreate,
    FeedSourceUpdate,
    FeedItem,
    ProcessedArticle,
    SearchResponse
)
from app.services.timeline_service import TimelineService
from app.services.category_service import CategoryService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# 时间线相关端点
@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    categories: Optional[List[int]] = Query(None),
    importance_min: Optional[int] = Query(None, ge=1, le=5),
    importance_max: Optional[int] = Query(None, ge=1, le=5),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取时间线事件"""
    service = TimelineService(db)
    return service.get_timeline_events(
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        categories=categories,
        importance_min=importance_min,
        importance_max=importance_max,
        search_query=search,
        page=page,
        limit=limit
    )


@router.get("/timeline/stats")
def get_timeline_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """获取时间线统计信息"""
    service = TimelineService(db)
    return service.get_timeline_stats(start_date=start_date, end_date=end_date)


# 信源相关端点
@router.get("/feed-sources", response_model=List[FeedSource])
def get_feed_sources(
    active_only: bool = Query(True),
    category_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取信源列表"""
    # TODO: 实现FeedSourceService后更新
    from app.models.news import FeedSource as FeedSourceModel
    query = db.query(FeedSourceModel)

    if active_only:
        query = query.filter(FeedSourceModel.is_active == True)

    if category_id is not None:
        query = query.filter(FeedSourceModel.category_id == category_id)

    return query.offset(skip).limit(limit).all()


@router.post("/feed-sources", response_model=FeedSource, status_code=201)
def create_feed_source(
    feed_source: FeedSourceCreate,
    db: Session = Depends(get_db)
):
    """创建信源"""
    # TODO: 实现FeedSourceService后更新
    from app.models.news import FeedSource as FeedSourceModel
    db_feed_source = FeedSourceModel(**feed_source.dict())
    db.add(db_feed_source)
    db.commit()
    db.refresh(db_feed_source)
    return db_feed_source


@router.put("/feed-sources/{source_id}", response_model=FeedSource)
def update_feed_source(
    source_id: int,
    feed_source: FeedSourceUpdate,
    db: Session = Depends(get_db)
):
    """更新信源"""
    # TODO: 实现FeedSourceService后更新
    from app.models.news import FeedSource as FeedSourceModel
    db_feed_source = db.query(FeedSourceModel).filter(FeedSourceModel.id == source_id).first()
    if not db_feed_source:
        raise HTTPException(status_code=404, detail="Feed source not found")

    update_data = feed_source.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_feed_source, key, value)

    db.commit()
    db.refresh(db_feed_source)
    return db_feed_source


@router.delete("/feed-sources/{source_id}", status_code=204)
def delete_feed_source(source_id: int, db: Session = Depends(get_db)):
    """删除信源"""
    # TODO: 实现FeedSourceService后更新
    from app.models.news import FeedSource as FeedSourceModel
    db_feed_source = db.query(FeedSourceModel).filter(FeedSourceModel.id == source_id).first()
    if not db_feed_source:
        raise HTTPException(status_code=404, detail="Feed source not found")

    db.delete(db_feed_source)
    db.commit()


@router.post("/fetch", status_code=202)
def fetch_feeds(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """手动触发信源抓取"""
    # TODO: 实现FeedFetcherService后更新
    logger.info("Manual feed fetch triggered")
    # 这里可以添加后台任务
    return {"message": "Feed fetch started in background"}


@router.get("/search", response_model=SearchResponse)
def search_articles(
    query: str = Query(..., min_length=1),
    category_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索文章"""
    # TODO: 实现搜索功能
    from app.models.news import ProcessedArticle as ProcessedArticleModel
    from sqlalchemy import or_

    search_query = db.query(ProcessedArticleModel)

    # 搜索条件
    if query:
        search_filter = or_(
            ProcessedArticleModel.title.ilike(f"%{query}%"),
            ProcessedArticleModel.summary.ilike(f"%{query}%"),
            ProcessedArticleModel.processed_content.ilike(f"%{query}%")
        )
        search_query = search_query.filter(search_filter)

    if category_id is not None:
        search_query = search_query.filter(ProcessedArticleModel.category_id == category_id)

    if start_date:
        # 需要连接FeedItem获取发布时间
        from app.models.news import FeedItem
        search_query = search_query.join(FeedItem).filter(FeedItem.published_at >= start_date)

    if end_date:
        from app.models.news import FeedItem
        search_query = search_query.join(FeedItem).filter(FeedItem.published_at <= end_date)

    # 总数
    total = search_query.count()

    # 分页
    offset = (page - 1) * limit
    articles = search_query.offset(offset).limit(limit).all()

    return SearchResponse(
        articles=articles,
        total=total,
        page=page,
        limit=limit
    )


@router.put("/{article_id}/process", response_model=ProcessedArticle)
def process_article(
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """手动触发文章处理"""
    # TODO: 实现ArticleProcessorService后更新
    from app.models.news import FeedItem, ProcessedArticle as ProcessedArticleModel

    feed_item = db.query(FeedItem).filter(FeedItem.id == article_id).first()
    if not feed_item:
        raise HTTPException(status_code=404, detail="Feed item not found")

    # 检查是否已处理
    existing = db.query(ProcessedArticleModel).filter(
        ProcessedArticleModel.feed_item_id == article_id
    ).first()

    if existing:
        return existing

    logger.info(f"Manual processing triggered for article {article_id}")
    # 这里可以添加后台处理任务
    return {"message": "Article processing started in background"}


@router.get("/categories", response_model=List[FeedSource])
def get_feed_sources_by_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取指定分类的信源"""
    # TODO: 实现FeedSourceService后更新
    from app.models.news import FeedSource as FeedSourceModel
    return db.query(FeedSourceModel).filter(FeedSourceModel.category_id == category_id).all()