from pathlib import Path
import json
import pandas as pd
import csv
import os

"""
Json Conversions Methods
"""


def convert():
    filename = 'report_messages_20230208-1259.json'
    p = Path(filename)
    with p.open('r', encoding='utf-8') as f:
        data = json.loads(f.read())
    df = pd.json_normalize(data)
    df.to_csv('report_messages_20230208-1259-json.csv')


def convert_2(filename):

    def flatten_json(b, delim):
        """
        Flatten nested json values
        :param b:
        :param delim:
        :return:
        """
        val = {}
        for i in b.keys():
            if isinstance(b[i], dict):
                get = flatten_json(b[i], delim)
                for j in get.keys():
                    val[i + delim + j] = get[j]
            else:
                val[i] = b[i]
        return val

    p = Path(filename)
    with p.open('r', encoding='utf-8') as f:
        data = json.loads(f.read())

    first_obj = data[1]
    # flat_obj = map(lambda x: flatten_json( x, "_" ), first_obj)
    flat_obj = flatten_json(first_obj, "_")
    columns = [x for x in flat_obj.keys()]
    # columns = list(set(columns))
    type(columns)

    # the whole oject
    flat_data = map(lambda x: flatten_json(x, "_"), data)

    output_file_name = filename + '.csv'

    with open(output_file_name, 'w', encoding='utf-8') as out_file:
        csv_w = csv.writer(out_file)
        csv_w.writerow(columns)

        for i_r in flat_data:
            csv_w.writerow(map(lambda x: i_r.get(x, ""), columns))

    return output_file_name
