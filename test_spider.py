#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 不启动 Flask 服务
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def test_spider():
    """测试爬虫功能"""
    logger.info("=" * 60)
    logger.info("快速测试爬虫功能")
    logger.info("=" * 60)

    # 导入爬虫类
    try:
        from iyf_spider import IYFSpider, HAS_CLOUDSCRAPER
    except ImportError as e:
        logger.error(f"导入失败: {e}")
        logger.error("请先安装依赖: pip install -r requirements.txt")
        return False

    # 检查 cloudscraper
    if HAS_CLOUDSCRAPER:
        logger.info("✅ cloudscraper 已安装")
    else:
        logger.warning("⚠️  cloudscraper 未安装，建议安装以获得更好效果")
        logger.warning("   安装命令: pip install cloudscraper")

    # 创建爬虫实例
    logger.info("\n创建爬虫实例...")
    spider = IYFSpider()

    # 测试1: 获取列表
    logger.info("\n" + "=" * 60)
    logger.info("测试 1/3: 获取视频列表")
    logger.info("=" * 60)
    try:
        videos = spider.get_list(page=1)
        if videos:
            logger.info(f"✅ 成功获取 {len(videos)} 个视频")
            logger.info(f"   示例: {videos[0]['vod_name']}")
        else:
            logger.error("❌ 列表为空")
            return False
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False

    # 测试2: 获取详情
    logger.info("\n" + "=" * 60)
    logger.info("测试 2/3: 获取视频详情")
    logger.info("=" * 60)
    if videos:
        try:
            vod_id = videos[0]['vod_id']
            logger.info(f"   视频ID: {vod_id}")

            detail = spider.get_detail(vod_id)
            if detail:
                logger.info(f"✅ 成功获取详情: {detail['vod_name']}")
                has_play = detail.get('vod_play_url', '').strip() != ''
                logger.info(f"   播放链接: {'✅ 已找到' if has_play else '⚠️  未找到'}")

                if detail.get('vod_actor'):
                    logger.info(f"   主演: {detail['vod_actor'][:50]}")
                if detail.get('vod_content'):
                    logger.info(f"   简介: {detail['vod_content'][:50]}...")
            else:
                logger.error("❌ 详情获取失败")
                return False
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}", exc_info=True)
            return False

    # 测试3: 搜索
    logger.info("\n" + "=" * 60)
    logger.info("测试 3/3: 搜索功能")
    logger.info("=" * 60)
    try:
        keyword = "爱情"
        logger.info(f"   关键词: {keyword}")

        results = spider.search(keyword)
        if results:
            logger.info(f"✅ 搜索成功，找到 {len(results)} 个结果")
            logger.info(f"   示例: {results[0]['vod_name']}")
        else:
            logger.warning("⚠️  搜索结果为空")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False

    # 统计信息
    stats = spider.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("统计信息")
    logger.info("=" * 60)
    logger.info(f"   请求次数: {stats['request_count']}")
    logger.info(f"   缓存项数: {stats['cache_size']}")
    logger.info(f"   Cookie数: {stats['cookies']}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有测试通过!")
    logger.info("=" * 60)

    return True


if __name__ == '__main__':
    success = test_spider()
    sys.exit(0 if success else 1)
