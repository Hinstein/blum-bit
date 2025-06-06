import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import schedule
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import bit_browser_request
import get_file
from bit_blume import clean_old_label
from blum_main import conditional_timeout
from kill_bit import terminate_processes
from log_config import setup_logger

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
        random.shuffle(numbers)

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
            time.sleep(15)

        logger.info("All task has completed")

        # 等待所有线程完成并检查异常
        for i, future in enumerate(futures):
            try:
                future.result()  # 捕获异常
            except Exception as e:
                logger.error(f"Thread-{i + 1} 发生异常: {e}")


def print_numbers(numbers, thread_name, shuffled_dict, task_timeout=1000):
    """
    打印给定的数字列表并处理任务。首先执行所有任务，若有 error_num，再针对这些错误任务进行重试。

    :param numbers: 数字列表
    :param thread_name: 线程名称
    :param shuffled_dict: 随机排序后的字典
    :param reader: 数据读取对象
    """
    error_list = []

    # 使用装饰器来决定是否启用超时
    @conditional_timeout(task_timeout, True)
    def task_function(seq, id):
        return execute_tasks(seq, id)

    # 第一步：先执行所有任务并记录出错的任务
    for seq in numbers:
        error_num = None
        try:
            id = shuffled_dict.get(seq)
            logger.info(f'{thread_name} 开始 {seq} 任务 {id}')

            try:
                task_function(seq, id)
                logger.info(f'{thread_name} 结束 {seq} 任务 {id}')
            except TimeoutError:
                logger.warning(f'{thread_name} 执行 {seq} 任务超时 {id}')
            except Exception as e:
                logger.error(f'{thread_name} 执行 {seq} 任务报错 {id}，错误信息: {e}')
            finally:
                terminate_processes(bit_browser_request.get_browser_pids(id))

        except Exception as e:
            logger.error(f'{thread_name} 执行 {seq} 任务报错 {id}，错误信息: {e}')

        if error_num is not None:
            error_list.append(error_num)

    # # 第二步：针对有 error_num 的任务进行重试，直到所有任务成功
    # while error_list:
    #     logger.info(f'{thread_name} 开始重试失败的任务列表...')
    #     retry_errors = []
    #
    #     # 遍历当前的 error_list
    #     for num, item in error_list:
    #         try:
    #             logger.info(f'{thread_name} 重试 {num} 任务 {item}')
    #             error_num = execute_tasks(num, item)
    #
    #             # 如果任务成功（error_num 为 None），任务完成，不再添加到 retry_errors
    #             if error_num is None:
    #                 logger.info(f'{thread_name} 成功完成 {num} 任务 {item}')
    #             else:
    #                 # 任务失败，加入重试列表
    #                 retry_errors.append((num, item))
    #                 logger.warning(f'{thread_name} {num} 任务重试失败，继续重试...')
    #
    #         except Exception as e:
    #             logger.error(f'{thread_name} 重试执行 {num} 任务报错: {e} 任务项: {item}')
    #             retry_errors.append((num, item))
    #
    #     # 更新 error_list 为 retry_errors，如果列表为空则说明所有任务成功
    #     error_list = retry_errors

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

        do_task(driver, seq)

    except Exception as e:
        logger.error(f"An error occurred in blum '{seq}'")
        # Close the browser session if an error occurs
        return seq

    finally:
        clean_old_label(driver)
        # Close the browser session
        bit_browser_request.close_browser(id)


