import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.news import FeedItem, ProcessedArticle, Category
from app.schemas.news import ProcessedArticleCreate
from app.services.claude import claude_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ArticleProcessorService:
    """AI文章处理服务"""

    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.is_processing = False

    async def process_article(self, feed_item: FeedItem, category: Optional[Category] = None) -> ProcessedArticleCreate:
        """处理单篇文章

        Args:
            feed_item: 原始FeedItem
            category: 可选分类

        Returns:
            处理后的文章数据
        """
        try:
            # 准备待处理内容
            content = feed_item.content or feed_item.description or ""
            if not content.strip():
                content = feed_item.title

            # 构建提示
            prompt = self._build_processing_prompt(
                title=feed_item.title,
                content=content,
                author=feed_item.author,
                published_date=feed_item.published_at
            )

            # 调用Claude服务
            response = await self._call_claude(prompt)

            # 解析响应
            processed_data = self._parse_claude_response(response)

            # 创建ProcessedArticleCreate对象
            return ProcessedArticleCreate(
                feed_item_id=feed_item.id,
                category_id=category.id if category else None,
                title=processed_data.get("title", feed_item.title),
                summary=processed_data.get("summary"),
                key_points=processed_data.get("key_points", []),
                sentiment=processed_data.get("sentiment"),
                tags=processed_data.get("tags", []),
                processed_content=processed_data.get("processed_content"),
                processing_status="completed"
            )

        except Exception as e:
            logger.error(f"Failed to process article {feed_item.id}: {e}")
            # 返回失败状态
            return ProcessedArticleCreate(
                feed_item_id=feed_item.id,
                category_id=category.id if category else None,
                title=feed_item.title,
                summary=f"Processing failed: {str(e)}",
                key_points=[],
                sentiment=None,
                tags=[],
                processed_content=None,
                processing_status="failed"
            )

    async def process_batch(self, feed_items: List[FeedItem]) -> List[ProcessedArticleCreate]:
        """批量处理文章

        Args:
            feed_items: FeedItem列表

        Returns:
            处理后的文章数据列表
        """
        if not settings.enable_ai_processing:
            logger.info("AI processing is disabled")
            return []

        results = []
        batch_size = min(settings.max_articles_per_batch, len(feed_items))

        for i in range(0, len(feed_items), batch_size):
            batch = feed_items[i:i + batch_size]
            tasks = [self.process_article(item) for item in batch]

            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing error: {result}")
                    else:
                        results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")

            # 避免速率限制
            await asyncio.sleep(1)

        return results

    async def start_processing_worker(self):
        """启动处理工作线程"""
        if self.is_processing:
            return

        self.is_processing = True
        logger.info("Article processing worker started")

        while self.is_processing:
            try:
                # 从队列获取任务
                task = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=5.0
                )

                if task is None:  # 停止信号
                    break

                feed_item, category = task
                await self.process_article(feed_item, category)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Processing worker error: {e}")

    def stop_processing_worker(self):
        """停止处理工作线程"""
        self.is_processing = False
        logger.info("Article processing worker stopped")

    def _build_processing_prompt(self, title: str, content: str,
                                author: Optional[str] = None,
                                published_date: Optional[datetime] = None) -> str:
        """构建处理提示"""
        prompt = f"""Please analyze the following news article:

Title: {title}

Content: {content[:2000]}  # 限制内容长度

Please provide:
1. A concise summary (2-3 sentences)
2. 3-5 key points
3. Sentiment analysis (positive, negative, or neutral)
4. Relevant tags (5-10 keywords)
5. Processed content (cleaned and formatted version)

Format your response as JSON with the following structure:
{{
  "summary": "string",
  "key_points": ["string1", "string2", ...],
  "sentiment": "positive/negative/neutral",
  "tags": ["tag1", "tag2", ...],
  "processed_content": "string"
}}"""

        if author:
            prompt += f"\nAuthor: {author}"
        if published_date:
            prompt += f"\nPublished: {published_date.isoformat()}"

        return prompt

    async def _call_claude(self, prompt: str) -> str:
        """调用Claude API"""
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        # 使用同步方法，但包装在异步中
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: claude_service.chat(messages)
        )

        return response

    def _parse_claude_response(self, response: str) -> Dict[str, Any]:
        """解析Claude响应"""
        import json
        import re

        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # 如果没有找到JSON，返回默认结构
                return {
                    "summary": response[:500],
                    "key_points": [],
                    "sentiment": "neutral",
                    "tags": [],
                    "processed_content": response
                }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            return {
                "summary": response[:500],
                "key_points": [],
                "sentiment": "neutral",
                "tags": [],
                "processed_content": response
            }


# 单例实例
article_processor_service = ArticleProcessorService()