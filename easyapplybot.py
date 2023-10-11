from __future__ import annotations
import time, random, os, csv, sys, platform
import logging
import argparse
import pickle
import datetime
from itertools import product
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import bs4
import pandas as pd
import pyautogui

from urllib.request import urlopen

import re
import yaml
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

def setupLogger() -> None:
    dt: str = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")

    if not os.path.isdir('./logs'):
        os.mkdir('./logs')

    # TODO need to check if there is a log dir available or not
    logging.basicConfig(filename=('./logs/' + str(dt) + 'applyJobs.log'),
                        filemode='w',
                        format='%(asctime)s::%(name)s::%(levelname)s::%(message)s',
                        datefmt='./logs/%d-%b-%y %H:%M:%S')
    log.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)
    return None

def get_browser_options():
    '''Configure browser to be less scrape-type'''
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-extensions")
    # Disable webdriver flags or you will be easily detectable
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return options

class EasyApplyBot:
    setupLogger()
    # MAX_SEARCH_TIME is 10 hours by default, feel free to modify it
    MAX_SEARCH_TIME = 10 * 60 * 60

    def __init__(self,
                 userParameters: dict = None,
                 cookies=[]) -> None:

        log.info("Welcome to Easy Apply Bot!")
        dirpath: str = os.getcwd()
        log.info("Current directory is : " + dirpath)
        log.debug(f"Parameters in bot: {str(userParameters)}")

        self.userParameters = userParameters
        self.uploads = userParameters['uploads']
        self.filename: str = userParameters['outputFilename']
        past_ids: list | None = self.get_appliedIDs(self.filename)
        self.appliedJobIDs: list = past_ids if past_ids != None else []
        
        self.blackList = userParameters['blackListCompanies']
        self.blackListTitles = userParameters['blackListTitles']
        self.jobListFilterKeys = userParameters['jobListFilterKeys']
        self.phone_number = userParameters['phoneNumber']

        self.jobsData = None
        
        #browser start
        self.options = get_browser_options()
        self.cookies = cookies
        try:
            self.browser = webdriver.Chrome(service = 
                            ChromeService(ChromeDriverManager().install()),
                            options=self.options)
        except Exception as err:
            log.error(f"Browser is not started: {str(err)}")
            self.browser.close()
            self.browser.exit()
            raise err
        log.debug("Browser loaded.")
        self.browser.get('https://www.linkedin.com/')
        for cookie in self.cookies: self.browser.add_cookie(cookie)
        self.wait = WebDriverWait(self.browser, 30)
        log.debug("Cookies sended.")
        return None

    def get_appliedIDs(self,
                       filename: str = None) -> list | None:
        '''Trying to get applied jobs ID from given csv file'''
        try:
            df = pd.read_csv(filename,
                             header=None,
                             names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
                             lineterminator='\n',
                             encoding='utf-8')
            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
            df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
            jobIDs: list = list(df.jobID)
            log.debug(f"JobIDs from CSV file: {str(jobIDs)}")
            log.info(f"{len(jobIDs)} jobIDs found in {filename}")
            return jobIDs
        except Exception as err:
            log.info(f"{str(err)} - jobIDs could not be loaded from {filename}")
            return None

    def get_job_filters_uri(self,
                            jobListFilterKeys: dict = None) -> str:
        """Building URI (a part of URL) for filters"""
        jobListFiltersURI: str = ''
        filterKeysMap = {
            "sort by" : ["Most Relevant",
                         "Most Recent"],
            "date posted" : ["Any Time", 
                             "Past Month",
                             "Past Week",
                             "Past 24 hours"],
            "easy apply enabler" : ["Easy Apply",
                                    "Usual Apply"]
            }
        filterKeysAlignment = {
            "Most Relevant" : "R",
            "Most Recent" : "DD",
            "Any Time" : None,
            "Past Week" : "r604800",
            "Past Month" : "r2592000",
            "Past 24 hours" : "r86400",
            "Easy Apply" : "f_AL",
            "Usual Apply" : None
            }
        filterKeysMapPrefix = {
            "sort by" : "sortBy",
            "date posted" : "f_TPR",
            "easy apply enabler" : "f_LF"
            }
        for element in jobListFilterKeys:
            if filterKeysAlignment[element] is not None:
                for key in filterKeysMapPrefix:
                    if element in filterKeysMap[key]:
                        jobListFiltersURI=str(jobListFiltersURI 
                                             + "&" 
                                             + filterKeysMapPrefix[key]
                                             + "="
                                             + filterKeysAlignment[element])
        log.debug(f"URI for filters: {jobListFiltersURI}")
        return jobListFiltersURI

    def apply_to_positions(self, 
                    positions:list,
                    locations:list,
                    jobListFilterKeys:list
                    ) -> None:
        '''Sets starting list for positions/locations combinatons
        and starts application fo each combination in the list.
        '''
        log.info("Start apllying")
        combos: list = None
