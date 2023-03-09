import os
import tempfile

# suffix of the logfile
LOGFILE_SUFFIX = 'harvest.log'
# directory to store log files !! the directory should exist !!
LOGFILE_DIR = ''
# log levels : DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'DEBUG'

API_URL = 'https://api.oaswitchboard.org/v2'

OUTPUT_FOLDER = './output'

OAS_EMAIL = ""
OAS_PASSWORD = ""

TOKEN_PATH = os.path.join(
    tempfile.gettempdir(),
    'ukb',
    'oas.token',
)

# TOKEN_PATH = './auth.token'

