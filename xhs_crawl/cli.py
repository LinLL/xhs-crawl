import asyncio
import argparse
from . import XHSSpider

def main():
    args = parse_args()
    asyncio.run(run(args.url, args.dir))

async def run(url: str, save_dir: str = "./downloads"):
    spider = XHSSpider()
    try:
        post = await spider.get_post_data(url)
        if post:
            print(f"标题: {post.title}")
            print(f"内容: {post.content}")
            print(f"发现 {len(post.images)} 张图片")
            await spider.download_images(post, save_dir)
            print(f"图片已保存到: {save_dir}")
    finally:
        await spider.close()

def parse_args():
    parser = argparse.ArgumentParser(description="小红书帖子爬虫")
    parser.add_argument("url", help="小红书帖子URL")
    parser.add_argument("-d", "--dir", default="./downloads", help="图片保存目录")
    return parser.parse_args()

if __name__ == "__main__":
    main()