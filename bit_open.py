from concurrent.futures import ThreadPoolExecutor

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

import time
import bit_browser_request
import get_file
from kill_bit import terminate_processes
from log_config import setup_logger

logger = setup_logger('bit_blum', 'blum_auto.log')


def create_threads(n, bit_num_start, bit_num_end,  error_list=None):
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
            time.sleep(5)

        logger.info("All task has completed")

        # 等待所有线程完成并检查异常
        for i, future in enumerate(futures):
            try:
                future.result()  # 捕获异常
            except Exception as e:
                logger.error(f"Thread-{i + 1} 发生异常: {e}")


def print_numbers(numbers, thread_name, shuffled_dict):
    """
    打印给定的数字列表

    :param numbers: 数字列表
    :param thread_name: 线程名称
    """
    error = []

    for num in numbers:
        error_num = None
        try:
            # 获取指定序号的数据
            item = shuffled_dict.get(num)
            logger.info(f'{thread_name} 开始 {num} 任务 {item}')
            error_num = execute_tasks(num, item)
            logger.info(f'{thread_name} 结束 {num} 任务 {item}')
        except Exception as e:
            logger.error(f'{thread_name} 执行 {num} 任务报错 {item}')
        if (error_num != None):
            error.append(error_num)


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

        # Close the browser session
        # bit_browser_request.close_browser(id)

    except Exception as e:
        logger.error(f"An error occurred in blum '{seq}'")
        # Close the browser session if an error occurs
        return seq


if __name__ == '__main__':
    # 开启几个线程
    thread_num = 20

    # select = list(range(1, 41))
    select = [1800, 393, 454, 563, 794, 1930, 19, 21, 83, 209, 269, 298, 324, 436, 455, 472, 610, 657, 704, 784, 954,
              993, 1020, 1100, 1188, 1212, 1308, 1351, 1367, 1398, 1480, 1553, 1554, 1630, 1723, 1836, 1988, 1989, 2104,
              2216, 2254, 2281, 2346, 2442, 2449, 2482, 2494, 2499]

    create_threads(thread_num, select)
