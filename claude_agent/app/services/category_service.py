from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.news import Category
from app.schemas.news import CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)


class CategoryService:
    """分类管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_category(self, category_data: CategoryCreate) -> Category:
        """创建分类"""
        # 检查名称是否已存在
        existing = self.db.query(Category).filter(
            func.lower(Category.name) == func.lower(category_data.name)
        ).first()

        if existing:
            raise ValueError(f"Category with name '{category_data.name}' already exists")

        db_category = Category(**category_data.dict())
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def get_category(self, category_id: int) -> Optional[Category]:
        """根据ID获取分类"""
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """根据名称获取分类"""
        return self.db.query(Category).filter(
            func.lower(Category.name) == func.lower(name)
        ).first()

    def get_categories(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Category]:
        """获取分类列表"""
        query = self.db.query(Category)

        if search:
            query = query.filter(
                Category.name.ilike(f"%{search}%") |
                Category.description.ilike(f"%{search}%")
            )

        query = query.order_by(Category.name)
        return query.offset(skip).limit(limit).all()

    def update_category(self, category_id: int, category_data: CategoryUpdate) -> Optional[Category]:
        """更新分类"""
        db_category = self.get_category(category_id)
        if not db_category:
            return None

        # 如果更新名称，检查是否冲突
        if category_data.name is not None and category_data.name != db_category.name:
            existing = self.get_category_by_name(category_data.name)
            if existing and existing.id != category_id:
                raise ValueError(f"Category with name '{category_data.name}' already exists")

        update_data = category_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_category, key, value)

        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def delete_category(self, category_id: int) -> bool:
        """删除分类"""
        db_category = self.get_category(category_id)
        if not db_category:
            return False

        # 检查是否有关联的信源
        if db_category.feed_sources:
            # 可以选择将关联信源的category_id设为null，或者拒绝删除
            # 这里我们拒绝删除
            raise ValueError(
                f"Cannot delete category '{db_category.name}' because it has {len(db_category.feed_sources)} "
                "associated feed sources. Please reassign or delete those sources first."
            )

        self.db.delete(db_category)
        self.db.commit()
        return True

    def get_category_stats(self, category_id: int) -> dict:
        """获取分类统计信息"""
        category = self.get_category(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # 统计关联的信源
        feed_source_count = len(category.feed_sources)

        # 统计处理后的文章
        processed_article_count = len(category.processed_articles)

        # 统计活跃信源
        active_feed_sources = [fs for fs in category.feed_sources if fs.is_active]

        return {
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description
            },
            "feed_source_count": feed_source_count,
            "active_feed_source_count": len(active_feed_sources),
            "processed_article_count": processed_article_count,
            "created_at": category.created_at,
            "updated_at": category.updated_at
        }

    def get_all_categories_with_counts(self) -> List[dict]:
        """获取所有分类及其计数"""
        categories = self.db.query(Category).all()
        result = []

        for category in categories:
            feed_source_count = len(category.feed_sources)
            processed_article_count = len(category.processed_articles)
            active_feed_sources = [fs for fs in category.feed_sources if fs.is_active]

            result.append({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "feed_source_count": feed_source_count,
                "active_feed_source_count": len(active_feed_sources),
                "processed_article_count": processed_article_count,
                "created_at": category.created_at,
                "updated_at": category.updated_at
            })

        return result

    def ensure_default_categories(self):
        """确保存在默认分类"""
        default_categories = [
            {"name": "Technology", "description": "Technology news and updates"},
            {"name": "Business", "description": "Business and finance news"},
            {"name": "Science", "description": "Scientific discoveries and research"},
            {"name": "Health", "description": "Health and medical news"},
            {"name": "Entertainment", "description": "Entertainment and media news"},
            {"name": "Sports", "description": "Sports news and updates"},
            {"name": "Politics", "description": "Political news and analysis"},
            {"name": "General", "description": "General news and events"}
        ]

        for cat_data in default_categories:
            existing = self.get_category_by_name(cat_data["name"])
            if not existing:
                try:
                    self.create_category(CategoryCreate(**cat_data))
                    logger.info(f"Created default category: {cat_data['name']}")
                except ValueError as e:
                    logger.warning(f"Failed to create category {cat_data['name']}: {e}")