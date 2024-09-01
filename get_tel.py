import pandas as pd

# 读取 Excel 文件

class ExcelDataReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data_dict = {}
        self._load_data()

    def _load_data(self):
        """读取 Excel 文件并加载数据到字典中。"""
        df = pd.read_excel(self.file_path)

        # 遍历数据并保存到字典
        for index, row in df.iterrows():
            serial_number = row['序号']
            account = row['账号']
            link = row['链接']
            self.data_dict[serial_number] = {'账号': account, '链接': link}

    def get_data_by_serial_number(self, serial_number):
        """根据序号获取对应的账号和链接。"""
        if serial_number in self.data_dict:
            return self.data_dict[serial_number]
        else:
            print("序号不存在！")
            return None


if __name__ == '__main__':
    # 使用示例
    file_path = '/Users/lilinhai/Documents/电报账号.xlsx'  # 替换为你的 Excel 文件路径
    reader = ExcelDataReader()

    # 获取序号为1的数据
    result = reader.get_data_by_serial_number(300)
    if result:
        print(f"账号: {result['账号']}, 链接: {result['链接']}")