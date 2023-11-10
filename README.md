# Linkedin EasyApply Bot - major fork and improvements

[![Paypal donate button](https://raw.githubusercontent.com/conradRz/readAloudSubtitlesFirefoxExtension---Chrome-Edge-Opera-browser-version/main/readmePics/PayPal-Donate-Button.png)](https://www.paypal.com/donate/?hosted_button_id=2QH26ZA928JNC)

^^^^^^^^^^^^^^^^

#### Major fork and improvements (increased speed and reliability - ability to persist through unhandled exceptions, for example caused by internet disconnection), as the owner of the original repo seem to had abandoned the project. 
#### To practice and showcase skill useful for automated testing/data scrapping/python/Selenium and save time

Automate the application process on LinkedIn. Your profile on LinkedIn should have an already saved CV, and a mobile number (this "saving" of such data is handled by the LinkedIn itself).

The CV should be [Applicant tracking system - Wikipedia](https://en.wikipedia.org/wiki/Applicant_tracking_system) friendly.
It might be the case, that I'll take it private at a certain point, so don't take availability of this for granted.

Best to just add it to a task scheduler/Cron(on Linux), for every other day, except Sundays - as new Jobs are not posted on Sundays.

## Setup

Best to [Venv it](https://docs.python.org/3/library/venv.html), especially if you're also using other Python scripts.

Install requirements:

```bash
pip3 install -r requirements.txt
```

Enter your username, password, and search settings into the `config.yaml` file

```yaml
username: # Insert your username here
password: # Insert your password here

positions:
  -  # positions you want to search for
  -  # Another position you want to search for

locations:
  -  # Location you want to search for
  -  # A second location you want to search in

output_filename:
  -  # PATH TO OUTPUT FILE (default output.csv), preferably don't change the output file, leave it as is.

blacklist:
  -  # Company names you want to ignore
```

**NOTE: AFTER EDITING SAVE THE FILE, DO NOT COMMIT FILE**
I have found loads of credentials posted on GitHub lol, it's out there if you know what/how to search for.

## Execute

```
exception_resistant_easyapplybot.bat
```
also it will work well inside the VSCode debugger.