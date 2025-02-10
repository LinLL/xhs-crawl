import asyncio
from xhs_crawl import XHSSpider

async def main():
    # 初始化爬虫
    spider = XHSSpider()
    
    try:
        # 示例URL
        url = "https://www.xiaohongshu.com/explore/67a6cb3900000000280366ea?xsec_token=CBPcJMnuWQ8xDC_yehXuwzSoWZNkNyBS9jB1oT6wTiVfg=&xsec_source=app_share"
        
        # 获取帖子数据
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