def click_visible_buttons(browser_driver, css_selector, wait_time=2):
    """
    增强版按钮点击逻辑：
    1. 每次点击成功后重新获取按钮列表
    2. 持续处理动态变化的按钮
    """
    total_click = 0
    is_started = 'started' in css_selector
    processed_titles = set()  # 记录已处理的标题

    while True:
        # 每次循环重新获取最新按钮列表
        current_buttons = browser_driver.find_elements(By.CSS_SELECTOR, css_selector)
        if not current_buttons:
            break

        clicked_in_loop = False

        for button in list(current_buttons):  # 转换为列表避免实时更新问题
            try:
                # 动态获取标题元素
                title_element = button.find_element(By.XPATH, "..//div[@class='title']")
                title_text = title_element.text

                if title_text in processed_titles:
                    continue

                if title_text not in forbidden_click:
                    # 滚动到最新位置
                    browser_driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
                                                  button)
                    time.sleep(0.3)

                    if button.is_displayed() and button.is_enabled():
                        # 点击前克隆必要信息
                        current_title = title_text

                        button.click()
                        time.sleep(wait_time)
                        clicked_in_loop = True
                        processed_titles.add(current_title)  # 记录已处理标题

                        # 特殊逻辑处理
                        if is_started:
                            total_click += 1
                            if total_click > 5:
                                clean_old_label(browser_driver)
                                iframe = browser_driver.find_element(By.CSS_SELECTOR, 'iframe.payment-verification')
                                browser_driver.switch_to.frame(iframe)
                                total_click = 0

                        # 点击后立即跳出循环重新获取列表
                        break  # 关键点：处理一个按钮后重新获取列表

            except StaleElementReferenceException:
                # 元素已失效时自动进入下一次循环
                break
            except Exception as e:
                continue

        # 如果本轮没有点击，说明处理完成
        if not clicked_in_loop:
            break

    return len(processed_titles) > 0


def is_element_with_class_present(driver, class_name):
    """
    检查是否存在具有指定类名的元素。

    :param driver: Selenium WebDriver
    :param class_name: 要检查的类名
    :return: 如果元素存在返回 True，否则返回 False
    """
    try:
        # 使用类名选择器查找元素
        element = driver.find_element(By.CSS_SELECTOR, class_name)
        return True if element else False
    except NoSuchElementException:
        return False


