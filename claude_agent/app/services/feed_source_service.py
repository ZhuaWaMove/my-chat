from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.news import FeedSource
from app.schemas.news import FeedSourceCreate, FeedSourceUpdate
from app.services.feed_fetcher import FeedFetcherService

logger = logging.getLogger(__name__)


class FeedSourceService:
    """信源管理服务"""

    def __init__(self, db: Session, feed_fetcher_service: Optional[FeedFetcherService] = None):
        self.db = db
        self.feed_fetcher_service = feed_fetcher_service or FeedFetcherService()

    def create_feed_source(self, feed_source_data: FeedSourceCreate) -> FeedSource:
        """创建信源

        Args:
            feed_source_data: 信源数据

        Returns:
            创建的FeedSource

        Raises:
            ValueError: 信源类型不支持或配置无效
        """
        # 验证信源类型
        if not self.feed_fetcher_service.get_plugin(feed_source_data.source_type):
            raise ValueError(f"Unsupported feed source type: {feed_source_data.source_type}")

        # 验证配置（如果提供）
        if feed_source_data.config:
            if not self.feed_fetcher_service.validate_feed_source(
                feed_source_data.source_type, feed_source_data.config
            ):
                raise ValueError(f"Invalid configuration for source type: {feed_source_data.source_type}")

        db_feed_source = FeedSource(**feed_source_data.dict())
        self.db.add(db_feed_source)
        self.db.commit()
        self.db.refresh(db_feed_source)
        return db_feed_source

    def get_feed_source(self, source_id: int) -> Optional[FeedSource]:
        """根据ID获取信源"""
        return self.db.query(FeedSource).filter(FeedSource.id == source_id).first()

    def get_feed_sources(
        self,
        active_only: bool = True,
        category_id: Optional[int] = None,
        source_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeedSource]:
        """获取信源列表"""
        query = self.db.query(FeedSource)

        if active_only:
            query = query.filter(FeedSource.is_active == True)

        if category_id is not None:
            query = query.filter(FeedSource.category_id == category_id)

        if source_type:
            query = query.filter(FeedSource.source_type == source_type)

        query = query.order_by(FeedSource.name)
        return query.offset(skip).limit(limit).all()

    def update_feed_source(
        self,
        source_id: int,
        feed_source_data: FeedSourceUpdate
    ) -> Optional[FeedSource]:
        """更新信源"""
        db_feed_source = self.get_feed_source(source_id)
        if not db_feed_source:
            return None

        update_data = feed_source_data.dict(exclude_unset=True)

        # 验证源类型（如果更新）
        if 'source_type' in update_data:
            new_type = update_data['source_type']
            if not self.feed_fetcher_service.get_plugin(new_type):
                raise ValueError(f"Unsupported feed source type: {new_type}")

        # 验证配置（如果提供）
        if 'config' in update_data and update_data['config']:
            source_type = update_data.get('source_type', db_feed_source.source_type)
            if not self.feed_fetcher_service.validate_feed_source(source_type, update_data['config']):
                raise ValueError(f"Invalid configuration for source type: {source_type}")

        for key, value in update_data.items():
            setattr(db_feed_source, key, value)

        self.db.commit()
        self.db.refresh(db_feed_source)
        return db_feed_source

    def delete_feed_source(self, source_id: int) -> bool:
        """删除信源"""
        db_feed_source = self.get_feed_source(source_id)
        if not db_feed_source:
            return False

        # 检查是否有关联的FeedItem（可选，根据业务需求）
        # 这里我们允许删除，关联的FeedItem可以通过级联删除或设为null处理

        self.db.delete(db_feed_source)
        self.db.commit()
        return True

    def update_last_fetched(self, source_id: int, timestamp: Optional[datetime] = None) -> Optional[FeedSource]:
        """更新最后抓取时间"""
        db_feed_source = self.get_feed_source(source_id)
        if not db_feed_source:
            return None

        db_feed_source.last_fetched_at = timestamp or datetime.now()
        self.db.commit()
        self.db.refresh(db_feed_source)
        return db_feed_source

    def toggle_active(self, source_id: int) -> Optional[FeedSource]:
        """切换激活状态"""
        db_feed_source = self.get_feed_source(source_id)
        if not db_feed_source:
            return None

        db_feed_source.is_active = not db_feed_source.is_active
        self.db.commit()
        self.db.refresh(db_feed_source)
        return db_feed_source

    def get_feed_source_stats(self) -> Dict[str, Any]:
        """获取信源统计信息"""
        total = self.db.query(func.count(FeedSource.id)).scalar() or 0
        active = self.db.query(func.count(FeedSource.id)).filter(FeedSource.is_active == True).scalar() or 0

        # 按类型统计
        by_type = dict(
            self.db.query(FeedSource.source_type, func.count(FeedSource.id))
            .group_by(FeedSource.source_type)
            .all()
        )

        # 按分类统计
        by_category = dict(
            self.db.query(FeedSource.category_id, func.count(FeedSource.id))
            .filter(FeedSource.category_id.isnot(None))
            .group_by(FeedSource.category_id)
            .all()
        )

        # 最近抓取的信源
        recent_fetched = self.db.query(FeedSource)\
            .filter(FeedSource.last_fetched_at.isnot(None))\
            .order_by(FeedSource.last_fetched_at.desc())\
            .limit(5).all()

        return {
            "total_sources": total,
            "active_sources": active,
            "inactive_sources": total - active,
            "by_type": by_type,
            "by_category": by_category,
            "recently_fetched": [
                {
                    "id": fs.id,
                    "name": fs.name,
                    "last_fetched": fs.last_fetched_at.isoformat() if fs.last_fetched_at else None
                }
                for fs in recent_fetched
            ]
        }

    def get_sources_due_for_fetch(self, limit: int = 10) -> List[FeedSource]:
        """获取需要抓取的信源"""
        query = self.db.query(FeedSource).filter(
            FeedSource.is_active == True,
            FeedSource.fetch_interval_minutes > 0
        )

        # 从未抓取过的信源优先
        never_fetched = query.filter(FeedSource.last_fetched_at.is_(None))\
            .order_by(FeedSource.created_at)\
            .limit(limit).all()

        if len(never_fetched) >= limit:
            return never_fetched[:limit]

        # 计算需要抓取的信源
        remaining = limit - len(never_fetched)
        if remaining > 0:
            import datetime as dt
            from sqlalchemy import or_

            cutoff = datetime.now() - dt.timedelta(minutes=60)  # 默认时间，实际应根据间隔计算
            due_for_fetch = query.filter(
                FeedSource.last_fetched_at.isnot(None),
                or_(
                    FeedSource.last_fetched_at < cutoff,
                    FeedSource.last_fetched_at.is_(None)
                )
            ).order_by(FeedSource.last_fetched_at).limit(remaining).all()

            return never_fetched + due_for_fetch

        return never_fetched

    def validate_feed_source_url(self, url: str, source_type: str) -> bool:
        """验证信源URL是否有效"""
        # 基础URL验证
        if not url or len(url) > 500:
            return False

        # 根据源类型进行额外验证
        if source_type == "rss":
            return url.startswith(('http://', 'https://'))
        elif source_type == "api":
            return url.startswith(('http://', 'https://'))
        elif source_type == "web":
            return url.startswith(('http://', 'https://'))
        else:
            return False