# coding=utf-8

from __future__ import annotations
import time, random, os, csv
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import winsound
from selenium.webdriver.chrome.service import Service
import re
import yaml
from datetime import date, datetime, timedelta
from selenium.webdriver.common.action_chains import ActionChains
import subprocess
from os import path


log = logging.getLogger(__name__)

service = Service(executable_path = path.dirname(__file__) + r"\assets\chromedriver.exe")
driver = webdriver.Chrome(service=service) # if you do just 
# driver = webdriver.Chrome() 
# you will sometimes get the below, this might be because they don't keep on top of things

# Exception has occurred: NoSuchDriverException
# Message: Unable to obtain chromedriver using Selenium Manager; Message: Unsuccessful command executed: C:\Users\User\AppData\Local\Programs\Python\Python39\lib\site-packages\selenium\webdriver\common\windows\selenium-manager.exe --browser chrome --output json.
# The chromedriver version cannot be discovered
# ; For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors/driver_location

num_successful_jobs_global_variable = 0


def setupLogger() -> None:
    dt: str = datetime.strftime(datetime.now(), 
                                "%m_%d_%Y %H_%M_%S ")

    if not os.path.isdir('./logs'):
        os.mkdir('./logs')

    # TODO need to check if there is a log dir available or not
    logging.basicConfig(filename=('./logs/' + str(dt) + 'applyJobs.log'), 
                        filemode='w',
                        format='%(asctime)s::%(name)s::%(levelname)s::%(message)s', 
                        datefmt='./logs/%d-%b-%Y %H:%M:%S')
    log.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)

def get_process_id(process_name):
  """Gets the PID of a process by its name.

  Args:
    process_name: The name of the process to get the PID of.

  Returns:
    The PID of the process, or None if the process could not be found.
  """

  # Get all running processes.
  processes = subprocess.check_output(["wmic", "process", "get", "processid,commandline"]).decode("utf-8").splitlines()

  # Find the process with the given name.
  for process in processes:
    if process_name in process:
        #Use regular expression to find the number
        result = re.search(r'\b\d+\b', process)
        return int(result.group())

  # If the process could not be found, return None.
  return None

process_id = get_process_id("automated-LinkedIn-applying\\run_script.bat")

def terminate_process(process_id):
  """Terminates a process by its PID.

  Args:
    process_id: The PID of the process to terminate.
  """
  subprocess.check_call(["taskkill", "/F", "/T", "/PID", str(process_id)])

