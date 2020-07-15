import time, random, os, csv, datetime, platform

from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import pandas as pd
import pyautogui

import loginGUI
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime
import logging

import win32com.client as comctl
wsh =comctl.Dispatch("WScript.Shell")

log = logging.getLogger(__name__)
driver = webdriver.Chrome(ChromeDriverManager().install())


# pyinstaller --onefile --windowed --icon=app.ico easyapplybot.py

class EasyApplyBot:
    MAX_APPLICATIONS = 5

    def __init__(self, username, password, language, positions, locations, resumeloctn, appliedJobIDs=[],
                 filename='output.csv'):

        log.info("Welcome to Easy Apply Bot\n")
        dirpath = os.getcwd()
        log.info("current directory is : " + dirpath)

        self.positions = positions
        self.locations = locations
        self.resumeloctn = resumeloctn
        self.language = language
        self.appliedJobIDs = appliedJobIDs
        self.filename = filename
        self.options = self.browser_options()
        self.browser = driver
        self.wait = WebDriverWait(self.browser, 30)
        self.start_linkedin(username, password)

    def browser_options(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        # options.add_argument("user-agent=Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393")
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        # options.add_argument('--disable-gpu')
        # options.add_argument('disable-infobars')
        options.add_argument("--disable-extensions")
        return options

    def start_linkedin(self, username, password):
        log.info("Logging in.....Please wait :) ")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            user_field = self.browser.find_element_by_id("username")
            pw_field = self.browser.find_element_by_id("password")
            login_button = self.browser.find_element_by_css_selector(".btn__primary--large")
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(1)
            pw_field.send_keys(password)
            time.sleep(1)
            login_button.click()
        except TimeoutException:
            log.info("TimeoutException! Username/password field or login button not found")

    def wait_for_login(self):
        if language == "en":
            title = "Sign In to LinkedIn"
        elif language == "es":
            title = "Inicia sesión"
        elif language == "pt":
            title = "Entrar no LinkedIn"

        time.sleep(1)

        while True:
            if self.browser.title != title:
                log.info("Starting LinkedIn bot\n")
                break
            else:
                time.sleep(1)
                log.info("Please Login to your LinkedIn account\n")

    def fill_data(self):
        self.browser.set_window_size(0, 0)
        self.browser.set_window_position(2000, 2000)
        os.system("reset")

        log.info(self.resumeloctn)

    def start_apply(self):
        # self.wait_for_login()
        self.fill_data()
        # TODO commented out positions and locations for loops since they caused issues with search. Need to fix later
        # for position in self.positions:
        #   for location in self.locations:
        log.info(f"Applying to {position}: {location}")
        # location = "&location=" + location
        self.applications_loop(position, location)
        self.finish_apply()

    def applications_loop(self, position, location):

        count_application = 0
        count_job = 0
        jobs_per_page = 0

        os.system("reset")

        log.info("Looking for jobs.. Please wait..")

        self.browser.set_window_position(0, 0)
        self.browser.maximize_window()
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page)
        log.info("Looking for jobs.. Please wait..")
        # below was causing issues, and not sure what they are for.
        # self.browser.find_element_by_class_name("jobs-search-dropdown__trigger-icon").click()
        # self.browser.find_element_by_class_name("jobs-search-dropdown__option").click()
        # self.job_page = self.load_page(sleep=0.5)

        while count_application < self.MAX_APPLICATIONS:

            # sleep to make sure everything loads, add random to make us look human.
            randoTime = random.uniform(3.5, 6.9)
            log.info("Sleeping for %s", randoTime)
            time.sleep(randoTime)
            self.load_page(sleep=1)

            # get job links
            links = self.browser.find_elements_by_xpath(
                '//div[@data-job-id]'
            )

            # get job ID of each job link
            IDs = []
            for link in links:
                temp = link.get_attribute("data-job-id")
                jobID = temp.split(":")[-1]
                IDs.append(int(jobID))
            IDs = set(IDs)

            # remove already applied jobs
            jobIDs = [x for x in IDs if x not in self.appliedJobIDs]

            if len(jobIDs) == 0:
                jobs_per_page = jobs_per_page + 25
                count_job = 0
                #self.avoid_lock()
                self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                  location,
                                                                  jobs_per_page)

            # loop over IDs to apply
            for jobID in jobIDs:
                count_job += 1
                self.get_job_page(jobID)

                # get easy apply button
                button = self.get_easy_apply_button()
                if button is not False:
                    string_easy = "* has Easy Apply Button"
                    button.click()
                    time.sleep(3)
                    result = self.send_resume()
                    count_application += 1
                else:
                    string_easy = "* Doesn't have Easy Apply Button"
                    result = False

                position_number = str(count_job + jobs_per_page)
                log.info(f"Position {position_number}:\n {self.browser.title} \n {string_easy} \n")

                # append applied job ID to csv file
                timestamp = datetime.now()
                toWrite = [timestamp, jobID, str(self.browser.title).split(' | ')[0],
                           str(self.browser.title).split(' | ')[1], button, result]
                log.info("Saving the following row in joblist")
                log.info(str(toWrite))
                with open(self.filename, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(toWrite)

                # sleep every 20 applications
                if count_application != 0 and count_application % 20 == 0:
                    sleepTime = random.randint(500, 900)
                    log.info(f'********count_application: {count_application}************\n\n')
                    log.info(f"Time for a nap - see you in:{int(sleepTime / 60)} min")
                    log.info('****************************************\n\n')
                    time.sleep(sleepTime)

                # go to new page if all jobs are done
                if count_job == len(jobIDs):
                    jobs_per_page = jobs_per_page + 25
                    count_job = 0
                    log.info('****************************************\n\n')
                    log.info('Going to next jobs page, YEAAAHHH!!')
                    log.info('****************************************\n\n')
                    #self.avoid_lock()
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                      location,
                                                                      jobs_per_page)

    def get_job_links(self, page):
        links = []
        for link in page.find_all('a'):
            url = link.get('href')
            if url:
                if '/jobs/view' in url:
                    links.append(url)
        return set(links)

    def get_job_page(self, jobID):
        # root = 'www.linkedin.com'
        # if root not in job:
        job = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        log.info("Opening Job Page \n %s", job)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def got_easy_apply(self, page):
        # button = page.find("button", class_="jobs-apply-button artdeco-button jobs-apply-button--top-card artdeco-button--3 ember-view")

        button = self.browser.find_elements_by_xpath(
            '//button[contains(@class, "jobs-apply")]/span[1]'
        )
        EasyApplyButton = button[0]
        if EasyApplyButton.text in "Easy Apply":
            return EasyApplyButton
        else:
            return False
        # return len(str(button)) > 4

    def get_easy_apply_button(self):
        try:
            button = self.browser.find_elements_by_xpath(
                '//button[contains(@class, "jobs-apply")]/span[1]'
            )
            # if button[0].text in "Easy Apply" :
            EasyApplyButton = button[0]
        except:
            EasyApplyButton = False

        return EasyApplyButton

    def easy_apply_xpath(self):
        button = self.get_easy_apply_button()
        button_inner_html = str(button)
        list_of_words = button_inner_html.split()
        next_word = [word for word in list_of_words if "ember" in word and "id" in word]
        ember = next_word[0][:-1]
        xpath = '//*[@' + ember + ']/button'
        return xpath

    def click_button(self, xpath):
        triggerDropDown = self.browser.find_element_by_xpath(xpath)
        time.sleep(0.5)
        triggerDropDown.click()
        time.sleep(1)

    def is_jsonable(self, x):
        try:
            json.dumps(x)
            return True
        except:
            return False

    def send_resume(self):
        def is_present(button_locator):
            return len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0

        try:
            time.sleep(3)
            log.info("Attempting to send resume")
            #TODO These locators are not future proof. These labels could easily change. Ideally we would search for contained text;
            # was unable to get it to work using XPATH and searching for contained text
            upload_locater = (By.CSS_SELECTOR, "label[aria-label='DOC, DOCX, PDF formats only (2 MB).']")
            next_locater = (By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
            review_locater = (By.CSS_SELECTOR, "button[aria-label='Review your application']")
            submit_locater = (By.CSS_SELECTOR, "button[aria-label='Submit application']")
            submit_application_locator = (By.CSS_SELECTOR, "button[aria-label='Submit application']")
            error_locator = (By.CSS_SELECTOR, "p[data-test-form-element-error-message='true']")

            testLabel_locator = (By.XPATH, "//span[@data-test-form-element-label-title='true']")
            yes_locator = (By.XPATH, "//input[@value='Yes']")
            no_locator = (By.XPATH, "//input[@value='No']")
            textInput_locator = (By.XPATH, "//div[@data-test-single-line-text-input-wrap='true']")


            submitted = False
            attemptQuestions = True
            while not submitted:
                button = None
                for i, button_locator in enumerate(
                        [upload_locater, next_locater, review_locater, submit_locater, submit_application_locator]):

                    log.info("Searching for button locator: %s", str(button_locator))
                    if is_present(button_locator):
                        log.info("button found with this locator: %s", str(button_locator))
                        button = self.wait.until(EC.element_to_be_clickable(button_locator))
                    else:
                        log.info("Unable to find button locator: %s", str(button_locator))
                        continue

                    if is_present(error_locator):
                        log.info("Checking for errors")
                        for errorElement in self.browser.find_elements(error_locator[0],
                                                                  error_locator[1]):
                            text = errorElement.text
                            if "Please enter a valid answer" in text:
                                log.warning("Warning message received: %s", text)
                                log.info("Attempting to resolve by finding test questions")

                                #TODO these questions will need to be logged so that way, individuals can look through the logs and add them at the end of an application run.
                                #Required question expects an answer. Search through possible questions/answer combos
                                if is_present(testLabel_locator) and attemptQuestions:
                                    for testLabelElement in self.browser.find_elements(testLabel_locator[0],
                                                                              testLabel_locator[1]):
                                        try:
                                            log.info("Found test element %s", testLabel_locator)
                                            text = testLabelElement.text
                                            log.info("test element text: %s", text)
                                            #assuming this question is asking if I am authorized to work in the US
                                            if ("Are you" in text and "authorized" in text) or ("Have You" in text and "eduation" in text):
                                                #Be sure to find the child element of the current test question section
                                                yesRadio = testLabelElement.find_element(By.XPATH, yes_locator[1])
                                                time.sleep(1)
                                                log.info("Attempting to click the radio button for %s", yes_locator)
                                                self.browser.execute_script("arguments[0].click()", yesRadio)
                                                log.info("Clicked the radio button %s", yes_locator)

                                            #assuming this question is asking if I require sponsorship
                                            if "require" in text and "sponsorship" in text:
                                                noRadio = testLabelElement.find_element(By.XPATH, no_locator[1])
                                                time.sleep(1)
                                                log.info("Attempting to click the radio button for %s", no_locator)
                                                self.browser.execute_script("arguments[0].click()", noRadio)
                                                log.info("Clicked the radio button %s", no_locator)

                                            # assuming this question is asking if I require sponsorship
                                            if "you have" in text and "Bachelor's" in text:
                                                yesRadio = testLabelElement.find_element(By.XPATH, yes_locator[1])
                                                time.sleep(1)
                                                log.info("Attempting to click the radio button for %s", yes_locator)
                                                self.browser.execute_script("arguments[0].click()", yesRadio)
                                                log.info("Clicked the radio button %s", yes_locator)

                                            #Some questions are asking how many years of experience you have in a specific skill
                                            #Automatically put the number of years that I have worked.
                                            if "How many years" in text and "experience" in text:
                                                textField = testLabelElement.find_element(By.XPATH, textInput_locator[1])
                                                time.sleep(1)
                                                log.info("Attempting to click the text field for %s", textInput_locator)
                                                self.browser.execute_script("arguments[0].click()", textField)
                                                log.info("Clicked the text field %s", textInput_locator)
                                                time.sleep(1)
                                                log.info("Attempting to send keys to the text field %s", textInput_locator)
                                                textField.send_keys("10")
                                                log.info("Sent keys to the text field %s", textInput_locator)


                                        except Exception as e:
                                            log.exception("Could not answer additional questions: %s", e)
                                            log.error("Unable to submit due to error with no solution")
                                            return submitted
                                    attemptQuestions = False
                                    log.info("no longer going to try and answer questions, since we have now tried")
                                else:
                                    log.error("Unable to submit due to error with no solution")
                                    return submitted


                    if button:
                        if button_locator == upload_locater:
                            log.info("Uploading resume now")

                            time.sleep(2)
                            driver.execute_script("arguments[0].click()", button)

                            #TODO This can only handle Chrome right now. Firefox or other browsers will need to be handled separately
                            # Chrome opens the file browser window with the title "Open"
                            status = wsh.AppActivate("Open")
                            log.debug("Able to find file browser dialog: %s", status)
                            #Must sleep around sending the resume location so it has time to accept all keys submitted
                            time.sleep(1)
                            wsh.SendKeys(str(self.resumeloctn))
                            time.sleep(1)
                            wsh.SendKeys("{ENTER}")

                        else:
                            try:
                                log.info("attempting to click button: %s", str(button_locator))
                                response = button.click()
                                if (button_locator == submit_locater) or (button_locator == submit_application_locator):
                                    log.info("Clicked the submit button. RESPONSE: %s", str(response))
                                    submitted = True
                                    return submitted
                            except EC.StaleElementReferenceException:
                                log.warning("Button was stale. Couldnt click")


                        randoTime = random.uniform(1.5, 2.5)
                        log.info("Just finished using button %s ; Im going to sleep for %s ;", str(button_locator), randoTime)
                        time.sleep(randoTime)


            randoTime = random.uniform(1.5, 2.5)
            log.info("Going to sleep after attempting to send resume for %s", randoTime)
            time.sleep(randoTime)

            # After submitting the application, a dialog shows up, we need to close this dialog
            close_button_locator = (By.CSS_SELECTOR, "button[aria-label='Dismiss']")
            if is_present(close_button_locator):
                close_button = self.wait.until(EC.element_to_be_clickable(close_button_locator))
                close_button.click()

        except Exception as e:
            log.info(e)
            log.warning("cannot apply to this job")
            raise (e)

        return submitted

    def load_page(self, sleep=1):
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 200
            time.sleep(sleep)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep * 3)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def avoid_lock(self):
        x, _ = pyautogui.position()
        pyautogui.moveTo(x + 200, pyautogui.position().y, duration=1.0)
        pyautogui.moveTo(x, pyautogui.position().y, duration=0.5)
        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(0.5)
        pyautogui.press('esc')

    def next_jobs_page(self, position, location, jobs_per_page):
        self.browser.get(
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            position + location + "&start=" + str(jobs_per_page))
       # self.avoid_lock()
        self.load_page()
        return (self.browser, jobs_per_page)

    def finish_apply(self):
        self.browser.close()

