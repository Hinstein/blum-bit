import random
import string

import numpy as np
import time

from pycparser.ply.yacc import error_count
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import re
import requests
from bs4 import BeautifulSoup
import bit_browser_request
import get_file
from get_tel import ExcelDataReader
from kill_bit import terminate_processes

from log_config import setup_logger
from concurrent.futures import ThreadPoolExecutor

logger = setup_logger('blum_auto', 'blum_auto.log')


def change_username(browser_driver, seq):
    # 打开目标页面
    browser_driver.get("https://web.telegram.org/k/")

    time.sleep(4)

    # 获取所有窗口句柄
    handles = browser_driver.window_handles

    # 切换到最后一个打开的窗口（通常是当前活动窗口）
    browser_driver.switch_to.window(handles[-1])

    # # 窗口自适应排列
    # try:
    #     bit_browser_request.windowbounds_flexable()
    # except Exception:
    #     logger.error("窗口自适应排列失败")
    #
    # # Random wait after clicking folders
    # time.sleep(1)

    wait = WebDriverWait(browser_driver, 10)

    # 点击左上角菜单
    try:
        button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button.btn-icon.rp.btn-menu-toggle.sidebar-tools-button.is-visible')))

        # 点击按钮
        button.click()

        # 使用 ActionChains 将鼠标悬浮在按钮上
        actions = ActionChains(browser_driver)
        actions.move_to_element(button).perform()

    except Exception as e:
        print(f"{seq} 点击菜单失败")
        raise  # 达到最大重试次数后，抛出异常

    time.sleep(1)

    # 点击settings
    try:
        button = wait.until(EC.element_to_be_clickable((By.XPATH,
                                                        '//div[@class="btn-menu-item rp-overflow" and .//span[@class="i18n btn-menu-item-text" and text()="Settings"]]')))

        # 点击按钮
        button.click()

    except Exception as e:
        print(f"{seq} 点击settings失败")
        raise

    time.sleep(1)

    # 点击修改按钮
    try:
        button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="column-left"]/div/div[2]/div[1]/button[2]')))

        # 点击按钮
        button.click()

    except Exception as e:
        print(f"{seq} 点击修改按钮失败")
        raise

    time.sleep(1)

    # 修改用户名
    try:
        # 等待 contenteditable div 元素出现
        editable_div = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.input-field-input[contenteditable="true"]')))

        # 获取 div 元素的文本内容
        div_text = editable_div.get_attribute('textContent').strip()

        # 使用正则表达式只保留字母
        div_text_only_letters = re.sub(r'[^a-zA-Z]', '', div_text)

        # 生成随机字符串
        random_text = generate_random_string()

        # 随机选择插入位置
        new_text = insert_random_string(div_text_only_letters, random_text)

        # 等待输入框元素出现
        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="username"]')))

        # 清空输入框
        input_box.clear()

        # 输入修改后的文本
        input_box.send_keys(new_text)

    except Exception as e:
        print(f"{seq} 点击修改按钮失败")
        raise

    time.sleep(2)

    # 点击修改按钮
    try:
        button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn-circle.btn-corner.z-depth-1.rp.is-visible')))

        # 点击按钮
        button.click()

    except Exception as e:
        print(f"{seq} 点击保存按钮失败")
        raise

    time.sleep(3)


def generate_random_string(length=5):
    """生成指定长度的随机字母字符串"""
    return ''.join(random.choices(string.ascii_letters, k=length))


def insert_random_string(original_text, random_text):
    """在原始文本的随机位置插入随机文本"""
    if len(original_text) == 0:
        return random_text
    position = random.randint(0, len(original_text))
    return original_text[:position] + random_text + original_text[position:]


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

        change_username(driver, seq)

        time.sleep(1)

        driver.quit()

        # Close the browser session
        bit_browser_request.close_browser(id)

    except Exception as e:
        logger.error(f"An error occurred in blum '{seq}'")
        # Close the browser session if an error occurs
        time.sleep(1)
        # Close the browser session
        bit_browser_request.close_browser(id)
        return seq


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
    thread_num = 20
    # 浏览器编号执行到多少
    bit_num_start = 1989
    bit_num_end = 2500
    error_list =[ 1554]

    # error_list = None
    create_threads(thread_num, bit_num_start, bit_num_end, error_list)
