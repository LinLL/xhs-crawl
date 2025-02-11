import asyncio
import argparse
from xhs_crawl import XHSSpider

async def main(url: str, save_dir: str = "./downloads"):
    # 初始化爬虫
    spider = XHSSpider()
    
    try:
        # 获取帖子数据
        post = await spider.get_post_data(url)
        if post:
            print(f"标题: {post.title}")
            print(f"内容: {post.content}")
            print(f"发现 {len(post.images)} 张图片")
            
            # 下载图片
            await spider.download_images(post, save_dir)
            print(f"图片已保存到: {save_dir}")
        else:
            print("未能获取帖子数据")
    finally:
        # 关闭客户端连接
        await spider.close()

def parse_args():
    parser = argparse.ArgumentParser(description="小红书帖子爬虫")
    parser.add_argument(
        "url",
        type=str,
        help="小红书帖子URL"
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        default="./downloads",
        help="图片保存目录（默认: ./downloads）"
    )
    return parser.parse_args()



async def test_get_post_data():
    """测试小红书爬虫的get_post_data方法"""
    # 初始化爬虫实例
    spider = XHSSpider()
    
    try:
        # 调用获取帖子数据方法（需要提供实际的小红书帖子URL）
        url = "https://www.xiaohongshu.com/explore/67a6cb3900000000280366ea?xsec_token=CBPcJMnuWQ8xDC_yehXuwzSoWZNkNyBS9jB1oT6wTiVfg=&xsec_source=app_share"
        post_data = await spider.get_post_data(url)
        print(post_data)
        # 验证返回数据
        assert post_data is not None, "帖子数据不应为空"
        assert hasattr(post_data, 'content'), "返回数据应包含content属性"
        assert hasattr(post_data, 'title'), "返回数据应包含title属性"
        assert hasattr(post_data, 'images'), "返回数据应包含images属性"
        assert hasattr(post_data, 'post_id'), "返回数据应包含post_id属性"
    
    finally:
        # 确保关闭客户端连接
        await spider.close()
        
if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.url, args.dir))


