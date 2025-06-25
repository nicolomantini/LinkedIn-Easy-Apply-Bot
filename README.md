# Linkedin EasyApply Bot
Automate the application process on LinkedIn

Write-up: https://www.nicolomantini.com/p/how-to-apply-for-jobs-while-you-are-sleeping
Video: https://www.youtube.com/watch?v=4R4E304fEAs

## Setup 

Python 3.10 using a conda virtual environment on Linux (Ubuntu)

The run the bot install requirements
```bash
pip3 install -r requirements.txt
```

Enter your username, password, and search settings into the `config.yaml` file

```yaml
username: Pradyumna
password: pradyumna@079
phone_number: +18573967207

positions:
- Software Engineer
- Software Developer
- Web Developer

locations:
- California
- United States

salary: #yearly salary requirement 
rate: #hourly rate requirement 

uploads:
 Resume: /Users/pradyumna/Documents/Full_Stack_resume_with_3_yrs/Pradyumna_Nunna_Resume.pdf
 Cover Letter: # PATH TO cover letter
 Photo: # PATH TO photo
# Note file_key:file_paths contained inside the uploads section should be written without a dash ('-') 

output_filename:
- /Users/pradyumna/Documents/Projects/LinkedIn-Easy-Apply-Bot/out.csv

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


Issues:
1) getting stuck on load page. loading same page again and again instead of going to next page
2) stops for "continue application" after clicking "easy apply" for a job
3) Fill current location as job locationi
4) Adding answers even if answer is already present

Commands:
1) python -m venv .venv - creates venv if not present
2) source .venv/bin/activate - to activate the venv
3) python3 easyapplybot.py - to run the application (in the venv)


