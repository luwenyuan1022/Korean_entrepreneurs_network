from pymongo import MongoClient
import pandas as pd
import os
from tqdm import tqdm


def main():
    try:
        # 连接 MongoDB 数据库
        client = MongoClient('mongodb://localhost:27017/')
        db = client['crawlers']
        collection = db['newspaper_query_through_keywords']

        # 批次大小
        batch_size = 100000
        batch_number = 0

        # 获取当前脚本的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        res_dir = os.path.join(script_dir, 'res')

        # 如果 res 目录不存在，创建它
        if not os.path.exists(res_dir):
            os.makedirs(res_dir)

        # 显示进度条
        with tqdm(total=collection.count_documents({}), desc="Writing batches") as pbar:
            while True:
                # 从 MongoDB 中读取数据，每次读取 batch_size 条
                data = list(collection.find().skip(batch_number * batch_size).limit(batch_size))

                if not data:
                    break

                # 将数据转换为 DataFrame
                df = pd.DataFrame(data)

                # 将 DataFrame 存储为 xlsx 文件，存储在 res 目录中
                file_path = os.path.join(res_dir, f'batch_{batch_number + 1}.xlsx')
                df.to_excel(file_path, index=False)

                batch_number += 1
                pbar.update(len(data))
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == '__main__':
    main()