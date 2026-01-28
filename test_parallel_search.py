#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试并行搜索功能
"""

import sys
import logging
from src.search_service import SearchService
from src.config import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def test_parallel_search():
    """测试并行搜索"""
    print("=" * 80)
    print("测试并行搜索功能")
    print("=" * 80)

    # 初始化搜索服务
    config = get_config()
    service = SearchService(
        tavily_keys=config.tavily_api_keys,
        exa_keys=config.exa_api_keys,
        serpapi_keys=config.serpapi_keys,
        enable_wallstreetcn=True,
    )

    print(f"\n可用搜索引擎: {[p.name for p in service._providers if p.is_available]}")
    print(f"搜索服务可用: {service.is_available}\n")

    if not service.is_available:
        print("❌ 没有可用的搜索引擎")
        return

    # 测试股票
    stock_code = "600519"
    stock_name = "贵州茅台"

    print(f"开始搜索: {stock_name}({stock_code})")
    print("-" * 80)

    # 执行多维度搜索
    intel_results = service.search_comprehensive_intel(
        stock_code=stock_code, stock_name=stock_name
    )

    # 显示结果
    print("\n" + "=" * 80)
    print("搜索结果汇总")
    print("=" * 80)

    for dim_name, response in intel_results.items():
        print(f"\n【{dim_name}】")
        print(f"  查询: {response.query}")
        print(f"  来源: {response.provider}")
        print(f"  成功: {response.success}")
        print(f"  结果数: {len(response.results)}")
        if not response.success:
            print(f"  错误: {response.error_message}")
        else:
            print(f"  前3条标题:")
            for i, result in enumerate(response.results[:3], 1):
                print(f"    {i}. {result.title}")

    # 格式化报告
    print("\n" + "=" * 80)
    print("格式化报告")
    print("=" * 80)
    report = service.format_intel_report(intel_results, stock_name)
    print(report)

    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_parallel_search()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