#        self.browser.set_window_size(1, 1)
#        self.browser.set_window_position(2000, 2000)
        jobFiltersURI: str = self.get_job_filters_uri(jobListFilterKeys)
        combos = list(product(positions, locations))
        log.debug(str(combos))
        for combo in combos:
            position, location = list(combo)
            log.info(f"Applying to: {position}, {location}")
            fullJobURI: str = ("keywords="
                               + position
                               + "&location="
                               + location
                               + jobFiltersURI)
            log.debug(f"Full Job URI: {fullJobURI}")
            self.get_jobs_data(fullJobURI)
            # Remove already applied jobs
            self.jobsData = {k: self.jobsData[k] for k in self.jobsData.keys() - self.appliedJobIDs}
            log.debug(f"jobsID - {str(self.jobsData.keys())}")
            self.dump_current_jobs_to_log()
            # Remove blacklisted keywords
            if self.blackListTitles is not None:
                for key in self.jobsData:
                    if any(word in self.jobsData[key]['title'] for word in self.blackListTitles):
                        log.info(f"Skipping application {key},"
                                 + " a blacklisted keyword"
                                 + " was found in the job title")
                        self.jobsData[key]['skipReason'] = "blacklisted keyword"
            # Remove blacklisted companies
            if self.blackList is not None:
                for key in self.jobsData:
                    if any(word in self.jobsData[key]['company'] for word in self.blackList):
                        log.info(f"Skipping application {key},"
                                 + f" a blacklisted keyword"
                                 + " was found in the job title")
                        self.jobsData[key]['skipReason'] = "blacklisted company"
            # Go easy apply
            self.jobsData = self.easy_apply()
            # sleep for a moment
            sleepTime: int = random.randint(60, 300)
            log.info(f"Time for a nap - see you in:{int(sleepTime/60)} min.")
            time.sleep(sleepTime)
        return None

    def get_jobs_data(self,
                      fullJobURI: str = None) -> None:
        """The loop to collect jobsID by given URI"""
        log.debug("Collecting jobs URI...")
        start_time: float = time.time()
        self.jobsData: dict = {}
        jobsDataDelta: dict = {}
        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()
        jobSearchPages = 3
        for jobSearchPage in range(1, jobSearchPages):
            log.debug(f"jobSearchPage - {jobSearchPage}")
            # get a soup for the search page
            soup = self.read_job_search_page(fullJobURI, jobSearchPage)
            # Break the cycle if no jobs found
            if soup is None:
                log.info(f"No search results for page {jobSearchPage}, "
                         + "stop collecting jobs for this search combo")
                break
            # rewrite number of pages with the first search result
            if jobSearchPage == 1:
                pages = soup.select_one('div .artdeco-pagination__page-state')
                if pages is None:
                    jobSearchPages = 1
                    log.debug("Only one page for this combo")
                else:
                    log.debug(str(pages))
                    pagesString = pages.string
                    pagesString = pagesString.strip()
                    index = pagesString.rfind(" ")
                    jobSearchPages = int(pagesString[index+1:])
                    log.debug(f"For this combo {str(jobSearchPages)} "
                              + "pages to take.")
            # get jobs delta
            jobsDataDelta = self.extract_data_from_search(jobSearchPage, soup)
            if jobsDataDelta is not None:
                self.jobsData = self.jobsData | jobsDataDelta
                log.debug(f"Jobs in jobsData: {len(self.jobsData)}")
        log.info(f"{(self.MAX_SEARCH_TIME-(time.time()-start_time)) // 60} minutes left in this search")
        return None

    def extract_data_from_search(self,
                                 page: int,
                                 soup: bs4.BeautifulSoup) -> dict | None:
        '''Deconstruct search page to usable dictionary'''
        log.info(f"Extract search page {page} data...")
        log.debug(f"Soup status: Size={str(sys.getsizeof(soup))}")
        jd: dict = {}  # result delta
        # collect all blocks with a job ID
        jobBlocks = soup.select('div[data-job-id]')
        log.debug(f"JobBlocks: {type(jobBlocks)} and len = {len(list(jobBlocks))}")
        if jobBlocks is None:
            log.debug(f"No job cards found on the page {page}")
            return None
        for block in jobBlocks:
            jobID: int = int(str(block['data-job-id']))
            # create dictionary for each job with ID as the key
            jd[jobID] = {}
            # extract data from the current card
            title = block.select_one('div .job-card-list__title')
            company = block.select_one('div ' 
                    +'.job-card-container__primary-description')
            metadata = block.select_one('li'
                    + ' .job-card-container__metadata-item')
            applyMethod = block.select_one('li'
                    + ' .job-card-container__apply-method')
            jd[jobID]['title'] = title.string
            jd[jobID]['company'] = company.string
            jd[jobID]['metadata'] = metadata.get_text()
            jd[jobID]['applyMethod'] : str = applyMethod.get_text()
            jd[jobID]['skipReason'] = None
            # clean data
            for key in jd:
                for p in jd[key]:
                    if jd[key][p] is not None:
                        jd[key][p] = str(jd[key][p]).strip()
        #            log.debug(f"{jd[key]} : {p} : {jd[key][p]}")
        log.info(f"{str(len(jd))} jobs collected on page {page}.")
        return jd

    def easy_apply(self) -> None:
        '''Apply to easy apply jobs'''
        log.info("Start easy apply...")
        # Check for data
        if self.jobsData is None:
            log.warning("No jobs sended to easy apply. Go back.")
            return None
        self.dump_current_jobs_to_log()
        # Extract JobID, ensure of correct apply method
        jobsID = [k for k in self.jobsData
                   if (self.jobsData[k]['applyMethod'] == 'Easy Apply')
                   and (self.jobsData[k]['skipReason'] is None)
                ]
        log.debug(f"{str(jobsID)} - {type(jobsID)}")
        # Check for zero list
        if len(jobsID) == 0:
            log.info("Zero Easy Apply jobs found, skip section.")
            return None
        # Let's loop applications
        for jobID in jobsID:
            self.apply_easy_job(jobID)
        self.write_to_file(self.jobsData)
        return None

    def apply_easy_job(self,
                       jobID : int = None) -> dict | None:
        '''Applying one EASY APPLY job'''
        log.info(f"Start applying to {self.jobsData[jobID]['title']}, {jobID}")
        if jobID is None:
            log.warning("No job sended to apply.")
            log.debug("The jobID is 'None'.")
            return None
        self.get_job_page(jobID)
        # get easy apply button
        button = self.get_easy_apply_button()
        if button is not False:
            log.info("Clicking the EASY apply button")
            button.click()
            time.sleep(3)
            self.fill_out_phone_number()
            result: bool = self.send_resume()
            if result is False:
                log.info(f"resume for {jobID} is not sended")
                self.browser.get_screenshot_as_png('screenshot_send_'
                                                    + str(jobID)
                                                    + '.png')
            log.debug(f"Button cycle is finished")
        else:
            log.info("The EASY APPLY button does not exist.")
            self.browser.get_screenshot_as_png(str('screenshot_ea_button_'
                                               + str(jobID)
                                               + '.png'))
            self.jobsData[jobID]['skipReason'] = "No 'Easy Apply' button"
        self.jobsData[jobID]['result'] = result
        return None

    def write_to_file(self) -> None:
        timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.filename, 'a') as f:
            for jobID in self.jobsData:
                toWrite: list = [timestamp,
                                 jobID,
                                 self.jobsData[jobID]['title'],
                                 self.jobsData[jobID]['company'],
                                 self.jobsData[jobID]['skipReason'],
                                 self.jobsData[jobID]['result']]
            writer = csv.writer(f)
            writer.writerow(toWrite)
        self.dump_current_jobs_to_log('write_to_file')
        return None


    def get_job_page(self, jobID):
        job: str = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def get_easy_apply_button(self):
        try:
            button = self.browser.find_elements("xpath",
                '//button[contains(@class, "jobs-apply-button")]'
            )
            EasyApplyButton = button[0]
        except Exception as e: 
            log.debug("Exception:",e)
            EasyApplyButton = False
        return EasyApplyButton

    def fill_out_phone_number(self):
        def is_present(button_locator) -> bool:
            return len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0
        # try:
        next_locater = (By.CSS_SELECTOR,
                        "button[aria-label='Continue to next step']")

        input_field = self.browser.find_element(By.CSS_SELECTOR, "input.artdeco-text-input--input[type='text']")

        if input_field:
            input_field.clear()
            input_field.send_keys(self.phone_number)
            time.sleep(random.uniform(4.5, 6.5))

            next_locater = (By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']")
            error_locator = (By.CSS_SELECTOR,
                             "p[data-test-form-element-error-message='true']")

            # Click Next or submitt button if possible
            button: None = None
            if is_present(next_locater):
                button: None = self.wait.until(EC.element_to_be_clickable(next_locater))

            if is_present(error_locator):
                for element in self.browser.find_elements(error_locator[0],
                                                            error_locator[1]):
                    text = element.text
                    if "Please enter a valid answer" in text:
                        button = None
                        self.browser.get_screenshot_as_png('screenshot_phone_number.png')
                        break
            if button:
                button.click()
                time.sleep(random.uniform(1.5, 2.5))
                # if i in (3, 4):
                #     submitted = True
                # if i != 2:
                #     break
        else:
            log.debug(f"Could not find phone number field")

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
            error_locator = (By.CSS_SELECTOR,
                             "p[data-test-form-element-error-message='true']")
            upload_locator = upload_locator = (By.CSS_SELECTOR, "button[aria-label='DOC, DOCX, PDF formats only (5 MB).']")
            follow_locator = (By.CSS_SELECTOR, "label[for='follow-company-checkbox']")

            submitted = False
            while True:

                # Upload Cover Letter if possible
                if is_present(upload_locator):

                    input_buttons = self.browser.find_elements(upload_locator[0],
                                                               upload_locator[1])
                    for input_button in input_buttons:
                        parent = input_button.find_element(By.XPATH, "..")
                        sibling = parent.find_element(By.XPATH, "preceding-sibling::*[1]")
                        grandparent = sibling.find_element(By.XPATH, "..")
                        for key in self.uploads.keys():
                            sibling_text = sibling.text
                            gparent_text = grandparent.text
                            if key.lower() in sibling_text.lower() or key in gparent_text.lower():
                                input_button.send_keys(self.uploads[key])

                    # input_button[0].send_keys(self.cover_letter_loctn)
                    time.sleep(random.uniform(4.5, 6.5))

                # Click Next or submitt button if possible
                button: None = None
                buttons: list = [next_locater, review_locater, follow_locator,
                           submit_locater, submit_application_locator]
                for i, button_locator in enumerate(buttons):
                    if is_present(button_locator):
                        button: None = self.wait.until(EC.element_to_be_clickable(button_locator))

                    if is_present(error_locator):
                        for element in self.browser.find_elements(error_locator[0],
                                                                  error_locator[1]):
                            text = element.text
                            if "Please enter a valid answer" in text:
                                button = None
                                break
                    if button:
                        button.click()
                        time.sleep(random.uniform(1.5, 2.5))
                        if i in (3, 4):
                            submitted = True
                        if i != 2:
                            break
                if button == None:
                    log.info("Could not complete submission")
                    break
                elif submitted:
                    log.info("Application Submitted")
                    break

            time.sleep(random.uniform(1.5, 2.5))

        except Exception as e:
            log.info(e)
            log.info("cannot apply to this job")
            raise (e)

        return submitted

    def load_page(self, sleep=1):
        log.debug("Load page like human mode...")
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 200
            time.sleep(sleep)
        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep * 3)
        return None
    
    def load_job_cards(self) -> None:
        '''Need to scroll jobcards column to load them all'''
        log.debug("Load job cards...")
        scriptScrollDiv: str = str("document.querySelector"
                                   + "('.jobs-search-results-list')"
                                   + ".scroll(0, 1000, 'smooth');")
        for p in range(0, 5):
            scriptScrollDiv: str = str((f"document.querySelector")
                                   + (f"('.jobs-search-results-list')")
                                   + (f".scroll({str(1000*p)}, ")
                                   + (f"{str(1000*(p+1))}, ")
                                   + "'smooth');")
            self.browser.execute_script(scriptScrollDiv)
            time.sleep(2)
        return None

    def avoid_lock(self) -> None:
        '''Imitate human on page'''
        x, _ = pyautogui.position()
        pyautogui.moveTo(x + 200, pyautogui.position().y, duration=1.0)
        pyautogui.moveTo(x, pyautogui.position().y, duration=0.5)
        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(0.5)
        pyautogui.press('esc')
        log.debug("Lock avoided.")
        return None

    def read_job_search_page(self,
                           fullJobURI: str = None,
                           jobPage: int = 1) -> bs4.BeautifulSoup | None:
        """Get current search page and save it to soup object
        """
        log.debug("Start reading search page...")
        jobPageURI: str = ''
        # Find page URI
        if jobPage != 1:
            jobPageURI = str ("&start="
                              + str((jobPage-1)*25))
        self.browser.get("https://www.linkedin.com/jobs/search/?"
                         + fullJobURI
                         + jobPageURI)
        self.avoid_lock()
        # Check 'No jobs found'
        if ('No matching jobs' in self.browser.page_source):
            log.info("No jobs found for this page")
            return None
        self.load_page()
        self.load_job_cards()
        # Get the column with list of jobs
        jobCardDiv = self.browser.find_element(By.CSS_SELECTOR,
                                               '.jobs-search-results-list')
        htmlChunk = jobCardDiv.get_attribute('innerHTML')
        # Store the column in soup lxml structure
        soup = bs4.BeautifulSoup(htmlChunk, "lxml")
        if soup is None:
            log.debug(f"Soup is not created.")
            return None
        log.debug(f"Soup is created.")
        # TODO check full jobcard column load
        return soup

    def shutdown(self) -> None:
        self.browser.close()
        self.browser.quit()
        log.debug("Browser is closed.")
        log.info("Bye!")
        return None
    
    def dump_current_jobs_to_log(self,
                                 context: str = 'undefined') -> None:
        '''For test / debug purpose. Dumps current jobs dictionary
        in logs in readable format
        '''
        if self.jobsData is None:
            log.warning(f'No jobs to dump into logs for {context}')
            return None
        log.debug(f"*** Jobs right now for {context}")
        for key in self.jobsData:
            log.debug(f"{key}:{type(self.jobsData[key])} collected data:")
            for p in self.jobsData[key]:
                log.debug(f"{p}:{type(self.jobsData[key][p])} {(self.jobsData[key][p])}")
        log.debug(f"*** End of jobs for {context}")
        return None

