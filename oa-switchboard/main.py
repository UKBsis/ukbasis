import requests
import logging
import json
import pandas as pd
from pathlib import Path
import os
import tempfile
import csv
import config

"""
API Documentation https://bitbucket.org/oaswitchboard/api/src/master/

INFO on decoding the AWS JWT: https://stackoverflow.com/questions/55703156/aws-cognito-how-to-decode-jwt-in-python

"""

logging.basicConfig(level=config.LOG_LEVEL)


def _token_write(token):
    with open(config.TOKEN_PATH, 'w') as outfile:
        outfile.write(token)


def _token_read():
    with open(config.TOKEN_PATH, 'r') as infile:
        return infile.read()


def _authorize():
    """
    Authorises user and returns either a 401 or a 200 with a JWT token
    that should be used with all following requests.
    :return:
    """
    token = None
    # Define the payload (data to send in the request)
    payload = {
        "email": config.OAS_EMAIL,
        "password": config.OAS_PASSWORD
    }

    # Make a POST request to the API
    response = requests.post(config.API_URL + '/authorize', json=payload)

    # Print the status code of the response
    # print(response.status_code)
    r_body = response.json()

    # Print the JSON content of the response
    # print(response.headers)
    # print(response.json())
    _token_write(r_body['token'])


def _get_headers():
    token = _token_read()
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }


"""
Json Conversions Methods
"""


def json_to_csv():
    filename = 'report_messages_20230208-1259.json'
    p = Path(filename)
    with p.open('r', encoding='utf-8') as f:
        data = json.loads(f.read())
    df = pd.json_normalize(data)
    df.to_csv('report_messages_20230208-1259-json.csv')


def json_to_csv_2():
    def flatten_json(b, delim):
        val = {}
        for i in b.keys():
            if isinstance(b[i], dict):
                get = flatten_json(b[i], delim)
                for j in get.keys():
                    val[i + delim + j] = get[j]
            else:
                val[i] = b[i]
        return val

    filename = 'report_messages_20230208-1259.json'
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

    file_name = 'report_messages_20230208-1259-json.csv'

    with open(file_name, 'w') as out_file:
        csv_w = csv.writer(out_file)
        csv_w.writerow(columns)

        for i_r in flat_data:
            csv_w.writerow(map(lambda x: i_r.get(x, ""), columns))


"""
OA Switchboard API Methods
"""


def get_schema():
    """
    Retrieves messages schema (e1, e2, p1 and p2)
    :return:
    """
    res = requests.get(config.API_URL + '/schema/e1', headers=_get_headers())
    print(res.json())


def post_report(report_type='excel'):
    """
    Get a report in excel or json format
    :param report_type: excel or json
    :return:
    """

    _authorize()

    token = _token_read()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Connection': 'keep-alive',
        # 'Accept-Encoding': 'gzip, deflate, br',
        # 'Accept-Language': 'en-US,en;q=0.5',
        # 'TE': 'trailers'
    }

    payload = {
        "state": None,
        "pio": False,
        "from": '2022-01-01',
        "to": '2023-02-01'
    }

    report_type = 'json' if report_type == 'json' else 'excel'
    res = requests.post(config.API_URL + '/report?type=' + report_type, headers=headers, data=json.dumps(payload))

    if res.status_code == 200:
        if 'content-disposition' in res.headers:
            filename = res.headers['content-disposition'].split('filename=', 1)[1]
            report_file = os.path.join(config.OUTPUT_FOLDER, filename)
            with open(report_file, 'wb') as fd:
                for chunk in res.iter_content(chunk_size=256):
                    fd.write(chunk)

        else:
            print('No data in the response')

    else:
        print(res.json())
        print(res.status_code)
        print(res.reason)


def get_messages():
    _authorize()
    res = requests.get(config.API_URL + '/messages?startrow=1&maxrows=1', headers=_get_headers())
    # res = requests.get(config.API_URL + '/messages', headers=_get_headers())
    print(json.dumps(res.json(), indent=2))


if __name__ == "__main__":
    # _authorize()
    # get_schema()
    # get_messages()
    post_report()
    # json_to_csv_2()
