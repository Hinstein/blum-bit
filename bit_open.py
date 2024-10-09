import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # 从 Selenium 导入 EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

import bit_browser_request
import get_file
from log_config import setup_logger

# 你的其他代码逻辑


logger = setup_logger('bit_blum', 'blum_auto.log')


def create_threads(n, bit_num_start, bit_num_end, error_list=None):
    """
    创建 n 个线程，并平分随机顺序的数字给这些线程打印

    :param n: 线程数量
    :param bit_num_start: 数字范围的起始值
    :param bit_num_end: 数字范围的结束值
    :param error_list: 错误列表，如果不为空，则用该列表的值代替正常的数字范围
    """
    if error_list is not None and len(error_list) > 0:
        numbers = error_list
    else:
        numbers = list(range(bit_num_start, bit_num_end + 1))

    selected_values = get_file.get_id_by_seq(numbers)

    logger.info("Original Dictionary:", selected_values)
    result = np.array_split(numbers, n)
    list_result = [subarray.tolist() for subarray in result]

    # 使用 ThreadPoolExecutor 进行多线程处理
    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = []
        for i in range(n):
            thread_name = f'Thread-{i + 1}'
            future = executor.submit(print_numbers, list_result[i], thread_name, selected_values)
            futures.append(future)

            # 添加启动延迟
            time.sleep(1)

        logger.info("All task has completed")

        # 等待所有线程完成并检查异常
        for i, future in enumerate(futures):
            try:
                future.result()  # 捕获异常
            except Exception as e:
                logger.error(f"Thread-{i + 1} 发生异常: {e}")


def print_numbers(numbers, thread_name, shuffled_dict):
    """
    打印给定的数字列表并处理任务。首先执行所有任务，若有 error_num，再针对这些错误任务进行重试。

    :param numbers: 数字列表
    :param thread_name: 线程名称
    :param shuffled_dict: 随机排序后的字典
    :param reader: 数据读取对象
    """
    error_list = []

    # 第一步：先执行所有任务并记录出错的任务
    for num in numbers:
        try:
            # 获取指定序号的数据
            item = shuffled_dict.get(num)
            logger.info(f'{thread_name} 开始 {num} 任务 {item}')
            error_num = execute_tasks(num, item)

            # 如果返回 error_num，则将任务记录到 error_list 中
            if error_num is not None:
                error_list.append((num, item))
                logger.warning(f'{thread_name} {num} 任务执行失败，需要重新尝试...')

            logger.info(f'{thread_name} 结束 {num} 任务 {item}')

        except Exception as e:
            logger.error(f'{thread_name} 执行 {num} 任务报错: {e} 任务项: {item}')
            # 异常任务也记录到重试列表
            error_list.append((num, item))

    # 第二步：针对有 error_num 的任务进行重试，直到所有任务成功
    while error_list:
        logger.info(f'{thread_name} 开始重试失败的任务列表...')
        retry_errors = []

        # 遍历当前的 error_list
        for num, item in error_list:
            try:
                logger.info(f'{thread_name} 重试 {num} 任务 {item}')
                error_num = execute_tasks(num, item)

                # 如果任务成功（error_num 为 None），任务完成，不再添加到 retry_errors
                if error_num is None:
                    logger.info(f'{thread_name} 成功完成 {num} 任务 {item}')
                else:
                    # 任务失败，加入重试列表
                    retry_errors.append((num, item))
                    logger.warning(f'{thread_name} {num} 任务重试失败，继续重试...')

            except Exception as e:
                logger.error(f'{thread_name} 重试执行 {num} 任务报错: {e} 任务项: {item}')
                retry_errors.append((num, item))

        # 更新 error_list 为 retry_errors，如果列表为空则说明所有任务成功
        error_list = retry_errors

    logger.info(f'{thread_name} 所有任务已成功完成。')


# Function to execute tasks for each profile
def execute_tasks(seq, id):
    try:
        response_data = bit_browser_request.send_post_request(id)
        driver_path = response_data['data']['driver']
        debugger_address = response_data['data']['http']

        # selenium 连接代码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debugger_address)

        chrome_service = Service(driver_path)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # 设置页面加载超时为10秒
        driver.set_page_load_timeout(10)

        # 设置 JavaScript 执行超时为10秒
        driver.set_script_timeout(10)

        driver.get('chrome://settings/clearBrowserData')

        # driver.get('https://web.telegram.org/k/#@BlumCryptoBot')

        # Close the browser session
        # bit_browser_request.close_browser(id)

    except Exception as e:
        logger.error(f"An error occurred in blum '{seq}'")
        # Close the browser session if an error occurs
        return seq


if __name__ == '__main__':
    # 开启几个线程
    thread_num = 15

    # 浏览器编号执行到多少
    bit_num_start = 174
    bit_num_end = 188


    # 电报账号文件
    file_path = 'file/电报账号.xlsx'
    error_list = [1293]
    error_list = None
    create_threads(thread_num, bit_num_start, bit_num_end, error_list)