def read_configuration(configFile: str = 'config.yaml') -> tuple[dict, dict]:
    """
    Unpack the configuration and check the data format. Username and password
    are separated from other parameters for security reasons. 
    """
    log.info(f"Reading configuration from {configFile} ...")
    def check_missing_parameters(parametersToCheck: dict = None,
                                 keysToCheck: list = None) -> None:
        """Check and add missing parameters if something wrong
        with a config file
        """
        p = parametersToCheck
        if keysToCheck is None:
            keysToCheck = ['username',
                           'password',
                           'phoneNumber',
                           'positions',
                           'locations',
                           'uploads',
                           'outputFilename',
                           'blackListCompanies',
                           'blackListTitles',
                           'jobListFilterKeys']
        for key in keysToCheck:
            if key not in p:
                p[key] = None
                log.debug(f"Check: added missing parameter {key}")
        
        for key in list(p.keys()):
            if key not in keysToCheck:
               log.warning(f"Check: unknown parameter {key}") 

        log.debug("Checked and added parameters: " + str(p.keys()))
        return p

    def check_input_data(parametersToCheck: dict = None,
                         keysToCheck: list = None) -> bool:
        """Check the parameters data completion."""
        p = parametersToCheck
        if keysToCheck is None:
            keysToCheck = ['username',
                           'password',
                           'locations',
                           'positions',
                           'phoneNumber']
        for key in keysToCheck:
            try:
                assert key in p
            except AssertionError as err:
                log.exception("Parameter '" 
                              + key
                              + "' is missing")
                raise err
            try:
                assert p[key] is not None
            except AssertionError as err:
                log.exception(f"Parameter '"
                              + key
                              + "' is None")
                raise err
        try:
            assert len(p['positions'])*len(p['locations']) < 500
        except AssertionError as err:
            log.exception("Too many positions and/or locations")
            raise err
        log.debug("Input data checked for completion.")
        return p

    def removeNone(userParameters: dict = None,
                    keysToClean: list = None) -> dict:
        """
        Remove None from some lists in configuration.
        Just to avoid this check later.
        """
        p = userParameters
        if keysToClean is None:
            keysToClean: list = ['positions',
                                 'locations',
                                 'blackListCompanies',
                                 'blackListTitles']
        for key in keysToClean:
            a_list = p[key]
            if a_list is not None:
                a_list = list(set(a_list))
                log.debug("key, a_list: " + key + ", " + str(a_list))
                try:
                    a_list.remove(None)
                    log.debug(f"Removed 'None' from {key}")
                except:
                    log.debug(f"No 'None' in {key}")
            else:
                log.debug(f"The {key} is None, skipped")
            if not a_list:
                a_list = None
                log.debug(f"{key} is empty and None")
            p[key] = a_list
        log.debug(f"Parameters after none_remover: {p}")
        return p

    with open(configFile, 'r') as stream:
        try:
            userParameters: dict = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            log.error(exc)
            raise exc
    
    p = userParameters
    log.debug(f"Parameters dirty: {p.keys()}")
    p = check_input_data(p, None)
    p = check_missing_parameters(p, None)

    if ('uploads') in p and type(p['uploads']) == list:
        raise Exception("Uploads read from the config file appear to be in list format" +
                        " while should be dict. Try removing '-' from line containing" +
                        " filename & path")

    loginInformation={'username' : p['username'],
                      'password' : p['password'],}

    del p['username']
    del p['password']

    log.debug(f"Personal information is separated.")

    p = removeNone(p)
 
    if (('outputFilename' not in p)
        or (p['outputFilename'] is not type(str))):
        p['outputFilename'] = 'output.csv'

    log.debug(f"Cleared parameters: {p}")
    return userParameters, loginInformation

