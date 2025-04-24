from concurrent.futures import ThreadPoolExecutor

import numpy as np
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import time
import random
import bit_browser_request
import get_file
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
            error_num = execute_tasks(num, item, False)

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
def execute_tasks(seq, id, play_blum_game):
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
        driver.set_page_load_timeout(30)

        # 设置 JavaScript 执行超时为10秒
        driver.set_script_timeout(30)

        # blum任务
        play_blum(driver, play_blum_game, seq)

        # 切换回主内容
        # driver.switch_to.default_content()

        # dog 任务
        # play_doges(driver)

        # 清理旧标签(只保留一个标签，避免标签过多卡顿)
        clean_old_label(driver)

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


def play_doges(driver):
    # 打开新标签页
    driver.execute_script("window.open('https://web.telegram.org/k/#@dogshouse_bot', '_blank');")
    # 获取所有窗口句柄
    window_handles = driver.window_handles
    # 切换到新标签页
    driver.switch_to.window(window_handles[-1])
    # 等待页面加载
    wait = WebDriverWait(driver, 15)
    # 使用 CSS 选择器定位并点击按钮
    try:
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".new-message-bot-commands-view")))
        button.click()

        button_alert = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.popup-button.btn.primary.rp")))
        button_alert.click()
    except Exception as e:
        pass
    time.sleep(random.uniform(5, 10))


def play_blum(browser_driver, is_play_blum_game, seq):
    # 打开目标页面
    browser_driver.get("https://web.telegram.org/k/#@BlumCryptoBot")

    # 窗口自适应排列
    # try:
    #     bit_browser_request.windowbounds_flexable()
    # except Exception:
    #     logger.error("窗口自适应排列失败")

    # Random wait after clicking folders
    time.sleep(random.uniform(1, 3))
    wait = WebDriverWait(browser_driver, 30)

    # 防止点击 launch 弹出 start 面板
    try:
        # 点击 左下角 Launch Blum 按钮
        button_element = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'div.new-message-bot-commands.is-view')))
        button_element.click()
    except Exception:
        logger.error(f"An error open blum '{seq}'")
        raise  # 重新抛出异常，终止程序

    # Random wait after clicking button
    time.sleep(random.uniform(1, 3))

    # 防止点击 launch 弹出 start 面板
    try:
        # 通过CSS选择器点击按钮
        button_css_selector = "button.popup-button.btn.primary.rp"
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_css_selector)))
        button.click()
    except Exception:
        pass


    iframe_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'iframe.payment-verification')))

    #  iframe 切换到游戏窗口
    try:
        # Random wait after clicking button
        browser_driver.switch_to.frame(iframe_element)
    except Exception as e:
        logger.error(f"blum '{seq}' : iframe 切换到游戏窗口失败")
        pass

    wait = WebDriverWait(browser_driver, 5)

    # 领取每日登录奖励
    # try:
    #     button = wait.until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "button.kit-button.is-large.is-primary.is-fill.btn")))
    #     button.click()
    # except Exception:
    #     pass

    # 打开 frens 页面
    button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/a[4]')))
    button.click()

    # 等待 points 按钮出现并点击
    points_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Points']")))
    points_button.click()

    try:
        # 等待 Claim 按钮加载出来
        claim_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(@class, 'claim-pill')]//div[text()='Claim']/..")
        ))
        browser_driver.execute_script("arguments[0].scrollIntoView();", claim_button)
        time.sleep(1)  # 给动画或滚动时间
        claim_button.click()

    except Exception as e:
        print(f"blum '{seq}'找不到 Claim 按钮或点击失败:", e)

    # 出现彩蛋，需要关闭
    # try:
    #     button1 = wait.until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR,
    #                                     'img[src="https://telegram.blum.codes/_dist/hacked-modal.CTHjvak8.webp"][alt="Pokras hacked modal"]')))
    #     button1.click()
    #     button2 = wait.until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR,
    #                                     'img[src="https://telegram.blum.codes/_dist/welcome-modal.QsapntSs.webp"][alt="Pokras welcome modal"]')))
    #     button2.click()
    # except (NoSuchElementException, TimeoutException):
    #     pass

    # Random wait after clicking folders
    # time.sleep(1)

    # days check-in
    # try:
    #     long_wait = WebDriverWait(browser_driver, 60)
    #     check_in_button = long_wait.until(EC.element_to_be_clickable(
    #         (By.CSS_SELECTOR, 'button.kit-pill-claim.reset.is-state-claim.is-type-default.pill .label')))
    #     browser_driver.execute_script("arguments[0].scrollIntoView();", check_in_button)
    #     check_in_button.click()
    #     # button = long_wait.until(
    #     #     EC.element_to_be_clickable(
    #     #         (By.CSS_SELECTOR, 'button.kit-pill-claim.reset.is-state-claim.is-type-default.pill .label')))
    #     # button.click()
    # except Exception:
    #     pass

    # time.sleep(1)

    # try:
    #     # 点击Blum points claim
    #     check_in_button = wait.until(EC.element_to_be_clickable(
    #         (By.CSS_SELECTOR,  'div.pages-wallet-asset-farming-slot button.kit-pill-claim .label')))
    #     browser_driver.execute_script("arguments[0].scrollIntoView();", check_in_button)
    #     check_in_button.click()
    #
    #
    #     # button = wait.until(
    #     #     EC.element_to_be_clickable(
    #     #         (By.CSS_SELECTOR, 'div.pages-wallet-asset-farming-slot button.kit-pill-claim .label')))
    #     # button.click()
    # except Exception:
    #     pass

    # try:
    #     # 点击Blum points farm
    #     check_in_button = wait.until(EC.element_to_be_clickable(
    #         (By.CSS_SELECTOR, 'button.kit-pill-claim.reset.is-state-claim.is-type-dark .label')))
    #     browser_driver.execute_script("arguments[0].scrollIntoView();", check_in_button)
    #     check_in_button.click()
    #
    #     # button = wait.until(
    #     #     EC.element_to_be_clickable(
    #     #         (By.CSS_SELECTOR, 'button.kit-pill-claim.reset.is-state-claim.is-type-dark .label')))
    #     # button.click()
    # except Exception:
    #     pass

    # Random wait after clicking folders
    time.sleep(5)

    if is_play_blum_game:
        # 是否玩游戏
        play_blum_game(browser_driver, wait, seq)


