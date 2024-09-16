import random
from threading import Thread, Event

import numpy as np
import time

import bit_browser_request
import get_file

from bit_blume import execute_tasks
from kill_bit import terminate_processes
from log_config import setup_logger
from concurrent.futures import ThreadPoolExecutor

logger = setup_logger('blum_auto', 'blum_auto.log')


class TimeoutError(Exception):
    pass


def conditional_timeout(seconds, enable_timeout):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if enable_timeout:
                result = [None]
                exception = [None]
                event = Event()

                def target():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e
                    finally:
                        event.set()

                thread = Thread(target=target)
                thread.start()
                event.wait(timeout=seconds)
                if thread.is_alive():
                    thread.join(0)  # Clean up the thread if still alive
                    raise TimeoutError("Function call timed out")
                if exception[0]:
                    raise exception[0]
                return result[0]
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


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


def print_numbers(numbers, thread_name, shuffled_dict, play_blum_game, task_timeout=90):
    """
    打印给定的数字列表，并根据 play_blum_game 设置超时机制

    :param numbers: 数字列表
    :param thread_name: 线程名称
    :param shuffled_dict: 字典，数字与任务相关联
    :param play_blum_game: 游戏标志或其他相关参数
    :param task_timeout: 每个任务的超时时间（秒）
    """
    error = []

    # 使用装饰器来决定是否启用超时
    @conditional_timeout(task_timeout, not play_blum_game)
    def task_function(num, item):
        return execute_tasks(num, item, play_blum_game)

    for num in numbers:
        error_num = None
        try:
            item = shuffled_dict.get(num)
            logger.info(f'{thread_name} 开始 {num} 任务 {item}')

            try:
                task_function(num, item)
                logger.info(f'{thread_name} 结束 {num} 任务 {item}')
            except TimeoutError:
                logger.warning(f'{thread_name} 执行 {num} 任务超时 {item}')
            except Exception as e:
                logger.error(f'{thread_name} 执行 {num} 任务报错 {item}，错误信息: {e}')
            finally:
                terminate_processes(bit_browser_request.get_browser_pids(item))

        except Exception as e:
            logger.error(f'{thread_name} 执行 {num} 任务报错 {item}，错误信息: {e}')

        if error_num is not None:
            error.append(error_num)

    # for error_no in error:
    #     try:
    #         item = get_item_by_index(shuffled_dict, error_no)
    #         logger.info(f'{thread_name} 重试 {error_no} 任务 {item}')
    #         execute_tasks(error_no, item, play_blum_game)
    #     except Exception as e:
    #         logger.error(f'{thread_name} 重试 {error_no} 任务错误')


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


def create_threads(n, bit_num_start, bit_num_end, play_blum_game):
    """
    创建 n 个线程，并平分随机顺序的数字给这些线程打印

    :param play_blum_game:
    :param n: 线程数量
    :param total: 总数字数量，默认值为 100
    """
    numbers = generate_random_sequence(bit_num_start, bit_num_end + 1)

    selected_values = get_file.get_id_by_seq(numbers)

    logger.info("Original Dictionary:", selected_values)
    result = np.array_split(numbers, n)
    list_result = [subarray.tolist() for subarray in result]

    # 使用 ThreadPoolExecutor 进行多线程处理
    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = []
        for i in range(n):
            thread_name = f'Thread-{i + 1}'
            future = executor.submit(print_numbers, list_result[i], thread_name, selected_values, play_blum_game)
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
    thread_num = 4
    # 浏览器编号执行到多少
    bit_num_start = 1
    bit_num_end = 500
    # blum玩游戏
    # play_blum_game = True
    # blum不玩游戏
    play_blum_game = False

    create_threads(thread_num, bit_num_start, bit_num_end, play_blum_game)
