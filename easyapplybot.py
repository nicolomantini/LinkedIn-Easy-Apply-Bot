import time, random, os, csv, datetime, platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import pyautogui
from tkinter import filedialog, Tk
import tkinter.messagebox as tm
from urllib.request import urlopen
import loginGUI
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(ChromeDriverManager().install())

# pyinstaller --onefile --windowed --icon=app.ico easyapplybot.py

class EasyApplyBot:

    MAX_APPLICATIONS = 500

    def __init__(self,username,password, language, position, location, resumeloctn, appliedJobIDs=[], filename='output.csv'):

        print("\nWelcome to Easy Apply Bot\n")
        dirpath = os.getcwd()
        print("current directory is : " + dirpath)


        self.position = position
        self.location = "&location=" + location
        self.resumeloctn = resumeloctn
        self.language = language
        self.appliedJobIDs = appliedJobIDs
        self.filename = filename
        self.options = self.browser_options()
        self.browser = driver
        self.wait = WebDriverWait(self.browser, 30)
        self.start_linkedin(username,password)


    def browser_options(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        #options.add_argument("user-agent=Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393")
        #options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        #options.add_argument('--disable-gpu')
        #options.add_argument('disable-infobars')
        options.add_argument("--disable-extensions")
        return options

    def start_linkedin(self,username,password):
        print("\nLogging in.....\n \nPlease wait :) \n ")
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
            print("TimeoutException! Username/password field or login button not found")

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
                print("\nStarting LinkedIn bot\n")
                break
            else:
                time.sleep(1)
                print("\nPlease Login to your LinkedIn account\n")

    def fill_data(self):
        self.browser.set_window_size(0, 0)
        self.browser.set_window_position(2000, 2000)
        os.system("reset")

        print(self.resumeloctn)

    def start_apply(self):
        #self.wait_for_login()
        self.fill_data()
        self.applications_loop()

    def applications_loop(self):

        count_application = 0
        count_job = 0
        jobs_per_page = 0

        os.system("reset")

        print("\nLooking for jobs.. Please wait..\n")

        self.browser.set_window_position(0, 0)
        self.browser.maximize_window()
        self.browser, _ = self.next_jobs_page(jobs_per_page)
        print("\nLooking for jobs.. Please wait..\n")
        #below was causing issues, and not sure what they are for.
        #self.browser.find_element_by_class_name("jobs-search-dropdown__trigger-icon").click()
        #self.browser.find_element_by_class_name("jobs-search-dropdown__option").click()
        #self.job_page = self.load_page(sleep=0.5)

        while count_application < self.MAX_APPLICATIONS:

            # sleep to make sure everything loads, add random to make us look human.
            time.sleep(random.uniform(3.5, 6.9))
            self.load_page(sleep=1)

            # get job links
            links = self.browser.find_elements_by_xpath(
                    '//div[@data-job-id]'
                    )

            # get job ID of each job link
            IDs = []
            for link in links :
                temp = link.get_attribute("data-job-id")
                jobID = temp.split(":")[-1]
                IDs.append(int(jobID))
            IDs = set(IDs)

            # remove already applied jobs
            jobIDs = [x for x in IDs if x not in self.appliedJobIDs]

            if len(jobIDs) == 0:
                jobs_per_page = jobs_per_page + 25
                count_job = 0
                self.avoid_lock()
                self.browser, jobs_per_page = self.next_jobs_page(jobs_per_page)

            # loop over IDs to apply
            for jobID in jobIDs:
                count_job += 1
                self.get_job_page(jobID)

                # get easy apply button
                button = self.get_easy_apply_button ()
                if button is not False:
                    string_easy = "* has Easy Apply Button"
                    button.click()
                    time.sleep (3)
                    result = self.send_resume()
                    count_application += 1
                else:
                    string_easy = "* Doesn't have Easy Apply Button"
                    result = False

                position_number = str(count_job + jobs_per_page)
                print(f"\nPosition {position_number}:\n {self.browser.title} \n {string_easy} \n")

                # append applied job ID to csv file
                timestamp = datetime.datetime.now()
                toWrite = [timestamp, jobID, str(self.browser.title).split(' | ')[0], str(self.browser.title).split(' | ')[1], button, result]
                with open(self.filename,'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(toWrite)

                # sleep every 20 applications
                if count_application != 0  and count_application % 20 == 0:
                    sleepTime = random.randint(500, 900)
                    print(f'\n\n********count_application: {count_application}************\n\n')
                    print(f"Time for a nap - see you in:{int(sleepTime/60)} min")
                    print('\n\n****************************************\n\n')
                    time.sleep (sleepTime)

                # go to new page if all jobs are done
                if count_job == len(jobIDs):
                    jobs_per_page = jobs_per_page + 25
                    count_job = 0
                    print('\n\n****************************************\n\n')
                    print('Going to next jobs page, YEAAAHHH!!')
                    print('\n\n****************************************\n\n')
                    self.avoid_lock()
                    self.browser, jobs_per_page = self.next_jobs_page(jobs_per_page)

        self.finish_apply()

    def get_job_links(self, page):
        links = []
        for link in page.find_all('a'):
            url = link.get('href')
            if url:
                if '/jobs/view' in url:
                    links.append(url)
        return set(links)

    def get_job_page(self, jobID):
        #root = 'www.linkedin.com'
        #if root not in job:
        job = 'https://www.linkedin.com/jobs/view/'+ str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def got_easy_apply(self, page):
        #button = page.find("button", class_="jobs-apply-button artdeco-button jobs-apply-button--top-card artdeco-button--3 ember-view")

        button = self.browser.find_elements_by_xpath(
                    '//button[contains(@class, "jobs-apply")]/span[1]'
                    )
        EasyApplyButton = button [0]
        if EasyApplyButton.text in "Easy Apply" :
            return EasyApplyButton
        else :
            return False
        #return len(str(button)) > 4

    def get_easy_apply_button(self):
        try :
            button = self.browser.find_elements_by_xpath(
                        '//button[contains(@class, "jobs-apply")]/span[1]'
                        )
            #if button[0].text in "Easy Apply" :
            EasyApplyButton = button [0]
        except :
            EasyApplyButton = False

        return EasyApplyButton

    def easy_apply_xpath(self):
        button = self.get_easy_apply_button()
        button_inner_html = str(button)
        list_of_words = button_inner_html.split()
        next_word = [word for word in list_of_words if "ember" in word and "id" in word]
        ember = next_word[0][:-1]
        xpath = '//*[@'+ember+']/button'
        return xpath

    def click_button(self, xpath):
        triggerDropDown = self.browser.find_element_by_xpath(xpath)
        time.sleep(0.5)
        triggerDropDown.click()
        time.sleep(1)

    def send_resume(self):
        def is_present(button_locator):
            return len(self.browser.find_elements(button_locator[0],
                                                     button_locator[1])) > 0

        try:
            time.sleep(3)
            #print(f"Navigating... ")
            next_locater = (By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
            review_locater = (By.CSS_SELECTOR, "button[aria-label='Review your application']")
            submit_locater = (By.CSS_SELECTOR, "button[aria-label='Submit application']")
            submit_application_locator = (By.CSS_SELECTOR, "button[aria-label='Submit application']")
            error_locator = (By.CSS_SELECTOR, "p[data-test-form-element-error-message='true']")
            
            submitted = False
            while True:
                button = None
                for i, button_locator in enumerate([next_locater, review_locater, submit_locater, submit_application_locator]):
                    #print(i)
                    if is_present(button_locator):
                        #print("button found")
                        button = self.wait.until(EC.element_to_be_clickable(button_locator))
                    
                    if is_present(error_locator):
                        for element in self.browser.find_elements(error_locator[0],
                                                 error_locator[1]):
                            text = element.text
                            if "Please enter a valid answer" in text:
                                #print("Error Found")
                                #print(element.get_attribute('class'))
                                button = None
                                break
                    if button:
                        button.click()
                        time.sleep(random.uniform(1.5, 2.5))
                        if i in (2, 3):
                            submitted = True
                        break
                if button == None:
                    print("Could not complete submission")
                    break
                elif submitted:
                    print("Application Submitted")
                    break

            time.sleep(random.uniform(1.5, 2.5))

            #After submiting the application, a dialog shows up, we need to close this dialog
            close_button_locator = (By.CSS_SELECTOR, "button[aria-label='Dismiss']")
            if is_present(close_button_locator):
                close_button = self.wait.until(EC.element_to_be_clickable(close_button_locator))
                close_button.click()

        except Exception as e:
            print(e)
            print("cannot apply to this job")
            raise(e)

        return submitted

    def load_page(self, sleep=1):
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0,"+str(scroll_page)+" );")
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

    def next_jobs_page(self, jobs_per_page):
        self.browser.get(
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            self.position + self.location + "&start="+str(jobs_per_page))
        self.avoid_lock()
        self.load_page()
        return (self.browser, jobs_per_page)

    def finish_apply(self):
        self.browser.close()

if __name__ == '__main__':

    # set use of gui (T/F)

    useGUI = True
    #useGUI = False

    # use gui
    if useGUI == True:

        app = loginGUI.LoginGUI()
        app.mainloop()

        #get user info info
        username=app.frames["StartPage"].username
        password=app.frames["StartPage"].password
        language=app.frames["PageOne"].language
        position=app.frames["PageTwo"].position
        location_code=app.frames["PageThree"].location_code
        if location_code == 1:
            location=app.frames["PageThree"].location
        else:
            location = app.frames["PageFour"].location
        resumeloctn=app.frames["PageFive"].resumeloctn

    # no gui
    if useGUI == False:

        username = ''
        password = ''
        language = 'en'
        position = 'marketing'
        location = ''
        resumeloctn = ''

    # print input
    print("\nThese is your input:")

    print(
        "\nUsername:  "+ username,
        "\nPassword:  "+ password,
        "\nLanguage:  "+ language,
        "\nPosition:  "+ position,
        "\nLocation:  "+ location
        )

    print("\nLet's scrape some jobs!\n")

    # get list of already applied jobs
    filename = 'joblist.csv'
    try:
        df = pd.read_csv(filename, header=None)
        appliedJobIDs = list (df.iloc[:,1])
    except:
        appliedJobIDs = []

    # start bot
    bot = EasyApplyBot(username, password, language, position, location, resumeloctn, appliedJobIDs, filename)
    bot.start_apply()