def play_blum_game(driver, wait, seq):
    try:
        balance_element = driver.find_element(By.CSS_SELECTOR, "div.content > div.balance")

        # 判断文本内容是否为 "0 Play passes"
        if balance_element.text != "0 Play passes":
            logger.info("不是 0 play")
            # Click Play button in iframe
            play_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button.kit-pill.reset.is-type-white.pill .label')))
            # 滚动到元素位置
            driver.execute_script("arguments[0].scrollIntoView();", play_button)
            play_button.click()

            # Loop to click the 'Play' button if it exists
            sum = 0
            long_wait = WebDriverWait(driver, 100)
            while True:
                try:
                    play_button = long_wait.until(EC.element_to_be_clickable(
                        (By.XPATH, '//button[contains(@class, "kit-button") and contains(.//span, "Play")]')))
                    driver.execute_script("arguments[0].scrollIntoView();", play_button)
                    play_button.click()
                    sum = sum + 1
                    # Random wait after clicking play button
                except (NoSuchElementException, TimeoutException):
                    logger.warning(f"blum '{seq}' : 点击结束")
                    break
            logger.info(f"blum '{seq}' completed the game '{sum}' times")

    except Exception:
        logger.warning(f"blum '{seq}' : 已经完成所有任务")


def clean_old_label(driver):
    try:
        # 打开一个初始页面并存储其句柄
        # driver.get("https://web.telegram.org/k")
        initial_handle = driver.current_window_handle

        # time.sleep(3)
        # 打开一个新的标签页
        # driver.execute_script("window.open('https://web.telegram.org/k', '_blank');")

        time.sleep(3)

        # 获取所有窗口句柄
        window_handles = driver.window_handles

        time.sleep(3)

        # 关闭除初始页面之外的所有标签页
        for handle in window_handles:
            if handle != initial_handle:
                driver.switch_to.window(handle)
                driver.close()
                time.sleep(1)

        time.sleep(2)
        # 切换回初始页面
        driver.switch_to.window(initial_handle)
    except Exception:
        pass


if __name__ == '__main__':
    # 开启几个线程
    thread_num = 25

    # 浏览器编号执行到多少
    bit_num_start = 1
    bit_num_end = 300

    error_list = None
    create_threads(thread_num, bit_num_start, bit_num_end, error_list)
