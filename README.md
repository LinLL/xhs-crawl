# XHS Crawl

小红书内容爬虫工具

## 功能特点

- 支持帖子内容抓取
- 支持图片下载
- 异步处理
- 自动重试机制

## 安装

```bash
pip install xhs-crawl
```

## 使用说明

### 命令行工具

安装完成后，你可以直接使用命令行工具下载小红书帖子内容：

```bash
xhs-crawl "https://www.xiaohongshu.com/explore/[POST_ID]" -d "./downloads"
```

参数说明：
- 第一个参数为小红书帖子URL（必填）
- `-d` 或 `--dir`：指定图片保存目录，默认为 `./downloads`

### Python代码调用

你也可以在Python代码中调用：

```python
import asyncio
from xhs_crawl import XHSSpider

async def main():
    # 初始化爬虫
    spider = XHSSpider()
    
    try:
        # 获取帖子数据
        url = "https://www.xiaohongshu.com/explore/[POST_ID]"
        post = await spider.get_post_data(url)
        
        if post:
            print(f"标题: {post.title}")
            print(f"内容: {post.content}")
            print(f"发现 {len(post.images)} 张图片")
            
            # 下载图片
            await spider.download_images(post, "./downloads")
    finally:
        # 关闭客户端连接
        await spider.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 返回数据结构

`get_post_data` 方法返回的 `post` 对象包含以下属性：

- `post_id`: 帖子ID
- `title`: 帖子标题
- `content`: 帖子正文内容
- `images`: 帖子包含的图片URL列表

## 注意事项

1. 请确保提供的URL格式正确
2. 下载目录需要有写入权限
3. 建议合理控制爬取频率，避免对目标网站造成压力
4. 该工具仅用于学习和研究目的，请遵守相关法律法规

## 许可证

MIT License