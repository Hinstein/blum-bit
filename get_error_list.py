import re
from collections import Counter, defaultdict


def extract_error_numbers(filename):
    """
    从给定的文件中提取所有错误信息中的数字，并返回一个包含这些数字的数组。

    :param filename: 包含错误信息的文件名
    :return: 包含所有提取到的数字的数组
    """
    error_pattern = re.compile(r"An error occurred in blum '(\d+)'")

    error_numbers = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                match = error_pattern.search(line)
                if match:
                    number = int(match.group(1))
                    error_numbers.append(number)
    except UnicodeDecodeError:
        print("文件编码错误，请检查文件的编码格式。")

    return error_numbers


def group_errors_by_frequency(error_numbers):
    """
    根据出现次数对错误号码进行分组，并对组内的序号按大小排序。

    :param error_numbers: 包含所有提取到的错误号码的数组
    :return: 一个字典，其中键是失败的次数，值是一个列表，包含所有出现该次数的错误号码，且该列表按序号大小排序
    """
    # 使用 Counter 统计每个错误号码的出现次数
    error_counts = Counter(error_numbers)

    # 创建一个默认字典，用于将错误号码按出现次数进行分组
    grouped_errors = defaultdict(list)

    for number, count in error_counts.items():
        grouped_errors[count].append(number)

    # 对每个失败次数的列表内的错误号码进行排序
    for count in grouped_errors:
        grouped_errors[count].sort()

    # 将结果转换为普通字典并按失败次数（键）降序排序
    grouped_errors = dict(sorted(grouped_errors.items(), key=lambda x: x[0], reverse=True))

    return grouped_errors


# 使用示例
filename = 'file/error_list.txt'
error_numbers = extract_error_numbers(filename)
grouped_errors = group_errors_by_frequency(error_numbers)

print(grouped_errors)