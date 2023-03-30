import re
import requests
import logging
import json
import time
import os
import json_to_csv
import config
import shutil
from urllib.parse import urlparse
from datetime import date, datetime
import sys
from dateutil.rrule import rrule, MONTHLY

"""
API Documentation https://bitbucket.org/oaswitchboard/api/src/master/

INFO on decoding the AWS JWT: https://stackoverflow.com/questions/55703156/aws-cognito-how-to-decode-jwt-in-python

"""

"""
Logging
"""
logfile = config.LOGFILE_DIR + date.today().strftime('%Y-%m-%d_') + config.LOGFILE_SUFFIX
log_format = "%(asctime)s - %(levelname)-8s - %(name)s | %(message)s"
logging.basicConfig(filename=logfile, filemode='a', format=log_format, level=config.LOG_LEVEL)
logger = logging.getLogger('OAS_API')

consoleHandler = logging.StreamHandler(sys.stdout)
logFormatter = logging.Formatter(log_format)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


def _token_write(token):
    os.makedirs(os.path.dirname(config.TOKEN_PATH), exist_ok=True)
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

    logger.info("Performing Auth request")

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
OA Switchboard API Methods
"""


def get_schema():
    """
    Retrieves messages schema (e1, e2, p1 and p2)
    :return:
    """
    res = requests.get(config.API_URL + '/schema/e1', headers=_get_headers())
    print(res.json())


def post_report(report_type='excel', start_date=None, end_date=None):
    """
    Get a report in excel or json format
    :param end_date:
    :param start_date:
    :param report_type: excel or json
    :return: downloaded file name
    """

    # _authorize()

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
    }

    if start_date and end_date:
        r = re.compile('[\d]{4}-[\d]{2}-[\d]{2}')
        if r.match(start_date) is None or r.match(end_date) is None:
            logger.error("Start date or end date are not valid")
            raise TypeError("Start date or end date are not valid")

        payload["from"] = start_date
        payload["to"] = end_date

    report_file = ''
    report_type = 'json' if report_type == 'json' else 'excel'
    res = requests.post(config.API_URL + '/report?type=' + report_type, headers=headers, data=json.dumps(payload))

    logger.info("Starting /report request fo type %s" % report_type)

    if res.status_code == 200:

        # Streamed content
        if 'content-disposition' in res.headers:
            logger.debug('Downloading file from content-disposition')

            report_file = _get_report_file(
                res.headers['content-disposition'].split('filename=', 1)[1],
                payload
            )

            with open(report_file, 'wb') as fd:
                for chunk in res.iter_content(chunk_size=256):
                    fd.write(chunk)

        # download url
        elif res.content:
            logger.debug('Downloading file from content URL')
            u = urlparse(res.content)

            report_file = _get_report_file(
                u.path.decode('utf-8').split('/')[-1],
                payload
            )

            with requests.get(res.content, stream=True) as report_data:
                with open(report_file, 'wb') as out_file:
                    # out_file.write(report_data.content)
                    shutil.copyfileobj(report_data.raw, out_file)
        else:
            logger.error('No data in the response')
            exit()

        logger.info('Downloaded report to %s' % report_file)

        if report_type == 'json':
            logger.info('Converting json file to CSV')
            csv_report_file = json_to_csv.convert_2(report_file)
            logger.info('File converted: %s' % csv_report_file)



    else:
        logger.error('Response error: %s - %s' % (res.status_code, res.reason))
        logger.error('Info: %s' % (res.json()))


def _get_report_file(filename, payload):
    """
    Generate report filename
    :param filename:
    :param payload:
    :return:
    """
    if "from" in payload:
        name_parts = filename.split('.')
        filename = ("%s_%s_%s.%s" % (name_parts[0], payload['from'], payload['to'], name_parts[1]))

    return os.path.join(config.OUTPUT_FOLDER, filename)


def get_more_reports(report_type, start_month, end_month):
    """
    Get more reports in batches of one month
    :param report_type:
    :param start_month:
    :param end_month:
    :return:
    """
    logger.info('## START MONTHLY PROCESSING from %s until %s', start_month, end_month)

    start_date = datetime.fromisoformat(start_month)
    end_date = datetime.fromisoformat(end_month)

    start_itr = start_date
    for end_itr in rrule(freq=MONTHLY, dtstart=start_date, until=end_date)[1:]:
        logger.info('Processing messages from: %s until: %s ' % (start_itr.strftime('%Y-%m-%d'), end_itr.strftime('%Y-%m-%d')))

        post_report(
            report_type=report_type,
            start_date=start_itr.strftime('%Y-%m-%d'),
            end_date=end_itr.strftime('%Y-%m-%d')
        )
        # change start iteration date to the current end iteration date
        start_itr = end_itr


def get_messages():
    """

    :return:
    """
    # _authorize()
    res = requests.get(config.API_URL + '/messages?startrow=1&maxrows=1', headers=_get_headers())
    # res = requests.get(config.API_URL + '/messages', headers=_get_headers())
    print(json.dumps(res.json(), indent=2))


if __name__ == "__main__":
    _authorize()
    time.sleep(5)

    # get_schema()
    # get_messages()

    post_report('json')

    """
    Get report on In batches of one Month per file
    use date format: YYYY-MM-DD
    """
    # get_more_reports(report_type='json', start_month='2021-11-01', end_month='2022-03-01')
