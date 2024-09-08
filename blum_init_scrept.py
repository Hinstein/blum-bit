import random
import numpy as np
import time

from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import requests
from bs4 import BeautifulSoup
import bit_browser_request
import get_file
from get_tel import ExcelDataReader
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
    # try:
    #     bit_browser_request.windowbounds_flexable()
    # except Exception:
    #     logger.error("窗口自适应排列失败")

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


def login_tele(browser_driver, seq, tele_result):
    # 打开目标页面
    browser_driver.get("https://web.telegram.org/k/#@BlumCryptoBot")

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
    time.sleep(random.uniform(1, 3))
    wait = WebDriverWait(browser_driver, 10)

    # 点击 LOGIN BY PHONE NUMBER
    try:
        # Random wait after clicking button
        button_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Log in by phone Number']]")))
        button_element.click()
    except Exception as e:
        logger.error(f"blum '{seq}' : 点击 LOGIN BY PHONE NUMBER 失败,'{e}'")
        pass

    # Random wait after clicking button
    time.sleep(random.uniform(1, 3))

    # 填入电话号码
    try:
        # Random wait after clicking button
        # 定位 contenteditable 的 <div> 元素
        input_field = wait.until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[2]/div[1]"))
        )

        # 点击输入框以确保焦点在该元素上
        input_field.click()

        # 清除输入框中的内容
        input_field.send_keys(Keys.CONTROL + "a")  # 选择所有文本

        for _ in range(5):
            input_field.send_keys(Keys.BACKSPACE)  # 删除文本

        phone_number = tele_result['账号']

        # 写入数字到输入框
        input_field.send_keys(phone_number)  # 替换为你想要输入的数字
    except Exception as e:
        logger.error(f"blum '{seq}' : 填入电话号码 失败,'{e}'")
        raise

    # 点击next按钮
    try:
        # 使用 XPath 根据文本内容定位按钮
        button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Next']]"))
        )

        # 点击该按钮
        button.click()
    except Exception as e:
        logger.error(f"blum '{seq}' : 点击next按钮 失败,'{e}'")
        raise

    # 输入验证码
    try:
        # 使用 XPath 根据文本内容定位按钮
        # 定义显式等待
        cod_wait = WebDriverWait(browser_driver, 30)  # 10秒的等待时间

        # 使用 XPath 定位输入框元素
        input_field = cod_wait.until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div/div[3]/div/input")))

        try:
            data = get_password_url(tele_result['链接'])
        except Exception as e:
            logger.error(f"blum '{seq}' : 获取链接失败,'{e}'")
            raise

        # 点击该按钮
        input_field.click()

        input_field.send_keys(data.get('code'))

        time.sleep(5)
    except Exception as e:
        logger.error(f"blum '{seq}' : 点击next按钮 失败,'{e}'")
        raise

    # Random wait after clicking button
    time.sleep(10)

    # 输入密码
    try:
        wait = WebDriverWait(browser_driver, 10)  # 10秒的等待时间

        # 使用 CSS 选择器定位输入框元素
        password_field = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'][name='notsearch_password']"))
        )

        # 输入密码
        password_field.send_keys(data.get('password'))  # 替换为你想要输入的密码

    except Exception as e:
        logger.error(f"blum '{seq}' : 点击next按钮 失败,'{e}'")
        raise

    time.sleep(5)

    # 点击next按钮
    try:
        # 使用 XPath 定位按钮元素
        button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="auth-pages"]/div/div[2]/div[5]/div/div[2]/button'))
        )

        # 点击按钮
        button.click()
    except Exception as e:
        logger.error(f"点击按钮失败: {e}")
        raise  # 向上抛出异常

    time.sleep(15)


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

        # 账号登陆
        # login_tele(driver, seq, tele_result)

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
