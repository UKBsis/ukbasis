"""
This script compares the output of:
* the reports downloaded from https://hub.oaswitchboard.org/dashboard/messages
* the reports downloaded by using the API
* the messages downloaded by using the API
"""

import json
import os

import pandas as pd


def get_file(start: str, extension: str):
    all_files = os.listdir("data")
    out = [x for x in all_files if x.startswith(start)]
    out = [x for x in out if x.endswith(extension)]
    if len(out) != 1:
        print("no file found")
    print("Filename: {}".format(out[0]))
    return out[0]


print("=============== Start comparing excel ===============")

# read the excel UI report
print("reading ui excel")
df_ui_excel = pd.read_excel(os.path.join("data", get_file("ui", "xlsx")))

# read the excel API report
print("reading api excel")
df_api_excel = pd.read_excel(os.path.join("data", get_file("report", "xlsx")))

# compare excel
if df_ui_excel.equals(df_api_excel):
    print("The excel from the UI exactly equals the excel from the API")
else:
    print("Unexpected difference!")


print("=============== Start comparing json ===============")

# read the json UI report
with open(os.path.join("data", get_file("ui", "json")), 'r', encoding='utf-8') as f:
    dict_ui_json = json.load(f)

# read the json API report
with open(os.path.join("data", get_file("report", "json")), 'r', encoding='utf-8') as f:
    dict_api_json = json.load(f)

# compare json
if dict_ui_json == dict_api_json:
    print("The json from the UI exactly equals the json from the API")
else:
    print("Unexpected difference!")


print("=============== Start comparing report and messages ===============")

# read the messages
with open(os.path.join("data", get_file("messages", "json")), 'r', encoding='utf-8') as f:
    dict_messages_json = json.load(f)

# read the json API report
with open(os.path.join("data", get_file("report", "json")), 'r', encoding='utf-8') as f:
    dict_report_json = json.load(f)

# compare messages and report
print("Number of items in report: {}".format(len(dict_report_json)))
print("Number of items in messages: {}".format(len(dict_messages_json)))
df_messages = pd.json_normalize(dict_messages_json)
df_report = pd.json_normalize(dict_report_json)

common_columns = df_messages.columns.intersection(df_report.columns)
print("Extra columns in report: {}".format(df_report.columns.difference(df_messages.columns)))
print("Extra columns in messages: {}".format(df_messages.columns.difference(df_report.columns)))


difference = df_messages[common_columns].head(1000).compare(
    df_report[common_columns],
    result_names=("message", "report")
)
# The DOI and DOI url seem to have moved to another place at some point
# The license differs at points

# Version number seems to be always 'v2'. This is however missing in some items of 'report'
print("missing header.version in report: {}".format(df_report["header.version"].isna().sum()))
print("missing header.version in messages: {}".format(df_messages["header.version"].isna().sum()))

print("There are 43 'data.article.vor.license' that are labeled 'non-CC BY' in report and 'non-CC' in message")
print(pd.crosstab(difference[('data.article.vor.license', 'message')], difference[('data.article.vor.license', 'report')]))

print("In the report the 'data.article.vor.publication' is sometimes preceded by 'open access'")
print(pd.crosstab(difference[('data.article.vor.publication', 'message')], difference[('data.article.vor.publication', 'report')]).to_string())

print("There is one difference in 'data.charges.charged'")
print(difference['data.charges.charged'].dropna(how="all"))

print("The DOI is sometimes converted to an url")
print(difference['data.article.doi'].dropna(how="all"))
print(difference['data.article.doiurl'].dropna(how="all"))


print("finished!")