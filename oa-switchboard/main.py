import requests
import logging
import json
import time
import os
import json_to_csv
import config
import shutil
from urllib.parse import urlparse
from datetime import date
import sys

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


def post_report(report_type='excel'):
    """
    Get a report in excel or json format
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
        # "state": None,
        # "pio": False,
        # "from": '2023-01-01',
        # "to": '2023-03-01'
    }

    report_file = ''
    report_type = 'json' if report_type == 'json' else 'excel'
    res = requests.post(config.API_URL + '/report?type=' + report_type, headers=headers, data=json.dumps(payload))

    logger.info("Starting /report request of type %s" % report_type)

    if res.status_code == 200:
        # Streamed content
        if 'content-disposition' in res.headers:
            logger.debug('Downloading file from content-disposition')
            filename = res.headers['content-disposition'].split('filename=', 1)[1]
            report_file = os.path.join(config.OUTPUT_FOLDER, filename)
            with open(report_file, 'wb') as fd:
                for chunk in res.iter_content(chunk_size=256):
                    fd.write(chunk)
        # download url
        elif res.content:
            logger.debug('Downloading file from content URL')
            u = urlparse(res.content)
            filename = u.path.decode('utf-8').split('/')[-1]
            report_file = os.path.join(config.OUTPUT_FOLDER, filename)

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


def get_messages(startrow: int = 1, maxrows: int = 50):
    """
    Gets the messages in batches. It starts at row 'startrow' and retrieves 'maxrows' messages.
    :param startrow: integer on which row to start
    :param maxrows: integer with the number of messages to retrieve. Maximum number of messages in one go is 50
    :return: dictionary with results
    """

    # authorize first
    _authorize()

    # request the messages
    res = requests.get(
        config.API_URL + '/messages?startrow={}&maxrows={}'.format(startrow, maxrows),
        headers=_get_headers()
    )
    # TODO: pretty catching of error such as done in get_report
    # TODO: write to logger
    # print("Total number of messages in database {}".format(res.json()["total"]))
    # print("Number of messages {}".format(len(res.json()["messages"])))
    # print("ID's: {}".format(", ".join([str(x["id"]) for x in res.json()["messages"]])))
    # print(json.dumps(res.json(), indent=2))
    return res.json()


def get_all_messages():
    """
    Returns all messages by retrieving them in batches
    :return: None
    """

    # get first row only
    first_item = get_messages(startrow=1, maxrows=1)

    # find out how many messages there are
    total_number_of_messages = first_item["total"]
    logger.info("Starting retrieving all {} messages".format(total_number_of_messages))

    # get other batches in a loop and combine
    out = list()
    for start_row in range(1, total_number_of_messages, 50):

        # retrieve the messages in a batch of 50
        batch = get_messages(startrow=start_row, maxrows=50)["messages"]

        # extend the list
        out = out + batch

    # save in json file
    filename = "messages_{}.json".format(time.strftime("%Y%m%d-%H%M"))
    messages_file = os.path.join(config.OUTPUT_FOLDER, filename)
    with open(messages_file, "w") as outfile:
        json.dump(out, outfile)

    logger.info('Downloaded messages to %s' % messages_file)


if __name__ == "__main__":
    _authorize()
    # time.sleep(5)
    # get_schema()
    get_all_messages()
    # report_file = post_report('excel')
