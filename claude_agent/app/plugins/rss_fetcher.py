import feedparser
import logging
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

from app.models.news import FeedSource
from app.schemas.news import FeedItemCreate
from app.services.feed_fetcher import FeedFetcherPlugin

logger = logging.getLogger(__name__)


class RSSFetcherPlugin(FeedFetcherPlugin):
    """RSS/Atom信源获取插件"""

    @property
    def plugin_type(self) -> str:
        return "rss"

    async def fetch(self, feed_source: FeedSource) -> List[FeedItemCreate]:
        """从RSS/Atom源获取内容

        Args:
            feed_source: 信源配置

        Returns:
            提取的FeedItem列表
        """
        url = feed_source.url
        config = feed_source.config or {}

        logger.info(f"Fetching RSS feed from {url}")

        try:
            # 解析feed
            feed = feedparser.parse(url)

            if feed.bozo:  # 解析错误
                error_msg = f"Failed to parse RSS feed {url}: {feed.bozo_exception}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            if not feed.entries:
                logger.warning(f"No entries found in RSS feed {url}")
                return []

            items = []
            for entry in feed.entries[:config.get('max_entries', 50)]:  # 限制条目数
                try:
                    feed_item = self._parse_entry(entry, feed_source.id)
                    if feed_item:
                        items.append(feed_item)
                except Exception as e:
                    logger.error(f"Failed to parse RSS entry: {e}")
                    continue

            logger.info(f"Successfully fetched {len(items)} items from {url}")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {url}: {e}")
            raise

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证RSS插件配置

        Args:
            config: 配置字典

        Returns:
            配置是否有效
        """
        # RSS插件可以接受空配置或包含max_entries的配置
        if not config:
            return True

        # 检查max_entries是否为整数且为正数
        if 'max_entries' in config:
            max_entries = config['max_entries']
            if not isinstance(max_entries, int) or max_entries <= 0:
                return False

        # 可以添加其他配置验证
        return True

    def _parse_entry(self, entry: Any, feed_source_id: int) -> FeedItemCreate:
        """解析单个RSS条目

        Args:
            entry: feedparser条目
            feed_source_id: 信源ID

        Returns:
            FeedItemCreate对象
        """
        # 提取标题
        title = getattr(entry, 'title', 'Untitled')
        if not title or title.strip() == '':
            title = 'Untitled'

        # 提取链接
        link = getattr(entry, 'link', None)

        # 提取描述/内容
        description = None
        if hasattr(entry, 'description'):
            description = entry.description
        elif hasattr(entry, 'summary'):
            description = entry.summary

        # 提取内容
        content = None
        if hasattr(entry, 'content'):
            # content是一个列表，取第一个
            if entry.content:
                content = entry.content[0].value

        # 提取发布时间
        published_at = None
        if hasattr(entry, 'published_parsed'):
            if entry.published_parsed:
                published_at = datetime.fromtimestamp(
                    entry.published_parsed.timetuple()
                )
        elif hasattr(entry, 'updated_parsed'):
            if entry.updated_parsed:
                published_at = datetime.fromtimestamp(
                    entry.updated_parsed.timetuple()
                )

        # 提取作者
        author = getattr(entry, 'author', None)

        # 原始数据（用于调试）
        raw_data = {
            'entry_id': getattr(entry, 'id', None),
            'feed_title': getattr(entry, 'feed', {}).get('title', ''),
            'categories': getattr(entry, 'tags', []),
        }

        return FeedItemCreate(
            feed_source_id=feed_source_id,
            title=title[:500],  # 确保不超过数据库限制
            link=link[:1000] if link else None,
            description=description,
            content=content,
            published_at=published_at,
            author=author[:200] if author else None,
            raw_data=raw_data
        )

    def _validate_url(self, url: str) -> bool:
        """验证URL是否有效

        Args:
            url: 要验证的URL

        Returns:
            URL是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


# 插件实例
rss_fetcher_plugin = RSSFetcherPlugin()