class EasyApplyBot:
    setupLogger()
    # MAX_SEARCH_TIME is 10 hours by default, feel free to modify it
    MAX_SEARCH_TIME = 10 * 60 * 60
    # LinkedIn limits how many you can apply to per day. After that it doesn't allow one to click the easy apply button
    MAX_ALLOWED_POSITIONS_TO_APPLY_TO_PER_DAY = 249

    def __init__(self,
                 username,
                 password,
                 filename='output.csv',
                 blacklist=[],
                 blackListTitles=[]) -> None:

        log.info("Welcome to Easy Apply Bot")
        dirpath: str = os.getcwd()
        log.info("current directory is : " + dirpath)

        past_ids: set | None = self.get_appliedIDs(filename)
        self.appliedJobIDs: set = past_ids if past_ids != None else {}
        self.filename: str = filename
        self.options = self.browser_options()
        self.browser = driver
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(username, password)

    def get_appliedIDs(self, filename) -> set | None:
        try:
            df = pd.read_csv(filename,
                             header=None,
                             names=['timestamp', 
                                    'jobID', 
                                    'job', 
                                    'company', 
                                    'attempted', 
                                    'result'],
                             lineterminator=None,
                             encoding='Windows-1252')

            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%d/%m/%Y %H:%M")
            df = df[df['timestamp'] > (datetime.now() - timedelta(days=14))]

            today = date.today()
            jobs_today = df[df['timestamp'].dt.date == today] 

            global num_successful_jobs_global_variable 
            num_successful_jobs_global_variable = len(jobs_today[jobs_today['result'] == True])

            #the limit seem to be 249 succesfully applied to jobs in 24hours, after that, Linkedin doesn't let you click the button. Add code check to do nothing once the daily limit is reached
            #then add the script to daily autostart, to apply till it reaches its daily limit
            if num_successful_jobs_global_variable > 249:
                log.debug("You have applied to more than 249 jobs today. Exiting the app...")
                # Get the PID of the process with "cmd.exe" and "easyapplybot.py" in its name.
                if process_id is not None:
                    terminate_process(process_id)
                    exit() #just incase if running from the VSC
                else:
                    exit() #just incase if running from the VSC

            # converting to set removes duplicates, and they're faster than lists for purpose of this program
            jobIDs = set(df.jobID)
            log.info(f"{len(jobIDs)} jobIDs found after filtration and removal of duplicates")

            return jobIDs
        except Exception as e:
            log.info(str(e) + "   jobIDs could not be loaded from CSV {}".format(filename))
            return None

    def browser_options(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")

        # disables “Chrome is being controlled by automated software” infobar, which is anoying as it takes away from useful space
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # Disable webdriver flags or you will be easily detectable
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        return options

    def start_linkedin(self, username, password) -> None:
        log.info("Logging in.....Please wait :)  ")
        self.load_page_and_wait_until_it_stops_loading("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            user_field = self.browser.find_element("id","username")
            pw_field = self.browser.find_element("id","password")
            login_button = self.browser.find_element("xpath",
                        '//*[@id="organic-div"]/form/div[3]/button')
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(3)
        except TimeoutException:
            log.info("TimeoutException! Username/password field or login button not found")

    def fill_data(self) -> None:
        self.browser.set_window_size(1, 1)
        # self.browser.set_window_position(2000, 2000)
        self.browser.set_window_position(1, 1) #breaking up here
        self.browser.maximize_window() #breaking up here, do it earlier and once

    def start_apply(self, positions, locations) -> None:
        if "verification" in self.browser.title.lower():
            winsound.PlaySound("C:\Windows\Media\chimes.wav", winsound.SND_FILENAME)
            input("Press Enter to continue...") # pause the script in case of captcha type verification
            log.debug("captcha verification needed")
        # TODO: only have the above activated, if the title mean its a captcha verification
        start: float = time.time()
        self.fill_data()

        # Define the CSV file name
        csv_combo_log_file = 'combos_output_log.csv'

        df = pd.read_csv(csv_combo_log_file, names=['Date', 'Combo'])

        # Convert the 'Date' column to datetime objects
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M')

        # Get the current date and time
        current_datetime = datetime.now()

        # Calculate the timestamp 24 hours ago from the current date and time
        twenty_four_hours_ago = current_datetime - timedelta(hours=24)

        # Filter rows based on timestamp within the last 24 hours
        filtered_df = df[df['Date'] > twenty_four_hours_ago]

        # Extract the 'Combo' values into a list of tuples
        combos_within_last_24_hours = list(filtered_df['Combo'])
        combos_within_last_24_hours = [tuple(eval(combo)) for combo in combos_within_last_24_hours]

        # Now convert the list of tuples to a tuple
        combos_within_last_24_hours = tuple(combos_within_last_24_hours)
        
        combos: list = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)
            if combo not in combos:
                combos.append(combo)
                if combo not in combos_within_last_24_hours:
                    # log.debug(f"Combos already applied to: {combos}")
                    log.debug(f"Number of job/location combos already applied to: {len(combos)}")
                    log.debug(f"All possible job/location combos given the config.yaml file: {len(positions) * len(locations)}")
                    log.debug(f"Remaining job/location combos to apply to: {(len(positions) * len(locations))-len(combos)}")
                    log.info(f"Applying to {position}: {location}")
                    location = "&location=" + location
                    self.applications_loop(position, location)

                # Open the CSV file in append mode with the specified encoding and line terminator
                with open(csv_combo_log_file, 
                          mode='a', 
                          encoding='Windows-1252', 
                          newline=None) as file:
                    writer = csv.writer(file)

                    # Get the current date and time in the desired format
                    current_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')

                    # Log the combo along with the current date and time to the CSV file
                    writer.writerow([current_datetime, combo])
            # if len(combos) > 500:
            #     break

    def applications_loop(self, position, location):

        count_application = 0
        count_job = 0
        jobs_per_page = 0
        start_time: float = time.time()

        # self.browser.set_window_position(1, 1) #breaking up here
        # self.browser.maximize_window() #breaking up here, do it earlier and once
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page)
        log.info("Looking for jobs.. Please wait..")

        while time.time() - start_time < self.MAX_SEARCH_TIME:
            try:
                log.info(f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search")

                # sleep to make sure everything loads, add random to make us look human.
                randoTime: float = random.uniform(3.5, 4.9)
                log.debug(f"Sleeping for {round(randoTime, 1)}")
                time.sleep(randoTime)

                #self.load_page(sleep=1) #commented out just now, potentially useless, at least useless on first iteration

                # LinkedIn displays the search results in a scrollable <div> on the left side, we have to scroll to its bottom

                # scrollresults = self.browser.find_element(By.CLASS_NAME,
                #     "jobs-search-results-list"
                # )
                # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
                # for i in range(300, 3000, 100):
                #     self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults)

                # exit this combo if the page contains "No matching jobs found." as it will have some jobs listed, but those are "Jobs you may be interested in" which are not very relevant location wise
                if "No matching jobs found" in self.browser.page_source:
                    log.debug("No matching jobs found. Moving onto next job/location combo")
                    break

                # get job links, (the following are actually the job card objects)
                links = self.browser.find_elements("xpath",
                                                   '//div[@data-job-id and .//text()[contains(., "Easy Apply")]]'
                )

                if len(links) == 0:
                    log.debug("No links found")
                    break
                else: # we have some links, but some of them are over 1 week old, then skip this job/location combo, and move to the next one # TODO: would be to add this to config.yaml as an option
                    first_link = links[0]
                    if any(phrase in first_link.text for phrase in ["week ago", 
                                                                    "6 days ago", 
                                                                    "5 days ago", 
                                                                    "4 days ago", 
                                                                    "3 days ago", 
                                                                    # "2 days ago", 
                                                                    "weeks ago",  
                                                                    "month ago", 
                                                                    "months ago"]):
                        log.debug("moving onto the next combo, due to no new jobs available to apply to for this combo")
                        break # this skips this job/location combo
                    else:
                        last_link = links[-1].text # don't put this further down, as you will then get StaleElementReferenceException(). Also don't do last_link = links[-1] as that would be reference assignment only, and not hold a copy

                IDs = []
                
                # children selector is the container of the job cards on the left
                for link in links:
                    if (not any(phrase.lower() in link.text.lower() for phrase in self.blacklist + self.blackListTitles)):
                        temp = link.get_attribute("data-job-id")
                        jobID = temp.split(":")[-1]
                        IDs.append(int(jobID))

                    # children = link.find_elements("xpath",
                    #     '//ul[@class="scaffold-layout__list-container"]'
                    # )
                    # for child in children:
                        #self.blacklist looks like this: ['Version 1', 'energy gym', 'Wood Mackenzie']

                        #child.text looks like this: 'Project Manager - HR System Implementation\nDigital Gurus\nCambridge, England, United Kingdom (Remote)\n£70/hr - £80/hr\nActively recruiting\nApplied 3 days ago\nSenior Service Delivery Specialist PMS (Hotel IT) - UK & Ireland\nHRS Hospitality & Retail Systems\nUnited Kingdom (Remote)\n1 school alum works here\nPromoted\nEasy Apply\nCX Project Manager - Compliance\nNtrinsic Consulting\nUnited Kingdom (Remote)\n£45/hr - £51/hr\nActively recruiting\nApplied 3 days ago\nIT Change Manager (SFIA / ITIL)\nPeople Source Consulting\nUnited Kingdom (Remote)\n£60/hr - £80/hr\n2 school alumni work here\nApplied 3 days ago\nSenior ERP Project/Delivery Manager - Remote Working - New!\nRedRock Consulting\nBirmingham, England, United Kingdom (Remote)\n£60K/yr - £70K/yr\nActively recruiting\nPromoted\nEasy Apply\nTechnical Project Manager (Must speak French and English)\nTalogy\nEngland, United Kingdom (Remote)\n$45/yr - $50/yr\n3 company alumni work here\nPromoted\nEasy Apply\nSenior Data Project Manager\nPrimis\nUnited Kingdom (Remote)\nActively recruiting\nPromoted\nEasy Apply\nSoftware Project Manager (Fashion/Apparel Industry)\nCGS (Computer Generated Solutions)\nUnited Kingdom (Remote)\n1 company alum works here\nApplied 26 minutes ago\nSolar Project Manager (Construction)\nSpencer Ogden\nUnited Kingdom (Remote)\n2 school alumni work here\nPromoted\nEasy Apply\nPensions Project Manager - GMPe\nBuck, A Gallagher Company\nUnited Kingdom (Remote)\n2 company alumni work here\nPromoted\nEasy Apply\nSenior Project Manager - Marketing, Comms, 2/3D Animation & Webinars\nECOM\nUnited Kingdom (Remote)\n£60K/yr - £65K/yr\nActively recruiting\nPromoted\nEasy Apply\nSenior Project Manager - Medical Devices\nSpacelabs Healthcare\nUnited Kingdom (Remote)\n1 company alum works here\nPromoted\nEasy Apply\nProject Manager - Business Transformation - French Speaking\nTechShack\nUnited Kingdom (Remote)\nActively recruiting\nPromoted\nEasy Apply\nFinancial Analyst & Project Manager\nBuck, A Gallagher Company\nUnited Kingdom (Remote)\n2 company alumni work here\nPromoted\nEasy Apply\nD365 Project Manager\nThe Engage Partnership Recruitment\nUnited Kingdom (Remote)\n£100K/yr - £125K/yr\nYour profile matches this job\nPromoted\nEasy Apply\nCAFM Project Manager\nJumar\nUnited Kingdom (Remote)\n£50/hr - £75/hr\nActively recruiting\nPromoted\nEasy Apply\nSenior Project Manager - Dynamics D365 (BC OR CE) - UK\nConspicuous\nUnited Kingdom (Remote)\nActively recruiting\nPromoted\nEasy Apply\nEngagement Manager - South West\nMacmillan Cancer Support\nBristol, England, United Kingdom (Remote)\nYour profile matches this job\nPromoted\nSAP Project Manager\nIBU Consulting\nUnited Kingdom (Remote)\nActively recruiting\n4 months ago\nEasy Apply\nSenior Project Manager\nISL Talent\nEngland, United Kingdom (Remote)\n£50K/yr - £60K/yr\nActively recruiting\nPromoted\nEasy Apply\nTranscreation Project Manager\nKey Content - Agency\nOxford, England, United Kingdom (Remote)\nActively recruiting\nPromoted\nEasy Apply\nSenior Project Manager\nPeaple Talent\nCardiff, Wales, United Kingdom (Remote)\n£50K/yr - £55K/yr\nActively recruiting\nPromoted\nEasy Apply\nSenior PMO / Project Change Manager (Healthcare)\nAttain\nUnited Kingdom (Remote)\n3 school alumni work here\nPromoted\nEasy Apply\nSenior Project Manager - London Markets\nDXC Technology\nEngland, United Kingdom (Remote)\n12 company alumni work here\nPromoted\nEasy Apply\nMicrosoft Project Manager\nCloud Decisions\nUnited Kingdom (Remote)\n£60K/yr - £70K/yr\nActively recruiting\nPromoted\nEasy Apply'
                        #link.text looks like this: 'Technical Project Manager (Must speak French and English)\nTalogy\nEngland, United Kingdom (Remote)\n$45/yr - $50/yr\n3 company alumni work here\nPromoted\nEasy Apply'
                        # if child.text not in self.blacklist:
                        #     temp = link.get_attribute("data-job-id")
                        #     jobID = temp.split(":")[-1]
                        #     IDs.append(int(jobID))
                #IDs = set(IDs)
                length_of_ids = len(IDs)
                log.info("it found this many job IDs with EasyApply button: %s", length_of_ids)
                # remove already applied jobs
                jobIDs = list(set(IDs) - self.appliedJobIDs)
                # given how the script works not, it should be the same number to this print and the above print, unless you also implement filtration by the job titles without opening the thing  
                log.info("This many job IDs passed filtration: %s", len(jobIDs))

                # it assumed that 25 jobs are listed in the results window
                if len(jobIDs) == 0 and len(IDs) > 23:
                    jobs_per_page = jobs_per_page + 25
                    count_job = 0
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                    location,
                                                                    jobs_per_page)
                    
                if len(jobIDs) == 0 and len(IDs) <= 23:
                    log.debug("No links found")
                    break


                # loop over IDs to apply
                # although _ doesn't seem used it, don't delete it. It's there for a reason
                for _, jobID in enumerate(jobIDs):
                    count_job += 1
                    self.get_job_page(jobID)

                    # get easy apply button
                    button = self.get_easy_apply_button()
                    # word filter to skip positions not wanted

                    if button is not False:
                        string_easy = "* has Easy Apply Button"
                        log.info("Clicking the EASY apply button")

                        self.browser.execute_script("let xpathExpression = '//button[contains(@class, \"jobs-apply-button\")]'; let matchingElement = document.evaluate(xpathExpression, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; if (matchingElement) {matchingElement.click()} else {console.log(\"Element not found with the given XPath expression.\")}")
                        #button.click() #this was commented out, as it stopped working after LinkedIn updated their website, and self.browser.execute_script() seem to work better (it's just lower level code than selenium. I could probably do all what selenium does with just JS)
                        time.sleep(4)
                        result: bool = self.send_resume()
                        count_application += 1
                    else:
                        log.info("The button does not exist.")
                        string_easy = "* Doesn't have Easy Apply Button"
                        # TODO: job ID should be added to applied to, to avoid it being openend again
                        result = False

                    position_number: str = str(count_job + jobs_per_page)

                    # Define a regular expression pattern to match non-UTF-8 characters
                    non_utf8_pattern = re.compile(r'[^\x00-\x7F]+')

                    # Remove or replace non-UTF-8 characters with a space
                    cleaned_title = re.sub(non_utf8_pattern, ' ', self.browser.title)

                    sanitisedBrowserTitle = cleaned_title.encode("utf-8").decode("utf-8")

                    log.info(f"Position {position_number}:\n {sanitisedBrowserTitle} \n {string_easy} \n")

                    self.write_to_file(button, jobID, sanitisedBrowserTitle, result)

                    # # sleep every 30 applications
                    # if count_application != 0 and count_application % 30 == 0:
                    #     sleepTime: int = random.randint(300, 500)
                    #     log.info(f"""********count_application: {count_application}************\n\n
                    #                 Time for a nap - see you in:{int(sleepTime / 60)} min
                    #             ****************************************\n\n""")
                    #     time.sleep(sleepTime)

                    # go to new page if all jobs are done
                    if count_job == len(jobIDs):                        
                        # break right here in case last job was old, this will save another reload, and just speed thing up in general. If it matches, do a break statement
                        if any(phrase in last_link for phrase in ["week ago", 
                                                                  "6 days ago", 
                                                                  "5 days ago", 
                                                                  "4 days ago", 
                                                                  "3 days ago", 
                                                                  # "2 days ago", 
                                                                  "weeks ago", 
                                                                  "month ago", 
                                                                  "months ago"]):
                            log.debug("moving onto the next combo, due to no new jobs available to apply to for this combo")
                            break # this skips this job/location combo
                        jobs_per_page = jobs_per_page + 25
                        count_job = 0
                        log.info("""****************************************\n\n
                        Going to next jobs page, YEAAAHHH!!
                        ****************************************\n\n""")
                        self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                        location,
                                                                        jobs_per_page)
            except Exception as e:
                log.info(e)

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp: str = datetime.now().strftime('%d/%m/%Y %H:%M')
        attempted: bool = False if button == False else True
        job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

        toWrite: list = [timestamp, jobID, job, company, attempted, result]
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):

        job: str = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.load_page_and_wait_until_it_stops_loading(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def get_easy_apply_button(self):
        while True:
            try:
                button = self.browser.find_elements("xpath",
                    '//button[contains(@class, "jobs-apply-button")]'
                )
                EasyApplyButton = button[0]
                break # Exit the loop if button is found successfully
            except IndexError: # this happens very rarely, it hapened only once after 1500 succesful applications
                print("Button not found. Waiting for 30 seconds and trying again...")
                time.sleep(30)  # Wait for 30 seconds before trying again
            except Exception as e: 
                log.info("Exception:",e)
                EasyApplyButton = False

        return EasyApplyButton        


    def send_resume(self) -> bool:
        def is_present(button_locator) -> bool:
            return len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0

        try:
            time.sleep(random.uniform(1.5, 2.5))
            next_locater = (By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']")
            review_locater = (By.CSS_SELECTOR,
                              "button[aria-label='Review your application']")
            submit_locater = (By.CSS_SELECTOR,
                              "button[aria-label='Submit application']")
            submit_application_locator = (By.CSS_SELECTOR,
                                          "button[aria-label='Submit application']")
            follow_locator = (By.CSS_SELECTOR, "label[for='follow-company-checkbox']")
            term_agree = (By.CSS_SELECTOR, "label[data-test-text-selectable-option__label='I Agree Terms & Conditions']")

            question_element = (By.XPATH, "//span[contains(text(), 'Will you now or in the future require sponsorship for employment visa status?')]")

            question_element_was_it_clicked_once_already_for_this_submission = False

            submitted = False
            while True:
                if is_present(term_agree):
                    button: None = self.wait.until(EC.element_to_be_clickable(term_agree))
                    button.click()
                    time.sleep(random.uniform(1.5, 2.5))

                if is_present(question_element) and not question_element_was_it_clicked_once_already_for_this_submission:
                    input_element = self.browser.find_element(By.XPATH, 
                                                              "//span[contains(text(), 'Will you now or in the future require sponsorship for employment visa status?')]")
                    question_element_was_it_clicked_once_already_for_this_submission = True
                    input_element.click()
                    time.sleep(1)
                    # Create an ActionChains object
                    actions = ActionChains(self.browser)
                    # Send keys to the browser window using ActionChains
                    actions.send_keys(Keys.TAB).perform()
                    time.sleep(1)
                    actions.send_keys(Keys.DOWN).perform()
                    # actions.send_keys(Keys.SPACE).perform()
                    time.sleep(random.uniform(1.5, 2.5))

                # Click Next or submitt button if possible
                button: None = None
                buttons: list = [next_locater, review_locater, follow_locator,
                           submit_locater, submit_application_locator]
                for i, button_locator in enumerate(buttons):
                    if is_present(button_locator):
                        button: None = self.wait.until(EC.element_to_be_clickable(button_locator))

                    # Find the element with the class "artdeco-inline-feedback__message"
                    # Find all of the elements with the class "artdeco-inline-feedback__message"
                    message_elements = self.browser.find_elements(By.CLASS_NAME, "artdeco-inline-feedback__message")

                    # Flag variable to track whether we need to break out of the outer loop
                    break_outer_loop = False

                    # Iterate over the message elements and print the text of each one
                    # for message_element in message_elements:
                    if message_elements:
                        # message_text = message_element.text
                        # log.info(message_text)
                        break_outer_loop = True  # Set the flag to break the outer loop
                        log.debug("setting break_outer_loop to True")
                        # winsound.PlaySound("C:\Windows\Media\chimes.wav", winsound.SND_FILENAME)
                        # input("Press Enter to continue...")
                        # print("needed manual intervention")
                        break

                    if break_outer_loop:
                        break  # Break the outer loop if the flag is set

                    if button:
                        button.click()
                        time.sleep(random.uniform(1.5, 2.5))
                        if i in (3, 4):
                            submitted = True
                        if i != 2:
                            break
                if button is None or break_outer_loop:
                    log.info(f"Could not complete submission, break_outer_loop is {break_outer_loop} and button is {button}")
                    # TODO: job ID should be added to applied to, to avoid it being openend again
                    break
                elif submitted:
                    global num_successful_jobs_global_variable
                    num_successful_jobs_global_variable += 1
                    log.info(f"Application Submitted. Today you have applied to {num_successful_jobs_global_variable} jobs")

                    if (num_successful_jobs_global_variable > 249):
                        log.debug("You have applied to more than 249 jobs today. Exiting the app...")
                        # Get the PID of the process with "cmd.exe" and "easyapplybot.py" in its name.
                        process_id = get_process_id("automated-LinkedIn-applying\\run_script.bat")
                        if process_id is not None:
                            terminate_process(process_id)
                            exit() #just incase if running from the VSC
                        else:
                            exit() #just incase if running from the VSC
                    break

            time.sleep(random.uniform(1.5, 2.5))


        except Exception as e:
            log.info(e)
            log.info("cannot apply to this job")
            raise (e)

        return submitted

    def load_page(self, sleep=1):
        # scroll_page = 0
        # while scroll_page < 4000:
        #     self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
        #     scroll_page += 300
        #     time.sleep(sleep)

        # if sleep != 1:
        #     self.browser.execute_script("window.scrollTo(0,0);")
        #     time.sleep(sleep * 2)
        #time.sleep(random.uniform(2.5, 3.5))
        if sleep == 2:
            scrollresults = self.browser.find_element(By.CLASS_NAME,
                "jobs-search-results-list")
            # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
            for i in range(300, 3600, 100):
                self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults)
                time.sleep(0.3)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def next_jobs_page(self, position, location, jobs_per_page):
        self.load_page_and_wait_until_it_stops_loading("https://www.linkedin.com/jobs/search/?f_LF=f_AL" + "&distance=5" + "&keywords=" +
            position + location + "&sortBy=DD" + "&start=" + str(jobs_per_page))
            
        # todo: now that would be a good call to do that scrolling thing, of the left pane
        self.load_page(sleep=2)
        return (self.browser, jobs_per_page)
    
    def load_page_and_wait_until_it_stops_loading(self, job_url):
        self.browser.get(job_url)
        self.wait.until(lambda driver: self.browser.execute_script('return document.readyState') == 'complete')
        # Page is now fully loaded and ready to be interacted with


if __name__ == '__main__':
    with open("config.yaml", 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    assert len(parameters['positions']) > 0
    assert len(parameters['locations']) > 0
    assert parameters['username'] is not None
    assert parameters['password'] is not None

    log.info({k: parameters[k] for k in parameters.keys() if k not in ['username', 'password']})

    output_filename: list = [f for f in parameters.get('output_filename', ['output.csv']) if f != None]
    output_filename: list = output_filename[0] if len(output_filename) > 0 else 'output.csv'
    blacklist = parameters.get('blacklist', [])
    blackListTitles = parameters.get('blackListTitles', [])

    bot = EasyApplyBot(parameters['username'],
                       parameters['password'],
                       filename=output_filename,
                       blacklist=blacklist,
                       blackListTitles=blackListTitles
                       )

    locations: list = [l for l in parameters['locations'] if l != None]
    positions: list = [p for p in parameters['positions'] if p != None]
    bot.start_apply(positions, locations)

    log.debug("controlled exit due to all job/location combos being processed successfully")
    # Get the PID of the process with "cmd.exe" and "easyapplybot.py" in its name.
    if process_id is not None:
        terminate_process(process_id)
        exit() #just incase if running from the VSC, defensive programming.
    else:
        exit() #just incase if running from the VSC

# log.debug("No links found")
# figure out why you have ^ two of the above statements in your code. The code seem to be breaking also, perhaps because of that 
#NOT (senior OR lead OR chief OR gas OR forklift OR lift OR fire OR electric OR air OR sprinkler OR HVAC OR construction OR mechanical)

# make it run headless unless last login attempt lead to captcha, as a setting in the config.yaml

# TODO: play around with auto filling fields which require a number with 0, as it will increase autocompletion rate of applications