def read_data_from_file(file_path):
    data_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            if ' : ' in line:
                key, value = line.strip().split(' : ')
                data_dict[int(key)] = value
    return data_dict


def get_id_by_seq(keys):
    data_dict = read_data_from_file(file_path)
    return {key: data_dict[key] for key in keys if key in data_dict}


# 文件路径
file_path = 'bit.txt'

# 读取文件数据
data_dict = read_data_from_file(file_path)

# 用户选择（使用从1到20的数组表示）
choices = list(range(1, 21))

# 获取相应的值
selected_values = get_id_by_seq(choices)

# for key in selected_values:
#     print(f"{key}: {selected_values[key]}")
