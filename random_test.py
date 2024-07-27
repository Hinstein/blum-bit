import numpy as np

# 创建一个数组
arr = np.array(range(1, 16))

# 将数组分割成3个子数组
result = np.array_split(arr, 3)

# 转换成列表形式
list_result = [subarray.tolist() for subarray in result]

print(list_result)
print(list_result[0])