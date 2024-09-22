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


def get_password_url(seq, url):
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
        logger.error(f"{seq} 序号请求成功:{data}")
        return data
    else:
        print(f"请求失败，状态码: {response.status_code}")
        return None


def install_script(browser_driver, seq):
    # 打开目标页面
    browser_driver.get("https://github.com/mudachyo/Blum/raw/main/blum-autoclicker.user.js")

    time.sleep(3)

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

    wait = WebDriverWait(browser_driver, 10)
    # 点击安装按钮
    try:
        button = wait.until(EC.element_to_be_clickable((By.ID, 'confirm')))

        # 点击按钮
        button.click()
        print(f"{seq} 安装成功！")

        # actions = ActionChains(browser_driver)
        #
        # # 模拟 Ctrl 按下不松开，按下 Enter，最后松开 Enter
        # actions.key_down(Keys.CONTROL)  # 按下 Ctrl
        # actions.key_down(Keys.ENTER)  # 按下 Enter
        # actions.key_up(Keys.ENTER)  # 松开 Enter
        # actions.key_up(Keys.CONTROL)  # 最后松开 Ctrl
        # actions.perform()

    except Exception as e:
        logger.error(f"{seq} 点击安装按钮失败")
        raise  # 向上抛出异常

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
    wait = WebDriverWait(browser_driver, 30)

    # 如果能够点击launch blum按钮，说明已经登陆了，不需要走下面的流程
    try:
        wait1 = WebDriverWait(browser_driver, 10)
        # 点击 左下角 Launch Blum 按钮
        button_element = wait1.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'div.new-message-bot-commands-view')))
        button_element.click()
        return
    except Exception as e:
        pass

    # 点击 🖊 退到上一层
    try:
        # Random wait after clicking button
        button_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.phone-edit')))
        button_element.click()
    except Exception as e:
        pass

    # 点击 LOGIN BY PHONE NUMBER
    try:
        # Random wait after clicking button
        button_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Log in by phone Number']]")))
        button_element.click()
    except Exception as e:
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

        time.sleep(30)

        try:
            data = get_password_url(seq, tele_result['链接'])
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
    time.sleep(3)

    # 输入密码
    try:
        wait = WebDriverWait(browser_driver, 10)  # 10秒的等待时间

        # 使用 CSS 选择器定位输入框元素
        password_field = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'][name='notsearch_password']"))
        )

        # 点击输入框以确保焦点在该元素上
        password_field.click()

        # 清除输入框中的内容
        password_field.send_keys(Keys.CONTROL + "a")  # 选择所有文本

        for _ in range(10):
            password_field.send_keys(Keys.BACKSPACE)  # 删除文本

        if 1741 >= seq:
            # 直接输入密码
            password_field.send_keys("qweqwe")
        else:
            # 接码平台获取
            password_field.send_keys(data.get('password'))


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


def execute_tasks(seq, id, tele_result):
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
        login_tele(driver, seq, tele_result)

        # 安装blum脚本
        # install_script(driver,seq)

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


def create_threads(n, bit_num_start, bit_num_end, file_path, error_list=None):
    """
    创建 n 个线程，并平分随机顺序的数字给这些线程打印

    :param play_blum_game:
    :param n: 线程数量
    :param total: 总数字数量，默认值为 100
    """
    if error_list is not None and len(error_list) > 0:
        numbers = error_list
    else:
        numbers = list(range(bit_num_start, bit_num_end + 1))

    selected_values = get_file.get_id_by_seq(numbers)

    logger.info("Original Dictionary:", selected_values)
    result = np.array_split(numbers, n)
    list_result = [subarray.tolist() for subarray in result]

    reader = ExcelDataReader(file_path)

    # 使用 ThreadPoolExecutor 进行多线程处理
    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = []
        for i in range(n):
            thread_name = f'Thread-{i + 1}'
            future = executor.submit(print_numbers, list_result[i], thread_name, selected_values, reader)
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
    bit_num_start = 2501
    bit_num_end = 2580

    # 电报账号文件
    file_path = 'file/电报账号.xlsx'
    error_list = [771, 772, 773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 999, 1017, 1025, 1201,
                  1203, 1205, 1206, 1207, 1208, 1209, 1210, 1211, 1212, 1214, 1216, 1217, 1219, 1220, 1222, 1223, 1224,
                  1225, 1226, 1227, 1228, 1230, 1231, 1232, 1233, 1242, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 1259,
                  1260, 1261, 1262, 1263, 1264, 1265, 1267, 1268, 1269, 1270, 1271, 1272, 1274, 1275, 1286, 1287, 1290,
                  1292, 1293, 1298, 1302, 1306, 1307, 1309, 1311, 1313, 1314, 1315, 1319, 1320, 1321, 1322, 1325, 1327,
                  1329, 1332, 1333, 1334, 1337, 1338, 1339, 1340, 1346, 1350, 1512, 1516, 1517, 1518, 1519, 1520, 1521,
                  1526, 1528, 1529, 1530, 1531, 1533, 1534, 1535, 1537, 1543, 1547, 1550, 1555, 1556, 1571, 1572, 1573,
                  1574, 1575, 1576, 1577, 1578, 1579, 1580, 1581, 1582, 1583, 1585, 1586, 1587, 1588, 1589, 1590, 1591,
                  1592, 1643, 1724, 1738, 1740, 1742, 1743, 1768, 1769, 1770, 1771, 1774, 1776, 1777, 1778, 1779, 1780,
                  1781, 1782, 1783, 1784, 1785, 1786, 1787, 1788, 1789, 1790, 1791, 1792, 1793, 1794, 1795, 1796, 1797,
                  1798, 1799, 1803, 1804, 1807, 1810, 1811, 1812, 1813, 1814, 1815, 1816, 1817, 1818, 1819, 1820, 1831,
                  1832, 1833, 1834, 1836, 1837, 1838, 1839, 1840, 1841, 1842, 1844, 1878, 1879, 1882, 1883, 1884, 1885,
                  1886, 1887, 1888, 1977, 1980, 2259, 2339, 2470, 2501, 2502, 2503, 2504, 2505, 2506, 2507, 2508, 2509,
                  2510, 2511, 2512, 2513, 2514, 2515, 2516, 2517, 2518, 2519, 2520, 2521, 2522, 2523, 2524, 2525, 2526,
                  2527, 2528, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 2538, 2539, 2540, 2541, 2542, 2543,
                  2544, 2545, 2546, 2547, 2548, 2549, 2550, 2551, 2552, 2553, 2554, 2555, 2556, 2557, 2558, 2559, 2560,
                  2561, 2562, 2563, 2564, 2565, 2566, 2567, 2568, 2569, 2570, 2571, 2572, 2573, 2574, 2575, 2576, 2577,
                  2578, 2579, 2580]
    # error_list = None
    create_threads(thread_num, bit_num_start, bit_num_end, file_path, error_list)
