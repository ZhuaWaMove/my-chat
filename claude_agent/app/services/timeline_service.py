from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
import logging

from app.models.news import ProcessedArticle, TimelineEvent, Category
from app.schemas.news import TimelineEventCreate, TimelineResponse

logger = logging.getLogger(__name__)


class TimelineService:
    """时间线服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_timeline_events(self, processed_article: ProcessedArticle) -> TimelineEventCreate:
        """为处理后的文章生成时间线事件

        Args:
            processed_article: 处理后的文章

        Returns:
            时间线事件数据
        """
        # 使用文章发布日期作为事件日期，如果没有则使用处理日期
        event_date = None
        if processed_article.feed_item and processed_article.feed_item.published_at:
            event_date = processed_article.feed_item.published_at
        else:
            event_date = processed_article.processed_at or processed_article.created_at

        # 确定事件类型
        event_type = "news"
        sentiment = processed_article.sentiment or "neutral"

        # 根据情感和重要性调整事件类型
        if sentiment == "positive":
            event_type = "positive_news"
        elif sentiment == "negative":
            event_type = "alert"

        # 计算重要性（基于关键点数量、标签数量等）
        importance = self._calculate_importance(processed_article)

        return TimelineEventCreate(
            processed_article_id=processed_article.id,
            event_date=event_date,
            title=processed_article.title,
            description=processed_article.summary,
            event_type=event_type,
            importance=importance,
            event_metadata={
                "sentiment": sentiment,
                "tags": processed_article.tags or [],
                "key_points": processed_article.key_points or [],
                "category_id": processed_article.category_id
            }
        )

    def create_timeline_event(self, event_data: TimelineEventCreate) -> TimelineEvent:
        """创建时间线事件"""
        db_event = TimelineEvent(**event_data.dict())
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def get_timeline_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        categories: Optional[List[int]] = None,
        importance_min: Optional[int] = None,
        importance_max: Optional[int] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> TimelineResponse:
        """获取时间线事件

        Args:
            start_date: 开始日期
            end_date: 结束日期
            event_types: 事件类型过滤
            categories: 分类过滤
            importance_min: 最小重要性
            importance_max: 最大重要性
            search_query: 搜索查询
            page: 页码
            limit: 每页数量

        Returns:
            时间线响应
        """
        query = self.db.query(TimelineEvent)

        # 连接ProcessedArticle和Category进行过滤
        query = query.join(ProcessedArticle)

        # 日期过滤
        if start_date:
            query = query.filter(TimelineEvent.event_date >= start_date)
        if end_date:
            query = query.filter(TimelineEvent.event_date <= end_date)

        # 事件类型过滤
        if event_types:
            query = query.filter(TimelineEvent.event_type.in_(event_types))

        # 分类过滤
        if categories:
            query = query.filter(ProcessedArticle.category_id.in_(categories))

        # 重要性过滤
        if importance_min is not None:
            query = query.filter(TimelineEvent.importance >= importance_min)
        if importance_max is not None:
            query = query.filter(TimelineEvent.importance <= importance_max)

        # 搜索查询
        if search_query:
            search_filter = or_(
                TimelineEvent.title.ilike(f"%{search_query}%"),
                TimelineEvent.description.ilike(f"%{search_query}%"),
                ProcessedArticle.title.ilike(f"%{search_query}%"),
                ProcessedArticle.summary.ilike(f"%{search_query}%")
            )
            query = query.filter(search_filter)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        query = query.order_by(desc(TimelineEvent.event_date))
        events = query.offset(offset).limit(limit).all()

        return TimelineResponse(
            events=events,
            total=total,
            page=page,
            limit=limit
        )

    def get_event_by_id(self, event_id: int) -> Optional[TimelineEvent]:
        """根据ID获取事件"""
        return self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()

    def update_event(self, event_id: int, event_data: Dict[str, Any]) -> Optional[TimelineEvent]:
        """更新事件"""
        db_event = self.get_event_by_id(event_id)
        if not db_event:
            return None

        for key, value in event_data.items():
            if hasattr(db_event, key) and value is not None:
                setattr(db_event, key, value)

        db_event.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def delete_event(self, event_id: int) -> bool:
        """删除事件"""
        db_event = self.get_event_by_id(event_id)
        if not db_event:
            return False

        self.db.delete(db_event)
        self.db.commit()
        return True

    def _calculate_importance(self, processed_article: ProcessedArticle) -> int:
        """计算文章重要性（1-5）"""
        importance = 1  # 默认

        # 基于关键点数量
        if processed_article.key_points:
            importance += min(len(processed_article.key_points) // 2, 2)

        # 基于标签数量
        if processed_article.tags:
            importance += min(len(processed_article.tags) // 3, 1)

        # 基于情感
        if processed_article.sentiment == "positive":
            importance += 1
        elif processed_article.sentiment == "negative":
            importance += 2  # 负面新闻通常更重要

        # 确保在1-5范围内
        return max(1, min(importance, 5))

    def generate_timeline_from_articles(self, articles: List[ProcessedArticle]) -> List[TimelineEvent]:
        """从文章列表生成时间线事件"""
        events = []
        for article in articles:
            event_data = self.generate_timeline_events(article)
            db_event = self.create_timeline_event(event_data)
            events.append(db_event)

        return events

    def get_timeline_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取时间线统计信息"""
        query = self.db.query(TimelineEvent)

        if start_date:
            query = query.filter(TimelineEvent.event_date >= start_date)
        if end_date:
            query = query.filter(TimelineEvent.event_date <= end_date)

        total_events = query.count()
        events_by_type = dict(
            self.db.query(TimelineEvent.event_type, func.count(TimelineEvent.id))
            .group_by(TimelineEvent.event_type)
            .all()
        )
        avg_importance = self.db.query(func.avg(TimelineEvent.importance)).scalar() or 0

        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "average_importance": float(avg_importance),
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }