import random
import threading
import time

import numpy as np

import get_file
from bit_blume import execute_tasks
from log_config import setup_logger

logger = setup_logger('blum_auto', 'blum_auto.log')


def get_item_by_index(items, index):
    """
    通过索引获取键值对

    :param items: 键值对列表
    :param index: 索引
    :return: 键值对
    """
    if 0 <= index < len(items):
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


def print_numbers(numbers, thread_name, shuffled_dict, play_blum_game):
    """
    打印给定的数字列表

    :param numbers: 数字列表
    :param thread_name: 线程名称
    """
    error = []

    for num in numbers:
        try:
            item = get_item_by_index(shuffled_dict, num)
            logger.info(f'{thread_name} 开始 {num} 任务 {item}')
            error_num = execute_tasks(num, item, play_blum_game)
            logger.info(f'{thread_name} 结束 {num} 任务 :id:{item}')
        except Exception as e:
            logger.error(f'{thread_name} 执行 {num} 任务报错 {item}')
        if (error_num != None):
            error.append(error_num)

    for error_no in error:
        try:
            item = get_item_by_index(shuffled_dict, error_no)
            logger.info(f'{thread_name} 重试 {error_no} 任务 {item}')
            execute_tasks(error_no, item, play_blum_game)
        except Exception as e:
            logger.error(f'{thread_name} 重试 {error_no} 任务错误')


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


def create_threads(n, total, play_blum_game):
    """
    创建 n 个线程，并平分随机顺序的数字给这些线程打印

    :param play_blum_game:
    :param n: 线程数量
    :param total: 总数字数量，默认值为 100
    """
    numbers = generate_random_sequence(1, total)

    select = list(range(1, total + 1))
    selected_values = get_file.get_id_by_seq(select)

    logger.info("Original Dictionary:", selected_values)
    step = total // n
    threads = []
    result = np.array_split(numbers, n)
    # 转换成列表形式
    list_result = [subarray.tolist() for subarray in result]

    for i in range(n):
        thread_name = f'Thread-{i + 1}'
        thread = threading.Thread(target=print_numbers,
                                  args=(list_result[i], thread_name, selected_values, play_blum_game))
        threads.append(thread)
        thread.start()
        # 删除等待60秒后再启动下一个线程的代码
        time.sleep(5)

    for thread in threads:
        thread.join()


# 不使用定时任务，单独运行
# n是线程个数， total是你要完成到哪个浏览器
if __name__ == '__main__':
    # 开启几个线程
    thread_num = 3
    # 浏览器编号执行到多少
    bit_num = 91
    # blum玩游戏
    # play_blum_game = True
    # blum不玩游戏
    play_blum_game = False

    create_threads(thread_num, bit_num, play_blum_game)