def parse_command_line_parameters(clParameters: list = None) -> dict:
    """Define input parameters for command string.
    Check config file for existing.
    """
    log.info("Checking command prompt parameters...")
    parser = argparse.ArgumentParser(prog="LinkedIn Easy Apply Bot",
                description="Some parameters to start with command line",
                usage="The bot options:",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config",
                        type=str,
                        default="config.yaml",
                        help="configuration file, YAML formatted")
    parser.add_argument("--forcelogin",
                        action='store_true',
                        help="force login no matter cookies")
    parser.add_argument("--nobot",
                        action='store_true',
                        help="do all setup but not start the bot")
    parser.add_argument("--fastapply",
                        type=str,
                        default=None,
                        help="fast apply the job by id without apply loop")
    args = parser.parse_args(clParameters)
    log.debug(f"Command string parameters: {str(vars(args))}")
    try:
        assert os.path.isfile(args.config)
    except AssertionError as err:
        log.exception(f"Config file {args.config} doesn't exist")
        raise err
    log.debug(f"Config file {args.config} is exist.")
    if args.fastapply is not None:
        log.debug(f"Fast apply for {args.fastapply} requested")
    return vars(args)

def login_to_LinkedIn(login: dict = None,
                      config: str = None,
                      browserOptions = None,
                      forceLogin: bool = 0) -> dict | None:
    """Login to linkedIn and collect cookies
    if cookies aren't exist or expired.
    Otherwise, return stored cookies.
    """
    log.info('Login to LinkedIn...')
    cookiesFileName = config + ".cookies"

    def check_actual_cookies(cookiesFileName: str = None) -> bool:
        '''Define filename for cookies, try to open it
        and check cookies actuality
        '''
        log.debug("Checking cookies...")
        cookies: list = None
        if os.path.exists(cookiesFileName):
            log.debug(f"Found the cookie file {cookiesFileName}, reading...")
            try:
                cookies = pickle.load(open(cookiesFileName, "rb"))
                log.debug(f"Cookies loaded")
            except:
                log.error("Something wrong withthe cookie file")
                raise
            loginExpires = [cookie['expiry'] for cookie in cookies
                            if cookie['name'] == 'li_at'][0]
            if datetime.fromtimestamp(loginExpires) <= datetime.today():
                log.warning("Auth cookie expiried, need to login.")
                cookies = None
            else:
                log.info("Auth cookie will expire "
                          + str(datetime.fromtimestamp(loginExpires))
                          + ", no need to login")
        else:
            log.debug(f"The cookie file {cookiesFileName} is not found.")
            cookies = None
        return cookies

    def login_in_browser(FileName: str = None,
                         browserOptions = None,
                         login: dict = None) -> list:
        '''Log in by browser and store cookies into the file,
        return actual cookies.
        '''
        log.info("Logging in.....Please wait :)  ")
        cookies: list = None
        driver = webdriver.Chrome(service =
                                  ChromeService(ChromeDriverManager().install()),
                                  options=browserOptions)
        driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            user_field = driver.find_element("id","username")
            pw_field = driver.find_element("id","password")
            login_button = driver.find_element("xpath",
                        '//*[@id="organic-div"]/form/div[3]/button')
            user_field.send_keys(login['username'])
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(login['password'])
            time.sleep(2)
            login_button.click()
            time.sleep(3)
        except TimeoutException as err:
            log.info("TimeoutException! Username/password field"
                     + "or login button not found")
            raise err
        # TODO check login result not by timeout
        cookies = driver.get_cookies()
        pickle.dump(cookies, open(FileName, "wb"))
        driver.close()
        driver.quit()
        return cookies
    
    if (forceLogin and os.path.exists(cookiesFileName)):
        log.info("Force Login - cookies are deleted")
        os.remove(cookiesFileName)
    cookies = check_actual_cookies(cookiesFileName)
    if cookies is None:
        cookies = login_in_browser(cookiesFileName,
                                   browserOptions,
                                   login)
    return cookies

