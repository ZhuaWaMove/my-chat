from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.news import FeedSource, FeedItem
from app.schemas.news import FeedItemCreate, FeedSourceCreate


class FeedFetcherPlugin(ABC):
    """信源获取插件基类"""

    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """插件类型标识，如 'rss', 'api', 'web'"""
        pass

    @abstractmethod
    async def fetch(self, feed_source: FeedSource) -> List[FeedItemCreate]:
        """从信源获取内容

        Args:
            feed_source: 信源配置

        Returns:
            提取的FeedItem列表
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证插件配置

        Args:
            config: 插件配置字典

        Returns:
            配置是否有效
        """
        pass


class FeedFetcherService:
    """信源获取服务"""

    def __init__(self):
        self._plugins: Dict[str, FeedFetcherPlugin] = {}

    def register_plugin(self, plugin: FeedFetcherPlugin) -> None:
        """注册插件"""
        self._plugins[plugin.plugin_type] = plugin

    def get_plugin(self, plugin_type: str) -> Optional[FeedFetcherPlugin]:
        """获取指定类型的插件"""
        return self._plugins.get(plugin_type)

    def get_available_plugin_types(self) -> List[str]:
        """获取可用的插件类型"""
        return list(self._plugins.keys())

    async def fetch_feed(self, feed_source: FeedSource) -> List[FeedItemCreate]:
        """获取信源内容

        Args:
            feed_source: 信源配置

        Returns:
            提取的FeedItem列表

        Raises:
            ValueError: 插件类型不支持
        """
        plugin = self.get_plugin(feed_source.source_type)
        if not plugin:
            raise ValueError(f"Unsupported feed source type: {feed_source.source_type}")

        return await plugin.fetch(feed_source)

    def validate_feed_source(self, source_type: str, config: Dict[str, Any]) -> bool:
        """验证信源配置

        Args:
            source_type: 信源类型
            config: 配置字典

        Returns:
            配置是否有效
        """
        plugin = self.get_plugin(source_type)
        if not plugin:
            return False

        return plugin.validate_config(config)