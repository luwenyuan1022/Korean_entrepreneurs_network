from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['crawlers']
collection = db['korea_ent_info']

all_ = collection.find({})
origin_name_set = set()


def multi_form_insert(item: str):
    if item:
        if ',' in item:
            sub_list = item.split(',')
            for i in sub_list:
                origin_name_set.add(i.strip())
        else:
            origin_name_set.add(item.strip())


def insert_if_exist(item: dict, key: str):
    if key in item and item[key]:
        multi_form_insert(item[key])


if __name__ == '__main__':
    for i in all_:
        insert_if_exist(i, '사장/대표')
        insert_if_exist(i, '중역')
    with open('origin_name.txt', 'w', encoding='utf-8') as f:
        for i in origin_name_set:
            f.write(i)
            f.write('\n')