def main() -> None:
    userParameters: dict = None
    login: dict = None
    configCommandString: dict = None
    cookies: list = None
    browserOptions = get_browser_options()

    configCommandString = parse_command_line_parameters(sys.argv[1:])
    userParameters, login = read_configuration(configCommandString['config'])


    cookies = login_to_LinkedIn(login,
                                configCommandString['config'],
                                browserOptions,
                                configCommandString['forcelogin'])

    log.debug(f"Output filename: {userParameters['outputFilename']}")

    if configCommandString['nobot']:
        log.info("Launched with --nobot parameter. Forced exit.")
        exit()

    bot = EasyApplyBot(userParameters, cookies)

    if configCommandString['fastapply'] is None:
        bot.apply_to_positions(userParameters['positions'],
                               userParameters['locations'],
                               userParameters['jobListFilterKeys'])
    else:
        log.info(f"Fast apply for {configCommandString['fastapply']} requested")
        fastApplyJob: dict = {int(configCommandString['fastapply']) :
                                {'title' : 'Fast Apply Forced Title',
                                 'company' : 'Fast Apply Forced Company',
                                 'metadata' : 'Fast Apply Forced Metadata',
                                 'applyMethod' : 'Easy Apply'
                                }
                              }
        bot.apply_easy_job(fastApplyJob)
        bot.write_to_file()
        log.info(f"Forced easy apply cycle for"
                 + f" {configCommandString['fastapply']} finished.")

    bot.shutdown()
    return None

if __name__ == '__main__':
    main()
