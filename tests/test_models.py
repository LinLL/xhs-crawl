import pytest
from xhs_spider.models import XHSPost

def test_xhs_post_creation():
    """测试XHSPost模型的基本创建功能"""
    post = XHSPost(
        post_id="test123",
        title="测试标题",
        content="测试内容",
        images=["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
    )
    assert post.post_id == "test123"
    assert post.title == "测试标题"
    assert post.content == "测试内容"
    assert len(post.images) == 2

def test_xhs_post_optional_fields():
    """测试XHSPost模型的可选字段"""
    post = XHSPost(post_id="test456")
    assert post.post_id == "test456"
    assert post.title is None
    assert post.content is None
    assert post.images == []

def test_xhs_post_empty_images():
    """测试XHSPost模型的空图片列表"""
    post = XHSPost(
        post_id="test789",
        title="无图片标题",
        content="无图片内容",
        images=[]
    )
    assert post.post_id == "test789"
    assert len(post.images) == 0