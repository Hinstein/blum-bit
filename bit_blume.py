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


# Function to execute tasks for each profile
def execute_tasks(seq, id, play_blum_game):
    global driver
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

        # blum任务
        play_blum(driver, play_blum_game, seq)

        # 切换回主内容
        driver.switch_to.default_content()

        # dog 任务
        # play_doges(driver)

        # 清理旧标签(只保留一个标签，避免标签过多卡顿)
        clean_old_label(driver)

        time.sleep(3)
        # Close the browser session
        bit_browser_request.close_browser(id)
        time.sleep(3)
        driver.quit()


    except Exception as e:
        logger.error(f"An error occurred in blum '{seq}'")
        # Close the browser session if an error occurs
        driver.quit()
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
    bit_browser_request.windowbounds_flexable()

    # Random wait after clicking folders
    time.sleep(random.uniform(1, 3))
    wait = WebDriverWait(browser_driver, 10)

    # Click another element
    button_element = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'button.is-web-view.reply-markup-button.rp')))
    button_element.click()

    # Random wait after clicking button
    time.sleep(random.uniform(1, 3))

    # 防止弹出小launch跳板
    try:
        # 通过CSS选择器点击按钮
        button_css_selector = "button.popup-button.btn.primary.rp"
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_css_selector)))
        button.click()
    except (NoSuchElementException, TimeoutException):
        pass

    # Find and switch to iframe
    iframe_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'iframe.payment-verification')))
    browser_driver.switch_to.frame(iframe_element)

    # 领取每日登录奖励
    try:
        button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.kit-button.is-large.is-primary.is-fill.btn")))
        button.click()
    except (NoSuchElementException, TimeoutException):
        pass

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

    # 领取每日奖励
    try:
        # 点击clam
        button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.kit-button.is-large.is-drop.is-fill.button.is-done")))
        button.click()

        # Random wait after clicking folders
        time.sleep(random.uniform(1, 3))

        # 点击start farming
        button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.kit-button.is-large.is-primary.is-fill.button")))
        button.click()
    except (NoSuchElementException, TimeoutException):
        pass
    # Random wait after clicking folders
    time.sleep(random.uniform(1, 3))

    if is_play_blum_game:
        # 是否玩游戏
        play_blum_game(browser_driver, wait, seq)


def play_blum_game(driver, wait, seq):
    try:
        # Click Play button in iframe
        play_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//a[contains(@class, "play-btn") and contains(text(), "Play")]')))
        # 滚动到元素位置
        driver.execute_script("arguments[0].scrollIntoView();", play_button)
        play_button.click()

        # Loop to click the 'Play' button if it exists
        sum = 0
        long_wait = WebDriverWait(driver, 80)
        while True:
            try:
                play_button = long_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//button[contains(@class, "kit-button") and contains(.//span, "Play")]')))
                play_button.click()
                sum = sum + 1
                # Random wait after clicking play button
            except (NoSuchElementException, TimeoutException):
                logger.warning(f"blum '{seq}' : 点击结束")
                break
        logger.info(f"blum '{seq}' completed the game '{sum}' times")

    except (NoSuchElementException, TimeoutException):
        logger.warning(f"blum '{seq}' : 已经完成所有任务")


def clean_old_label(driver):
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
    # driver.switch_to.window(initial_handle)


if __name__ == '__main__':
    # select = list(range(1, 41))
    select = [17]
    selected_values = get_file.get_id_by_seq(select)
    # Iterate through each profile directory
    for key in selected_values:
        seq = {key}
        id = selected_values[key]
        logger.info(f"Executing tasks for blum '{key}'...")
        execute_tasks(key, id, True)

    logger.info("All tasks completed successfully.")