def setupLogger():
    dt = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")
    logging.basicConfig(filename=('./logs/' + str(dt)+'applyJobs.log'), filemode='w', format='%(name)s::%(levelname)s::%(message)s', datefmt='./logs/%d-%b-%y %H:%M:%S') #TODO need to check if there is a log dir available or not

    log.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter('%(name)s::%(levelname)s::%(lineno)d- %(message)s')
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)

if __name__ == '__main__':

    setupLogger()
    # set use of gui (T/F)

    #TODO set the GUI flag as a configuration file/settings
    #useGUI = True
    useGUI = False

    # use gui
    if useGUI == True:

        app = loginGUI.LoginGUI()
        app.mainloop()

        # get user info info
        username = app.frames["StartPage"].username
        password = app.frames["StartPage"].password
        language = app.frames["PageOne"].language
        position = app.frames["PageTwo"].position
        location_code = app.frames["PageThree"].location_code
        if location_code == 1:
            location = app.frames["PageThree"].location
        else:
            location = app.frames["PageFour"].location
        resumeloctn = app.frames["PageFive"].resumeloctn

    # no gui
    if useGUI == False:
        #TODO Set the user information as configuration file/settings
        username = ''
        password = ''
        language = 'en'
        position = ''
        location = ''
        resumeloctn = ''

    # log.info input
    log.info("Your input:")

    log.info(
        "\nUsername:  %s \nPassword:  %s\nLanguage:  %s\nPosition:  %s\nLocation:  %s", username, 'Just Kidding', language, position, location   )

    log.info("Let's scrape some jobs!\n")

    # get list of already applied jobs
    filename = 'joblist.csv'
    try:
        df = pd.read_csv(filename, header=None)
        appliedJobIDs = list(df.iloc[:, 1])
    except:
        appliedJobIDs = []

    # start bot
    bot = EasyApplyBot(username, password, language, position, location, resumeloctn, appliedJobIDs, filename)
    bot.start_apply()
