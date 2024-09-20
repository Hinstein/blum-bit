import random
import numpy as np
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import requests
from bs4 import BeautifulSoup
import bit_browser_request
import get_file
from kill_bit import terminate_processes

from log_config import setup_logger
from concurrent.futures import ThreadPoolExecutor

logger = setup_logger('blum_auto', 'blum_auto.log')


def get_password_url(url):
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        html_content = response.text

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取验证码和密码
        code = soup.find('td', {'id': 'code'}).text
        password = soup.find('td', {'id': 'password'}).text

        # 将提取的内容保存到字典中
        data = {
            'code': code,
            'password': password
        }

        print(data)
        return data
    else:
        print(f"请求失败，状态码: {response.status_code}")
        return None


def install_script(browser_driver, seq):
    # 打开目标页面
    browser_driver.get("https://github.com/mudachyo/Blum/raw/main/blum-autoclicker.user.js")

    time.sleep(6)

    # 获取所有窗口句柄
    handles = browser_driver.window_handles

    # 切换到最后一个打开的窗口（通常是当前活动窗口）
    browser_driver.switch_to.window(handles[-1])

    # 窗口自适应排列
    try:
        bit_browser_request.windowbounds_flexable()
    except Exception:
        logger.error("窗口自适应排列失败")

    # Random wait after clicking folders
    time.sleep(3)

    wait = WebDriverWait(browser_driver, 5)
    # 点击安装按钮

    max_retries = 5  # 最大重试次数
    for attempt in range(1, max_retries + 1):
        try:
            button = wait.until(EC.element_to_be_clickable((By.ID, 'confirm')))

            # 点击按钮
            button.click()
            print(f"{seq} 安装成功！")
            break  # 如果点击成功，退出循环

        except Exception as e:
            print(f"{seq} 点击安装按钮失败，正在重试 ({attempt}/{max_retries})...")
            if attempt == max_retries:
                raise  # 达到最大重试次数后，抛出异常

    time.sleep(3)


def execute_tasks(seq, id):
    try:
        response_data = bit_browser_request.send_post_request(id)
        driver_path = response_data['data']['driver']
        debugger_address = response_data['data']['http']

        # selenium 连接代码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debugger_address)
        chrome_options.add_argument("--load-extension=/path/to/your/extension")

        chrome_service = Service(driver_path)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # 设置页面加载超时为10秒
        driver.set_page_load_timeout(10)

        # 设置 JavaScript 执行超时为10秒
        driver.set_script_timeout(10)

        # 安装blum脚本
        install_script(driver, seq)

        time.sleep(3)

        driver.quit()

        # Close the browser session
        bit_browser_request.close_browser(id)

    except Exception as e:
        logger.error(f"An error occurred in blum '{seq}'")
        # Close the browser session if an error occurs
        time.sleep(3)
        bit_browser_request.close_browser(id)
        return seq
    finally:
        # 删除进程
        time.sleep(3)
        terminate_processes(bit_browser_request.get_browser_pids(id))


def get_item_by_index(items, index):
    """
    通过索引获取键值对

    :param items: 键值对列表
    :param index: 索引
    :return: 键值对
    """
    if 0 <= index <= len(items):
        return items[index]
    else:
        return None


def generate_random_sequence(start=1, end=100):
    """
    生成一个从 start 到 end 的数字列表，并随机打乱顺序

    :param start: 起始数字，默认值为 1
    :param end: 结束数字，默认值为 100
    :return: 随机打乱顺序的数字列表
    """
    numbers = list(range(start, end))
    random.shuffle(numbers)
    return numbers


def print_numbers(numbers, thread_name, shuffled_dict, reader):
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
            tele_result = reader.get_data_by_serial_number(num)
            item = shuffled_dict.get(num)
            logger.info(f'{thread_name} 开始 {num} 任务 {item}')
            error_num = execute_tasks(num, item, tele_result)

            # 如果返回 error_num，则将任务记录到 error_list 中
            if error_num is not None:
                error_list.append((num, item, tele_result))
                logger.warning(f'{thread_name} {num} 任务执行失败，需要重新尝试...')

            logger.info(f'{thread_name} 结束 {num} 任务 {item}')

        except Exception as e:
            logger.error(f'{thread_name} 执行 {num} 任务报错: {e} 任务项: {item}')
            # 异常任务也记录到重试列表
            error_list.append((num, item, tele_result))

    # 第二步：针对有 error_num 的任务进行重试，直到所有任务成功
    while error_list:
        logger.info(f'{thread_name} 开始重试失败的任务列表...')
        retry_errors = []

        # 遍历当前的 error_list
        for num, item, tele_result in error_list:
            try:
                logger.info(f'{thread_name} 重试 {num} 任务 {item}')
                error_num = execute_tasks(num, item, tele_result)

                # 如果任务成功（error_num 为 None），任务完成，不再添加到 retry_errors
                if error_num is None:
                    logger.info(f'{thread_name} 成功完成 {num} 任务 {item}')
                else:
                    # 任务失败，加入重试列表
                    retry_errors.append((num, item, tele_result))
                    logger.warning(f'{thread_name} {num} 任务重试失败，继续重试...')

            except Exception as e:
                logger.error(f'{thread_name} 重试执行 {num} 任务报错: {e} 任务项: {item}')
                retry_errors.append((num, item, tele_result))

        # 更新 error_list 为 retry_errors，如果列表为空则说明所有任务成功
        error_list = retry_errors

    logger.info(f'{thread_name} 所有任务已成功完成。')


def shuffle_dict(input_dict):
    """
    打乱字典的键值对顺序

    :param input_dict: 输入的字典
    :return: 顺序被打乱的新字典
    """
    # 将字典的键值对转换为列表
    items = list(input_dict.items())
    # 随机打乱列表
    random.shuffle(items)
    # 创建一个新的字典，并将打乱顺序后的键值对插入其中
    shuffled_dict = dict(items)
    return shuffled_dict


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
            time.sleep(5)

        logger.info("All task has completed")

        # 等待所有线程完成并检查异常
        for i, future in enumerate(futures):
            try:
                future.result()  # 捕获异常
            except Exception as e:
                logger.error(f"Thread-{i + 1} 发生异常: {e}")


# 不使用定时任务，单独运行
# n是线程个数， total是你要完成到哪个浏览器
if __name__ == '__main__':
    # 开启几个线程
    thread_num = 1
    # 浏览器编号执行到多少
    bit_num_start = 1000
    bit_num_end = 1500
    error_list = [1345]
    # error_list = None
    create_threads(thread_num, bit_num_start, bit_num_end, error_list)
