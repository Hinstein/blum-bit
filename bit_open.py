from selenium import webdriver
from selenium.webdriver.chrome.service import Service

import time
import bit_browser_request
import get_file
from kill_bit import terminate_processes
from log_config import setup_logger

logger = setup_logger('bit_blum', 'blum_auto.log')


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
    # select = list(range(1, 41))
    select = [1494]
    selected_values = get_file.get_id_by_seq(select)
    # Iterate through each profile directory
    for key in selected_values:
        seq = {key}
        id = selected_values[key]
        logger.info(f"Executing tasks for blum '{key}'...")
        execute_tasks(key, id)
    try:
        bit_browser_request.windowbounds_flexable()
    except Exception:
        logger.error("窗口自适应排列失败")

    logger.info("All tasks completed successfully.")
