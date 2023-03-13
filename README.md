ukbasis
==============================

Using the OAswitchboard api to download the reports

The project can be cloned from Github as follows:
```commandline
git clone https://github.com/frubini/ukbasis
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