import re


def extract_error_numbers(filename):
    """
    从给定的文件中提取所有错误信息中的数字，并返回一个包含这些数字的数组。

    :param filename: 包含错误信息的文件名
    :return: 包含所有提取到的数字的数组
    """
    # 定义用于匹配错误信息中的数字的正则表达式
    error_pattern = re.compile(r"An error occurred in blum '(\d+)'")

    error_numbers = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                match = error_pattern.search(line)
                if match:
                    # 提取匹配的数字并将其转换为整数
                    number = int(match.group(1))
                    error_numbers.append(number)
    except UnicodeDecodeError:
        print("文件编码错误，请检查文件的编码格式。")

    return error_numbers


# 使用示例
filename = 'file/error_list.txt'
error_numbers = extract_error_numbers(filename)
print(error_numbers)
