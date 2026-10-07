# Linkedin EasyApply Bot
Automate the application process on LinkedIn

Write-up: https://substack.com/@nicolomantini/posts - How to apply for 1,000 jobs while sleeping

Video: https://www.youtube.com/watch?v=4R4E304fEAs

## **Website & Autofill Extension**

[![Apply to jobs in seconds with Zapply.](apply-faster-banner.png)](https://app.zapply.jobs/onboarding?ref=github-cta-nicolomantini)

Explore Zapply’s website and check out:

- Our Chrome extension, which autofills job applications in seconds.
- A dedicated job board featuring the latest openings across various roles.
- User accounts with multiple profiles for different resume types and roles.
- Job application tracking with streaks and commitment awards.

Experience an advanced career journey with us! 🚀

<p align="center">
    <a href="https://app.zapply.jobs/onboarding?ref=github-cta-nicolomantini">
        <img src="get-started-button.png" alt="Visit Zapply" width="700">
    </a>
</p>

<p align="right"><sub>Sponsored by Zapply</sub></p>

## Setup 

Python 3.10 using a conda virtual environment on Linux (Ubuntu)

The run the bot install requirements
```bash
pip3 install -r requirements.txt
```

Enter your username, password, and search settings into the `config.yaml` file

```yaml
username: # Insert your username here
password: # Insert your password here
phone_number: #Insert your phone number

positions:
- # positions you want to search for
- # Another position you want to search for
- # A third position you want to search for

locations:
- # Location you want to search for
- # A second location you want to search in 

salary: #yearly salary requirement 
rate: #hourly rate requirement 

uploads:
 Resume: # PATH TO Resume 
 Cover Letter: # PATH TO cover letter
 Photo: # PATH TO photo
# Note file_key:file_paths contained inside the uploads section should be written without a dash ('-') 

output_filename:
- # PATH TO OUTPUT FILE (default output.csv)

blacklist:
- # Company names you want to ignore
```
__NOTE: AFTER EDITING SAVE FILE, DO NOT COMMIT FILE__

### Uploads

There is no limit to the number of files you can list in the uploads section. 
The program takes the titles from the input boxes and tries to match them with 
list in the config file.

## Execute

To execute the bot run the following in your terminal
```
python3 easyapplybot.py
```