def do_task(browser_driver, seq):
    global task_items
    try:
        browser_driver.get("https://web.telegram.org/k/#@BlumCryptoBot")
        time.sleep(random.uniform(1, 3))
        wait = WebDriverWait(browser_driver, 15)

        # 窗口自适应排列
        # try:
        #     bit_browser_request.windowbounds_flexable()
        # except Exception:
        #     logger.error("窗口自适应排列失败")

        long_wait = WebDriverWait(browser_driver, 45)
        # 点击 Launch Blum 按钮
        button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.new-message-bot-commands-view')))
        button_element.click()
        time.sleep(random.uniform(1, 3))

        # 点击防止弹出 start 面板
        button_css_selector = "button.popup-button.btn.primary.rp"
        try:
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_css_selector)))
            button.click()
        except Exception:
            pass

        # 切换到游戏窗口 iframe
        iframe_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'iframe.payment-verification')))
        browser_driver.switch_to.frame(iframe_element)

        # 打开 frens 页面 ，获取邀请奖励
        # button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/a[3]')))
        # button.click()
        #
        # time.sleep(10)
        #
        # # 点击 clamin 按钮
        # try:
        #     button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[1]/div/div[1]/div[2]/button')))
        #     button.click()
        # except Exception:
        #     pass

        # 打开 earn 页面
        button = long_wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/a[2]')))
        button.click()

        # 第一排任务
        # try:
        #     # 找到所有的任务项
        #     task_items = browser_driver.find_elements(By.CSS_SELECTOR,
        #                                               ".pages-tasks-list.is-card .pages-tasks-item.item")
        #
        #     # 遍历每个任务项，找到其中的按钮并点击
        #     for item in task_items:
        #         try:
        #             # 找到任务项中的按钮
        #             button = item.find_element(By.CSS_SELECTOR, '.tasks-pill-inline')
        #
        #             # 检查按钮中的文本是否是 "Start"
        #             if "Start" in button.text or "Claim" in button.text:
        #                 wait.until(EC.element_to_be_clickable(button)).click()
        #         except Exception:
        #             pass
        # except Exception:
        #     pass

        # 点击 weekly open 按钮
        # Find all task items by class name
        try:
            task_items = long_wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".pages-tasks-list.is-short-card .pages-tasks-item.item")
                )
            )
        except TimeoutException:
            # 处理超时逻辑（例如记录日志或抛出错误）
            print("等待30秒后仍未找到元素")

        try:
            for item in task_items:
                title = item.find_element(By.CLASS_NAME, "title").text
                # 获取分数显示元素
                points_element = item.find_element(By.CLASS_NAME, "points")
                points_text = points_element.text.split()[0]  # 提取 "450/450" 部分

                # 解析分数
                numerator, denominator = map(int, points_text.split('/'))

                if numerator != denominator and title != "Proof of Activity":
                    # Once the correct item is found, locate the button within it
                    button = item.find_element(By.CLASS_NAME, "tasks-pill-inline")

                    # Scroll to the button and click it
                    browser_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    button.click()

                    # 点击 "Start" 按钮
                    # print("开始点击 Start 按钮...")
                    was_clicked = click_visible_buttons(browser_driver,
                                                        ".tasks-pill-inline.is-status-not-started.is-dark.is-nested.pages-tasks-pill.pill-btn")

                    # 等待一段时间，确保任务处理完成
                    time.sleep(2)

                    # 被点击过才执行claim操作
                    if was_clicked:
                        clean_old_label(browser_driver)
                        browser_driver.switch_to.frame(iframe_element)

                    # 点击 "Claim" 按钮
                    # print("开始点击 Claim 按钮...")
                    click_visible_buttons(browser_driver,
                                          ".tasks-pill-inline.is-status-ready-for-claim.is-dark.is-nested.pages-tasks-pill.pill-btn")

                    time.sleep(2)

                    # 关闭页面
                    button = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, '.kit-button.is-medium.is-ghost.is-icon-only.close-btn')))
                    button.click()

                    # 等待页面加载完成
                    time.sleep(2)  # 可以根据页面加载速度调整等待时间
            home_task_click(browser_driver, iframe_element)
        except Exception as e:
            pass

        try:
            # 点击socilas
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="app"]/div[1]/div[2]/div[3]/div/div[1]/div[3]/div/label[2]')))
            browser_driver.execute_script("arguments[0].scrollIntoView();", button)
            time.sleep(0.5)  # 等待滚动完成
            button.click()
            # 等待页面加载完成
            time.sleep(2)  # 可以根据页面加载速度调整等待时间
            home_task_click(browser_driver, iframe_element)
        except Exception as e:
            pass

        try:
            # 点击socilas
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="app"]/div[1]/div[2]/div[3]/div/div[1]/div[3]/div/label[3]')))
            browser_driver.execute_script("arguments[0].scrollIntoView();", button)
            time.sleep(0.5)  # 等待滚动完成
            button.click()
            # 等待页面加载完成
            time.sleep(2)  # 可以根据页面加载速度调整等待时间
            home_task_click(browser_driver, iframe_element)
        except Exception as e:
            pass

        try:
            # 点击Acedemy
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="app"]/div[1]/div[2]/div[3]/div/div[1]/div[3]/div/label[4]')))
            browser_driver.execute_script("arguments[0].scrollIntoView();", button)
            time.sleep(0.5)  # 等待滚动完成
            button.click()
            # 等待页面加载完成
            time.sleep(2)  # 可以根据页面加载速度调整等待时间
            home_task_click(browser_driver, iframe_element)
        except Exception as e:
            pass

        try:
            # 点击 Blum bits
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="app"]/div[1]/div[2]/div[3]/div/div[1]/div[3]/div/label[5]')))
            browser_driver.execute_script("arguments[0].scrollIntoView();", button)
            time.sleep(0.5)  # 等待滚动完成
            button.click()
            # 等待页面加载完成
            time.sleep(2)  # 可以根据页面加载速度调整等待时间
            home_task_click(browser_driver, iframe_element)
        except Exception as e:
            pass

        try:
            # 点击Frens
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="app"]/div[1]/div[2]/div[3]/div/div[1]/div[3]/div/label[6]')))
            browser_driver.execute_script("arguments[0].scrollIntoView();", button)
            time.sleep(0.5)  # 等待滚动完成
            button.click()
            # 等待页面加载完成
            time.sleep(2)  # 可以根据页面加载速度调整等待时间
            home_task_click(browser_driver, iframe_element)
        except Exception as e:
            pass

        try:
            # 点击Farming
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="app"]/div[1]/div[2]/div[3]/div/div[1]/div[3]/div/label[7]')))
            browser_driver.execute_script("arguments[0].scrollIntoView();", button)
            time.sleep(0.5)  # 等待滚动完成
            button.click()
            # 等待页面加载完成
            time.sleep(2)  # 可以根据页面加载速度调整等待时间
            home_task_click(browser_driver, iframe_element)
        except Exception as e:
            pass


    except Exception as e:
        print(f"{seq}任务执行失败:")


