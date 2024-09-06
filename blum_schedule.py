# 定时任务模式
import threading
import time
import schedule

import main
from blum_main import create_threads
from log_config import setup_logger

logger = setup_logger('main', 'blum_auto.log')


# n是线程个数， total是你要完成到哪个浏览器
def run_create_threads():
    logger.info("定时任务开始")

    # 开启几个线程
    thread_num = 15
    # 浏览器编号执行到多少
    bit_num_start = 1
    bit_num_end = 500
    # blum玩游戏
    play_blum_game = True
    # blum不玩游戏
    # play_blum_game = False

    logger.info("开始执行bit浏览器任务")
    create_threads(thread_num, bit_num_start, bit_num_end, play_blum_game)

    logger.info("开始执行本地chrome")
    # 使用多进程异步执行 main.main(play_blum_game)
    # process = Process(target=main.main, args=(play_blum_game,))
    # process.start()
    main.main(play_blum_game)


run_create_threads()
# 使用 schedule 库设置每3小时执行一次的定时任务
schedule.every(1).hours.do(run_create_threads)


def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)


# 创建一个单独的线程来运行 schedule 检查器
schedule_thread = threading.Thread(target=schedule_checker)
schedule_thread.daemon = True
schedule_thread.start()

# 主线程等待 schedule 线程
schedule_thread.join()
