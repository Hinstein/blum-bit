from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import time
import random

from log_config import setup_logger

logger = setup_logger('main', 'blum_auto.log')

# List of profile directories to iterate through
# Creates a list from "Profile 1" to "Profile 20"
# profile_directories = [f"Profile {i}" for i in range(1, 32)]

profile_directories = [f"Profile {i}" for i in range(18, 19)]

# Common Chrome options setup
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(r'--user-data-dir=D:\03 文档\chrome')
# chrome_options.add_argument('headless')

# Using local ChromeDriver
service = Service('chromedriver-win64/chromedriver.exe')


# Function to execute tasks for each profile
def execute_tasks(profile_directory, play_game):
    try:
        # Set profile directory argument
        chrome_options.add_argument(f"--profile-directory={profile_directory}")

        # Initialize Chrome browser
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 120)

        # Random wait before starting tasks
        time.sleep(random.uniform(1, 3))

        # Navigate to Telegram web
        # driver.get("https://web.telegram.org/k/")
        #
        # # Random wait after navigation
        # time.sleep(random.uniform(5, 10))
        #
        # # Click folders element
        # folder_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="folders-container"]/div/div[2]/ul/a[2]')))
        # folder_element.click()

        driver.get("https://web.telegram.org/k/#@BlumCryptoBot")

        # Random wait after clicking folders
        time.sleep(random.uniform(5, 10))
        wait = WebDriverWait(driver, 20)

        # Click another element
        button_element = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button.is-web-view.reply-markup-button.rp')))
        button_element.click()

        # Random wait after clicking button
        time.sleep(random.uniform(5, 10))

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
        driver.switch_to.frame(iframe_element)

        # 领取每日登录奖励
        try:
            button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.kit-button.is-large.is-primary.is-fill.btn")))
            button.click()
        except (NoSuchElementException, TimeoutException):
            pass

        # 出现彩蛋，需要关闭
        try:
            button1 = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                                            'img[src="https://telegram.blum.codes/_dist/hacked-modal.CTHjvak8.webp"][alt="Pokras hacked modal"]')))
            button1.click()
            button2 = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                                            'img[src="https://telegram.blum.codes/_dist/welcome-modal.QsapntSs.webp"][alt="Pokras welcome modal"]')))
            button2.click()
        except (NoSuchElementException, TimeoutException):
            pass

        # 领取每日奖励
        try:
            # 点击clam
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.kit-button.is-large.is-drop.is-fill.button.is-done")))
            button.click()

            # Random wait after clicking folders
            time.sleep(random.uniform(5, 10))

            # 点击start farming
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.kit-button.is-large.is-primary.is-fill.button")))
            button.click()
        except (NoSuchElementException, TimeoutException):
            pass

        # Random wait after clicking folders
        time.sleep(random.uniform(5, 10))

        if play_game:
            # 点击最初的play按钮
            try:
                # Click Play button in iframe
                play_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.play-btn')))
                # 滚动到元素位置
                driver.execute_script("arguments[0].scrollIntoView();", play_button)
                # driver.execute_script("arguments[0].scrollIntoView();", driver.find_element_by_css_selector("a.play-btn"))
                play_button.click()

                # Loop to click the 'Play' button if it exists
                sum = 0
                long_wait = WebDriverWait(driver, 120)
                while True:
                    try:
                        play_button = long_wait.until(EC.element_to_be_clickable(
                            (By.XPATH, '//button[contains(@class, "kit-button") and contains(.//span, "Play")]')))
                        play_button.click()
                        sum = sum + 1
                        # Random wait after clicking play button
                    except (NoSuchElementException, TimeoutException):
                        logger.warning(f"blum '{profile_directory}' : 点击结束")
                        break
                logger.info(f"blum '{profile_directory}' completed the game '{sum}' times")

            except (NoSuchElementException, TimeoutException):
                logger.warning(f"blum '{profile_directory}' : 已经完成所有任务")

        # 切换回主内容
        driver.switch_to.default_content()
        # 打开新标签页
        driver.execute_script("window.open('https://web.telegram.org/k/#@dogshouse_bot', '_blank');")
        # 获取所有窗口句柄
        window_handles = driver.window_handles
        # 切换到新标签页
        driver.switch_to.window(window_handles[-1])
        # 等待页面加载
        wait = WebDriverWait(driver, 20)
        # 使用 CSS 选择器定位并点击按钮
        try:
            button_alert = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.popup-button.btn.primary.rp")))
            button_alert.click()
            button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.new-message-bot-commands.is-view")))
            button.click()
            print("Button clicked successfully.")
        except Exception as e:
            pass

        time.sleep(random.uniform(5, 10))

        # Close the browser session
        driver.quit()

    except Exception as e:
        logger.error(f"An error occurred in blum '{profile_directory}'")
        # Close the browser session if an error occurs
        driver.quit()


def main(play_game):
    # Iterate through each profile directory
    for profile in profile_directories:
        print(f"Executing tasks for profile '{profile}'...")
        execute_tasks(profile, play_game)
        # Random wait after clicking button
        # time.sleep(random.uniform(300, 600))
        print(f"Tasks completed for profile '{profile}'. Moving to next profile.")

    print("All tasks completed successfully.")


if __name__ == "__main__":
    main(True)
