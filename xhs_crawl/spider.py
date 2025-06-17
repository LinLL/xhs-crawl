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
import random
import asyncio
import json

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
        
    def _get_nested_value(self, data: dict, keys: list):
        """
        从嵌套字典中安全地获取值。
        """
        current_data = data
        for key in keys:
            if isinstance(current_data, dict) and key in current_data:
                current_data = current_data[key]
            else:
                return None
        return current_data

    async def _extract_initial_state_data(self, soup: BeautifulSoup, post_id: str) -> dict:
        """
        从script标签的window.__INITIAL_STATE__中提取帖子标题、描述和图片列表。
        """
        data = {}
        script_tag = soup.find('script', string=re.compile(r'window\.__INITIAL_STATE__'))
        if script_tag:
            script_content = script_tag.string
            try:
                # 使用 split 提取 JS 对象字符串
                json_str_match = script_content.split("__INITIAL_STATE__=")[-1]
                json_str_match = json_str_match.split("</script>")[0].strip()

                # 修复非标准JSON：将 undefined 替换为 null
                json_str_match = json_str_match.replace('undefined', 'null')

                # 移除可能的尾随分号
                if json_str_match.endswith(';'):
                    json_str_match = json_str_match[:-1]
                
                if json_str_match:
                    json_data = json.loads(json_str_match)
                    
                    # 根据新的JSON结构更新提取逻辑
                    note_detail_path = ['note', 'noteDetailMap', post_id, 'note']
                    note_detail = self._get_nested_value(json_data, note_detail_path)
                    
                    if note_detail:
                        title = note_detail.get('title')
                        if title:
                            data['title'] = title
                        
                        desc = note_detail.get('desc')
                        if desc:
                            data['desc'] = desc
                            
                        image_list = note_detail.get('imageList')
                        if image_list:
                            image_urls = []
                            for img in image_list:
                                if isinstance(img, dict):
                                    # 优先使用 urlDefault
                                    if img.get('urlDefault'):
                                        image_urls.append(img.get('urlDefault'))
                                    # 其次尝试从 infoList 中获取
                                    elif img.get('infoList'):
                                        info_list = img.get('infoList')
                                        if isinstance(info_list, list) and len(info_list) > 0 and info_list[0].get('url'):
                                            image_urls.append(info_list[0].get('url'))
                            data['image_list'] = image_urls

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from script tag: {e}")
            except Exception as e:
                logger.error(f"Error extracting data from __INITIAL_STATE__: {e}")
        return data

    async def get_post_data(self, url: str) -> Optional[XHSPost]:
        """获取帖子数据"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 尝试匹配 /explore/ 格式
                post_id_match = re.search(r'/explore/([\w]+)', url)
                
                if not post_id_match:
                    # 如果 /explore/ 格式不匹配，则尝试匹配 /discovery/item/ 格式
                    post_id_match = re.search(r'/discovery/item/([\w]+)', url)
                
                if not post_id_match:
                    logger.error(f"Invalid URL format: {url}")
                    return None

                post_id = post_id_match.group(1)
                response = await self.client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()

                if response.status_code == 302:
                    retry_count += 1
                    logger.warning(f"Encountered redirect (302), attempt {retry_count} of {max_retries}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 尝试从 __INITIAL_STATE__ 提取数据
                initial_state_data = await self._extract_initial_state_data(soup, post_id)
                if initial_state_data.get('title'): # 检查是否成功提取到数据
                    logger.info("Successfully extracted data from __INITIAL_STATE__.")
                    return XHSPost(
                        post_id=post_id,
                        title=initial_state_data.get('title'),
                        content=initial_state_data.get('desc'),
                        images=initial_state_data.get('image_list', [])
                    )

                logger.warning("Failed to extract data from __INITIAL_STATE__, falling back to meta tags.")
                # 提取标题和内容
                title = soup.find('title')
                content = soup.find('meta', {'name': 'description'})
                if content and content.get('content') == "":
                    # 遇到空内容时随机等待1-5秒后重试
                    wait_time = random.uniform(1, 5)
                    await asyncio.sleep(wait_time)
                    self.headers['User-Agent'] = self.ua.random
                    logger.warning(f"Empty content found, waiting {wait_time:.2f}s before retrying... (attempt {retry_count + 1} of {max_retries})")
                    retry_count += 1
                    continue
                
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