def home_task_click(browser_driver, iframe_element):
    try:
        # 定位 "首页" 任务的 Start 按钮
        css_selector = ".tasks-pill-inline.is-status-not-started.is-dark.pages-tasks-pill.pill-btn"
        # 使用该方法点击 "Start" 按钮
        was_clicked = click_visible_buttons(browser_driver, css_selector)
        # 等待一段时间，确保任务处理完成
        time.sleep(2)
        if was_clicked:
            clean_old_label(browser_driver)
            browser_driver.switch_to.frame(iframe_element)
        # 点击verify
        verify_css_selector = ".tasks-pill-inline.is-status-ready-for-verify.is-dark.pages-tasks-pill.pill-btn"
        click_verify(browser_driver, verify_css_selector)
        #
        # # 使用该方法点击 "Claim" 按钮（示例代码）
        claim_css_selector = ".tasks-pill-inline.is-status-ready-for-claim.is-dark.pages-tasks-pill.pill-btn"
        click_visible_buttons(browser_driver, claim_css_selector)
    except Exception:
        pass


def click_verify(browser_driver, verify_css_selector, wait_time=2):
    buttons = browser_driver.find_elements(By.CSS_SELECTOR, verify_css_selector)

    for button in buttons:
        try:
            # 获取标题文本
            title_element = button.find_element(By.XPATH, "..//div[@class='title']")
            title_text = title_element.text

            # 检查标题是否在字典的键中
            if title_text in answers_dict:
                value_to_input = answers_dict[title_text]

                # 滚动并点击按钮
                browser_driver.execute_script("arguments[0].scrollIntoView();", button)
                time.sleep(0.5)

                if button.is_displayed() and button.is_enabled():
                    button.click()
                    time.sleep(wait_time)

                    # 新增：输入值并点击验证
                    if value_to_input != "N/A":
                        # 方案1：通过 placeholder 属性定位
                        input_box = WebDriverWait(browser_driver, 15).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, "input[placeholder='Keyword']")
                            )
                        )

                        # 清空并输入值
                        input_box.clear()
                        input_box.send_keys(value_to_input)

                        # 定位验证按钮
                        verify_button = WebDriverWait(browser_driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//button[contains(@class, 'kit-button') and .//div[text()='Verify']]"))
                        )

                        # 点击验证
                        verify_button.click()
                        time.sleep(wait_time)

            else:
                print(f"跳过未配置的标题: {title_text}")

        except Exception as e:
            continue


def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)


def run_create_threads():
    # 开启几个线程
    thread_num = 20

    # 浏览器编号执行到多少
    bit_num_start = 1
    bit_num_end = 400

    # 定义两个范围
    range1 = list(range(1, 301))
    range2 = list(range(2400, 3001))

    # 合并两个列表
    combined_range = range1 + range2

    error_list = [165]
    # error_list = range2
    error_list = None
    create_threads(thread_num, bit_num_start, bit_num_end, error_list)


forbidden_click = ["Trade any memecoin", "Launch a memecoin", "Share story", "Trade any token in Blum bot",
                   "Connect TON wallet"]

with open('./file/codes.json', 'r', encoding='utf-8') as file:
    answers_dict = json.load(file)  # 直接使用字典结构

if __name__ == '__main__':
    run_create_threads()
    # 使用 schedule 库设置每1min执行一次的定时任务
    schedule.every(1).minute.do(run_create_threads)

    # 创建一个单独的线程来运行 schedule 检查器
    schedule_thread = threading.Thread(target=schedule_checker)
    schedule_thread.daemon = True
    schedule_thread.start()

    # 主线程等待 schedule 线程
    schedule_thread.join()
