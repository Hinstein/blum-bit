import requests
import json
import time

from log_config import setup_logger

logger = setup_logger('bit_request', 'blum_auto.log')

url = "http://127.0.0.1:54345"
headers = {'Content-Type': 'application/json'}


def open_browser(id):  # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
    json_data = {"id": f'{id}'}
    res = requests.post(f"{url}/browser/open",
                        data=json.dumps(json_data), headers=headers).json()
    print(res)
    print(res['data']['http'])
    return res


def close_browser(id):  # 关闭窗口
    json_data = {"id": f'{id}'}
    res = requests.post(f"{url}/browser/close",
                        data=json.dumps(json_data), headers=headers).json()
    time.sleep(2)
    return res


def get_browser_pids(browser_id):  # 关闭窗口
    json_data = {
        "ids": [
            f'{browser_id}'
        ]
    }
    res = requests.post(f"{url}/browser/pids/alive",
                        data=json.dumps(json_data), headers=headers).json()
    time.sleep(3)
    # 提取 data 中的值
    if 'data' in res and res['data']:
        error_treads = list(res['data'].values())
        return error_treads
    else:
        return []


def browser_list(page_num):
    json_data = {
        "page": page_num,
        "pageSize": 200
    }
    res = requests.post(f"{url}/browser/list",
                        data=json.dumps(json_data), headers=headers).json()
    # print(res)
    return res


def windowbounds_flexable():
    json_data = {
        "page": 0,
        "pageSize": 200
    }
    res = requests.post(f"{url}/windowbounds/flexable",
                        data=json.dumps(json_data), headers=headers).json()
    # print(res)
    return res


def send_post_request(id):
    # print('请求开始')

    data = {
        "id": id,
        "args": [],
        "loadExtensions": True
    }

    response = requests.post(f"{url}/browser/open", json=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        # print('请求成功')
        # print('返回的内容：', response.json())
        driver_path = response_data['data']['driver']  # 提取'driver'字段的值
        # print('驱动路径：', driver_path)
    else:
        print('请求失败，状态码：', response.status_code)

    return response.json()


if __name__ == '__main__':
    # 总页数
    page = 10
    for i in range(29, -1, -1):
        ori_data = browser_list(i)
        datajson = ori_data['data']['list']

        # 指定要筛选的字段
        fieldnames = ['id', 'seq']

        # 循环遍历每个字典，筛选出指定字段的键值对，构造新的字典，并更新metamask数据
        # 按seq排序
        sorted_datajson = sorted(datajson, key=lambda x: x['seq'])

        # 遍历排序后的列表并输出
        for item in sorted_datajson:
            filtered_item = {key: item[key] for key in fieldnames}
            id = filtered_item['id']
            seq = filtered_item['seq']
            print(seq, ":", id)
