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

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.url, args.dir))