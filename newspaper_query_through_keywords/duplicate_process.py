import json
import re

final_name_list_json = {}


def get_real_name(origin_name: str):
    return re.sub(r'[（(].*?[）)]', "", origin_name)


if __name__ == '__main__':
    with open('origin_name.txt', 'r', encoding='utf-8') as f:
        with open('newspaper_query_through_keywords/spiders/final_name_json.txt', 'w', encoding='utf-8') as f2:
            readlines = f.readlines()
            for i in readlines:
                line = i.replace('\n', '')
                if line:
                    real_name = get_real_name(line)
                    if real_name in final_name_list_json:
                        final_name_list_json[real_name].append(line)
                    else:
                        final_name_list_json[real_name] = [line]

            for j in final_name_list_json:
                f2.write(json.dumps({j:final_name_list_json[j]},ensure_ascii=False)+ '\n')
