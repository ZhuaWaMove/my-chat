#!/usr/bin/env python3
"""
初始化新闻聚合模块
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal
from app.services.category_service import CategoryService
from app.services.feed_fetcher import FeedFetcherService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库表"""
    from app.models.news import Base
    from app.db.session import engine

    logger.info("Creating news database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("News tables created successfully")


def init_default_categories():
    """初始化默认分类"""
    db = SessionLocal()
    try:
        category_service = CategoryService(db)
        category_service.ensure_default_categories()
        logger.info("Default categories initialized")
    finally:
        db.close()


def register_default_plugins():
    """注册默认插件"""
    try:
        from app.plugins.rss_fetcher import rss_fetcher_plugin
        from app.services.feed_fetcher import FeedFetcherService

        # 创建FeedFetcherService实例并注册插件
        feed_fetcher_service = FeedFetcherService()
        feed_fetcher_service.register_plugin(rss_fetcher_plugin)

        logger.info(f"Registered plugin: {rss_fetcher_plugin.plugin_type}")

        # 返回服务实例，可以在其他地方使用
        return feed_fetcher_service
    except ImportError as e:
        logger.warning(f"Failed to import RSS plugin, skipping plugin registration: {e}")
        return None
    except Exception as e:
        logger.error(f"Error registering plugins: {e}")
        return None


async def main():
    """主初始化函数"""
    logger.info("Initializing news aggregation module...")

    # 1. 创建数据库表
    init_database()

    # 2. 初始化默认分类
    init_default_categories()

    # 3. 注册默认插件
    register_default_plugins()

    logger.info("News module initialization completed")


if __name__ == "__main__":
    asyncio.run(main())