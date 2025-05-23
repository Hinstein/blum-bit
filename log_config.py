import logging


def setup_logger(name, log_file, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果日志记录器已有处理器，直接返回（避免重复添加）
    if logger.handlers:
        return logger

    # 创建文件处理器（仅处理 ERROR 及以上级别）
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.ERROR)

    # 创建控制台处理器（根据参数 level 设置级别）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
