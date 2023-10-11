# Linkedin EasyApply Bot
Automate the application process on LinkedIn

Medium Write-up: https://medium.com/xplor8/how-to-apply-for-1-000-jobs-while-you-are-sleeping-da27edc3b703
Video: https://www.youtube.com/watch?v=4R4E304fEAs

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
phoneNumber: # Insert your phone number here

positions:
- # positions you want to search for
- # Another position you want to search for
- # A third position you want to search for

locations:
- # Location you want to search for
- # A second location you want to search in 

# --------- Optional Parameters -------
uploads:
 Resume: # PATH TO Resume 
 Cover Letter: # PATH TO cover letter
 Photo: # PATH TO photo
# Note file_key:file_paths contained inside the uploads section should be writted without a dash ('-') 

outputFilename: # PATH TO OUTPUT FILE (default output.csv)

blackListCompanies:
- # Company names you want to ignore

blackListTitles:
- # Add job titles you want to ignore

jobListFilterKeys:
- Most Recent # Most Recent | Most Relevant - Sort by
- Any Time # Any Time | Past Month | Past Week | Past 24 hours - Date posted
- Fast Apply # Fast Apply | Usual Apply - work only with fast apply or get the full job list
```
__NOTE: AFTER EDITING SAVE FILE, DO NOT COMMIT FILE__

### Uploads

There is no limit to the number of files you can list in the uploads section. 
The program takes the titles from the input boxes and tries to match them with 
list in the config file.

## Execute

To execute the bot with default config file run the following in your terminal
```
python3 easyapplybot.py
```
You can use the bot with a separate config.
- Create the ```private``` folder in the bot folder - this folder is excluded in .gitignore and more or less safe for your personal information
- Copy ```config.yaml``` to the ```private``` directory
- Make changes in copy
- Run the bot with
```
python3 easyapplybot.py --config private/config.yaml
```
### Additional parameters
```
options:
  -h, --help            show this help message and exit
  --config CONFIG       configuration file, YAML formatted (default:
                        config.yaml)
  --forcelogin          force login no matter cookies (default: False)
  --nobot               do all setup but not start the bot (default: False)
  --fastapply FASTAPPLY fast apply the job by id without the apply loop

```