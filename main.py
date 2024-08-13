from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time

from bit_blume import play_blum, play_doges, clean_old_label
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
def execute_tasks(profile_directory, play_blum_game):
    try:
        # Set profile directory argument
        chrome_options.add_argument(f"--profile-directory={profile_directory}")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Initialize Chrome browser
        # 设置页面加载超时为10秒
        driver.set_page_load_timeout(10)

        # 设置 JavaScript 执行超时为10秒
        driver.set_script_timeout(10)

        # blum任务
        play_blum(driver, play_blum_game)

        # 切换回主内容
        driver.switch_to.default_content()

        # dog 任务
        play_doges(driver)

        # 清理旧标签(只保留一个标签，避免标签过多卡顿)
        clean_old_label(driver)

        time.sleep(1)

    except Exception as e:
        logger.error(f"An error occurred in blum error:{e}")

    finally:
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
