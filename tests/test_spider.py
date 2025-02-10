import pytest
import pytest_asyncio
import os
import aiofiles
from xhs_spider import XHSSpider, XHSPost
from unittest.mock import AsyncMock, patch, MagicMock

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def spider():
    _spider = XHSSpider()
    yield _spider
    await _spider.close()

@pytest.mark.asyncio
async def test_get_post_data_success(spider):
    """测试成功获取帖子数据的场景"""
    test_url = "https://www.xiaohongshu.com/explore/test123"
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <title>测试标题</title>
        <meta name="description" content="测试内容">
        <meta name="og:image" content="http://sns-webpic-qc.xhscdn.com/test1.jpg">
        <meta name="og:image" content="http://sns-webpic-qc.xhscdn.com/test2.jpg">
    </html>
    """
    mock_response.status_code = 200

    with patch.object(spider.client, 'get', return_value=mock_response) as mock_get:
        post = await spider.get_post_data(test_url)
        assert post.post_id == "test123"
        assert post.title == "测试标题"
        assert post.content == "测试内容"
        assert len(post.images) == 2
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_get_post_data_invalid_url(spider):
    """测试无效URL的场景"""
    test_url = "https://invalid-url.com"
    post = await spider.get_post_data(test_url)
    assert post is None

@pytest.mark.asyncio
async def test_download_images(spider, tmp_path):
    """测试图片下载功能"""
    post = XHSPost(
        post_id="test123",
        images=[
            "http://sns-webpic-qc.xhscdn.com/test1.jpg",
            "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
        ]
    )

    mock_response = MagicMock()
    mock_response.content = b"fake_image_data"

    with patch.object(spider.client, 'get', return_value=mock_response):
        await spider.download_images(post, str(tmp_path))
        assert os.path.exists(os.path.join(str(tmp_path), f"{post.post_id}_0.jpg"))
        assert os.path.exists(os.path.join(str(tmp_path), f"{post.post_id}_1.jpg"))

@pytest.mark.asyncio
async def test_get_post_data_retry(spider):
    """测试重试机制"""
    test_url = "https://www.xiaohongshu.com/explore/test456"
    mock_response_302 = MagicMock(status_code=302)
    mock_response_200 = MagicMock(status_code=200)
    mock_response_200.text = '<html><title>重试成功</title></html>'

    with patch.object(spider.client, 'get', side_effect=[mock_response_302, mock_response_200]):
        post = await spider.get_post_data(test_url)
        assert post is not None
        assert post.title == "重试成功"