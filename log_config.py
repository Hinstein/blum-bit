import logging


def setup_logger(name, log_file, level=logging.DEBUG):
    """
    配置并返回一个日志记录器

    :param name: 日志记录器名称
    :param log_file: 日志文件路径
    :param level: 日志记录级别
    :return: 配置好的日志记录器
    """
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(level)  # 设置日志级别

    # 创建一个文件处理器，写入日志到文件，并指定编码为 UTF-8
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.ERROR)

    # 创建一个控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 创建格式器并将其添加到处理器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 将处理器添加到日志器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
