import psutil

from log_config import setup_logger

logger = setup_logger('kill_thread', 'blum_auto.log')

def terminate_processes(pids):
    for pid in pids:
        try:
            process = psutil.Process(pid)
            process.terminate()
            logger.info(f"进程 {pid} 已成功终止")
        except psutil.NoSuchProcess:
            logger.info(f"没有找到 PID 为 {pid} 的进程")
        except psutil.AccessDenied:
            logger.info(f"权限不足，无法终止进程 {pid}")
        except Exception as e:
            logger.error(f"终止进程 {pid} 时发生错误: {str(e)}")

if __name__ == '__main__':
    # 示例：调用方法并传入 PID 列表
    pid_list = [22824]  # 将此替换为目标进程的 PID 列表
    terminate_processes(pid_list)