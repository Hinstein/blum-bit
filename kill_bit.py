import os
import signal

def terminate_processes(pids):
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)  # 或者使用 signal.SIGKILL 直接强制终止
            print(f"进程 {pid} 已成功终止")
        except ProcessLookupError:
            print(f"没有找到 PID 为 {pid} 的进程")
        except PermissionError:
            print(f"权限不足，无法终止进程 {pid}")

if __name__ == '__main__':
    # 示例：调用方法并传入 PID 列表
    pid_list = [24564]  # 将此替换为目标进程的 PID 列表
    terminate_processes(pid_list)

