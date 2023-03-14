ukbasis
==============================

Using the OAswitchboard api to download the reports. This work is based upon the repository by Frederico Rubini: https://github.com/frubini/ukbasis

The project can be cloned from Github as follows:
```commandline
git clone https://github.com/ukbsis/ukbasis
```

The repository uses `pipenv` for environment creation and package version management. 
The environment can be created from **within the project directory** as follows:
```commandline
pip install pipenv
pipenv install
```

Copy the contents of `config.example.py` to `config.py` and provide the proper
email and password details in this file. Subsequently, the reports can be downloaded by
running `main.py` in the `oa-switchboard` folder.

Note that one may need to run `main.py` several times to get a successful response. The first attempts may result in 500 or 502 http errors.

## Notes on API documentation

The host of the API must start with `https` and equals  'https://api.oaswitchboard.org/v2'

### Authentication

The authentication happens through the endpoint `POST /authorize` with a json payload of 
`{"email": "bla@foo.com", "password": "very_secret"}`. The API returns a token in the body.

The token must be supplied in the header as 
```
'Content-Type': 'application/json',
'Authorization': 'Bearer <token>'
```
for all other endpoints.

### Report

A report can be requested through the endpoint `POST /report`. One can set a parameter as report=json|excel. 
The payload can consist of: `{"state": "None", "pio": "False"}`. These are not mandatory.

### Messages

The messages can be obtained through the endpoint `GET /messages`. One must add the parameter
`startrow=<integer>`. Other parameters are optional and consist of maxrows, searchq, orderby and orderdir.
The maximum number of rows returned seems to be 50.

