from .models import XHSPost
from typing import Optional
from loguru import logger
from httpx import AsyncClient
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import os
import base64
import aiofiles

class XHSSpider:
    """小红书爬虫主类"""
    def __init__(self):
        self.ua = UserAgent()
        self.client = AsyncClient()
        self.headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    async def get_post_data(self, url: str) -> Optional[XHSPost]:
        """获取帖子数据"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                post_id = re.search(r'/explore/([\w]+)', url)
                if not post_id:
                    logger.error(f"Invalid URL format: {url}")
                    return None

                post_id = post_id.group(1)
                response = await self.client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()

                if response.status_code == 302:
                    retry_count += 1
                    logger.warning(f"Encountered redirect (302), attempt {retry_count} of {max_retries}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取标题和内容
                title = soup.find('title')
                content = soup.find('meta', {'name': 'description'})
                
                # 提取图片URL
                image_urls = []
                meta_tags = soup.find_all('meta', {'name': 'og:image'})
                for meta in meta_tags:
                    image_url = meta.get('content')
                    if image_url and image_url.startswith('http://sns-webpic-qc.xhscdn.com'):
                        image_urls.append(image_url)

                return XHSPost(
                    post_id=post_id,
                    title=title.text if title else None,
                    content=content.get('content') if content else None,
                    images=image_urls
                )

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed after {max_retries} attempts: {str(e)}")
                    raise Exception(f"Maximum retries ({max_retries}) exceeded: {str(e)}")
                logger.warning(f"Error on attempt {retry_count}: {str(e)}")

        return None

    async def download_images(self, post: XHSPost, save_dir: str):
        """下载帖子图片，支持URL和base64格式"""
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        for idx, img_data in enumerate(post.images):
            try:
                file_path = os.path.join(save_dir, f"{post.post_id}_{idx}.jpg")

                # 检查是否为base64格式
                if img_data.startswith('data:image'):
                    # 提取base64数据部分
                    base64_data = img_data.split(',')[1]
                    image_data = base64.b64decode(base64_data)
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(image_data)
                    logger.info(f"Saved base64 image: {file_path}")
                else:
                    # 处理URL格式的图片
                    response = await self.client.get(img_data, headers=self.headers)
                    response.raise_for_status()
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(response.content)
                    logger.info(f"Downloaded image: {file_path}")

            except Exception as e:
                logger.error(f"Error processing image {img_data[:100]}: {str(e)}")

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()