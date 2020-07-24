import csv
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta

import pandas as pd
import pyautogui
import win32com.client as comctl
import yaml
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

wsh = comctl.Dispatch("WScript.Shell")

log = logging.getLogger(__name__)
driver = webdriver.Chrome(ChromeDriverManager().install())


# pyinstaller --onefile --windowed --icon=app.ico easyapplybot.py

class EasyApplyBot:
	MAX_SEARCH_TIME = 30 * 60

	def __init__(self,
				 username,
				 password,
				 uploads={},
				 filename='output.csv',
				 blacklist=[]):

		log.info("Welcome to Easy Apply Bot\n")
		dirpath = os.getcwd()
		log.info("current directory is : " + dirpath)

		self.uploads = uploads
		past_ids = self.get_appliedIDs(filename)
		self.appliedJobIDs = past_ids if past_ids != None else []
		self.filename = filename
		self.options = self.browser_options()
		self.browser = driver
		self.wait = WebDriverWait(self.browser, 30)
		self.blacklist = blacklist
		self.start_linkedin(username, password)


	def get_appliedIDs(self, filename):
		try:
			df = pd.read_csv(filename,
							header=None,
							names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
							lineterminator='\n',
							encoding='utf-8')

			df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S.%f")
			df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
			jobIDs = list(df.jobID)
			print(f"{len(jobIDs)} jobIDs found")
			return jobIDs
		except Exception as e:
			print(str(e) + "   jobIDs could not be loaded from CSV {}".format(filename))
			return None


	def browser_options(self):
		options = Options()
		options.add_argument("--start-maximized")
		options.add_argument("--ignore-certificate-errors")
		options.add_argument('--no-sandbox')
		options.add_argument("--disable-extensions")

		#Disable webdriver flags or you will be easily detectable
		options.add_argument("--disable-blink-features")
		options.add_argument("--disable-blink-features=AutomationControlled")
		return options

	def start_linkedin(self,username,password):
		log.info("Logging in.....Please wait :)  ")
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

	def fill_data(self):
		self.browser.set_window_size(0, 0)
		self.browser.set_window_position(2000, 2000)


	def start_apply(self, positions, locations):
		start = time.time()
		self.fill_data()

		combos = []
		while len(combos) < len(positions) * len(locations):
			position = positions[random.randint(0, len(positions) - 1)]
			location = locations[random.randint(0, len(locations) - 1)]
			combo = (position, location)
			if combo not in combos:
				combos.append(combo)
				log.info(f"Applying to {position}: {location}")
				location = "&location=" + location
				self.applications_loop(position, location)
			if len(combos) > 20:
				break
		self.finish_apply()

	def applications_loop(self, position, location):

		count_application = 0
		count_job = 0
		jobs_per_page = 0
		start_time = time.time()


		log.info("Looking for jobs.. Please wait..")

		self.browser.set_window_position(0, 0)
		self.browser.maximize_window()
		self.browser, _ = self.next_jobs_page(position, location, jobs_per_page)
		log.info("Looking for jobs.. Please wait..")

		while time.time() - start_time < self.MAX_SEARCH_TIME:
			log.warning(f"{(self.MAX_SEARCH_TIME - (time.time() - start_time))//60} minutes left in this search")

			# sleep to make sure everything loads, add random to make us look human.
			randoTime = random.uniform(3.5, 6.9)
			log.info("Sleeping for %s", randoTime)
			time.sleep(randoTime)
			self.load_page(sleep=1)

			# get job links
			links = self.browser.find_elements_by_xpath(
					'//div[@data-job-id]'
					)

			if len(links) == 0:
				break

			# get job ID of each job link
			IDs = []
			for link in links:
				children = link.find_elements_by_xpath(
					'.//a[@data-control-name]'
					)
				for child in children:
					if child.text not in self.blacklist:
						temp = link.get_attribute("data-job-id")
						jobID = temp.split(":")[-1]
						IDs.append(int(jobID))
			IDs = set(IDs)

			# remove already applied jobs
			before = len(IDs)
			jobIDs = [x for x in IDs if x not in self.appliedJobIDs]
			after = len(jobIDs)

			if len(jobIDs) == 0 and len(IDs) > 24:
				jobs_per_page = jobs_per_page + 25
				count_job = 0
				# TODO avoid lock function disabled during debugging.
				#  Turn back on with major release and running while sleeping.
				#self.avoid_lock()
				self.browser, jobs_per_page = self.next_jobs_page(position,
																	location,
																	jobs_per_page)
			# loop over IDs to apply
			for i, jobID in enumerate(jobIDs):
				count_job += 1
				tabs = len(self.browser.window_handles)
				job, jobPage = self.get_job_page(jobID)

				# get easy apply button
				button = self.get_easy_apply_button()
				if button :
					log.info("It appears that the apply button is considered an EASY apply")
					#TODO Need to confirm that its an easy apply button by checking the URL is still linkedin URL and not a redirect
					string_easy = "* has Easy Apply Button"
					log.info("Clicking the EASY apply button")
					button.click()
					log.info("Wait for page to load")
					time.sleep(3)
					log.info("Checking to see if the current URL is the same as the job URL")
					log.info(self.browser.current_url)
					log.info(job)
					newTabs = len(self.browser.window_handles)
					if self.browser.current_url == job and (newTabs == tabs):
						log.info("The URLs match; Attempting to apply")
						result = self.send_resume()
						count_application += 1
					else:
						log.info("The URLs do not match")
						string_easy = "* Doesn't have Easy Apply Button"
						result = False
				else:
					log.info("The button does not exist.")
					string_easy = "* Doesn't have Easy Apply Button"
					result = False

				position_number = str(count_job + jobs_per_page)
				log.info(f"\nSuccess?: {result} \n Position {position_number}\n {self.browser.title} \n {string_easy} \n {job}")

				self.write_to_file(button, jobID, self.browser.title, result)

				# sleep every 20 applications
				if count_application != 0  and count_application % 20 == 0:
					sleepTime = random.randint(500, 900)
					log.info(f'********count_application: {count_application}************\n\n')
					log.info(f"Time for a nap - see you in:{int(sleepTime/60)} min")
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
			if len(jobIDs) == 0 or i == (len(jobIDs) - 1):
				break

	def write_to_file(self, button, jobID, browserTitle, result):
		def re_extract(text, pattern):
			target = re.search(pattern, text)
			if target:
				target = target.group(1)
			return target

		timestamp = datetime.now()
		attempted = False if button == False else True
		job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
		company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)" )

		toWrite = [timestamp, jobID, job, company, attempted, result]
		with open(self.filename,'a') as f:
			writer = csv.writer(f)
			writer.writerow(toWrite)


	def get_job_page(self, jobID):

		job = 'https://www.linkedin.com/jobs/view/'+ str(jobID) + '/'

		self.browser.get(job)
		self.job_page = self.load_page(sleep=0.5)
		return job, self.job_page


	def get_easy_apply_button(self):
		try :
			button = self.browser.find_elements_by_xpath(
						'//button[contains(@class, "jobs-apply")]/span[1]'
						)

			EasyApplyButton = button [0]
		except :
			EasyApplyButton = False

		return EasyApplyButton


	def is_jsonable(self, x):
		try:
			json.dumps(x)
			return True
		except:
			return False

	def send_resume(self):
		def is_present(button_locator):
			return (len(self.browser.find_elements(button_locator[0], button_locator[1])) > 0)

		try:

			time.sleep(random.uniform(2.2, 4.3))
			log.info("Attempting to apply")
			#TODO These locators are not future proof. These labels could easily change.
			# Ideally we would search for contained text;
			# was unable to get it to work using XPATH and searching for contained text
			upload_locator = (By.CSS_SELECTOR, "label[aria-label='DOC, DOCX, PDF formats only (2 MB).']")
			next_locator = (By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
			review_locator = (By.CSS_SELECTOR, "button[aria-label='Review your application']")
			submit_locator = (By.CSS_SELECTOR, "button[aria-label='Submit application']")
			submit_application_locator = (By.CSS_SELECTOR, "button[aria-label='Submit application']")
			error_locator = (By.CSS_SELECTOR, "p[data-test-form-element-error-message='true']")
			cover_letter = (By.CSS_SELECTOR, "input[name='file']")

			question_locator = (By.XPATH, ".//div[@class='jobs-easy-apply-form-section__grouping']")
			yes_locator = (By.XPATH, ".//input[@value='Yes']")
			no_locator = (By.XPATH, ".//input[@value='No']")
			textInput_locator = (By.XPATH, ".//input[@type='text']")


			submitted = False
			attemptQuestions = True
			while not submitted:
				button = None

				# Upload  if possible

				#TODO Should check if there is already a resume that is saved from the last time the application was attempted.
				# If so, then remove and re upload it in case there is new version.
				if is_present(upload_locator):
					log.info("Resume upload option available. Attempting to upload.")
					input_buttons = self.browser.find_elements(cover_letter[0],
															 cover_letter[1])
					for input_button in input_buttons:
						parent = input_button.find_element(By.XPATH, "..")
						sibling = parent.find_element(By.XPATH, "preceding-sibling::*")
						grandparent = sibling.find_element(By.XPATH, "..")
						for key in self.uploads.keys():
							if key in sibling.text or key in grandparent.text:
								input_button.send_keys(self.uploads[key])

				for i, button_locator in enumerate(
						[upload_locator, next_locator, review_locator, submit_locator, submit_application_locator]):

					#Sleep every iteration so that the bot is harded to detect.
					time.sleep(random.uniform(2.2, 4.3))

					log.info("Searching for button locator: %s", str(button_locator))
					if is_present(button_locator):
						log.info("button found with this locator: %s", str(button_locator))
						try:
							button = self.wait.until(EC.element_to_be_clickable(button_locator))
						except TimeoutException:
							log.exception("Timed out waiting for button %s ", button_locator)
							continue
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
								if is_present(question_locator) and attemptQuestions:
									questionSections = self.browser.find_elements(question_locator[0], question_locator[1])
									for questionElement in questionSections:
										try:
											log.info("Found test element %s", questionElement)
											text = questionElement.text
											log.warning("Question Text: %s", text)
											#assuming this question is asking if I am authorized to work in the US
											if ("Are you" in text and "authorized" in text) or ("Have You" in text and "education" in text):
												#Be sure to find the child element of the current test question section
												yesRadio = questionElement.find_element(By.XPATH, yes_locator[1])
												time.sleep(1)
												log.info("Attempting to click the radio button for %s", yes_locator)
												self.browser.execute_script("arguments[0].click()", yesRadio)
												log.info("Clicked the radio button %s", yes_locator)

											#assuming this question is asking if I require sponsorship
											elif "require" in text and "sponsorship" in text:
												noRadio = questionElement.find_element(By.XPATH, no_locator[1])
												time.sleep(1)
												log.info("Attempting to click the radio button for %s", no_locator)
												self.browser.execute_script("arguments[0].click()", noRadio)
												log.info("Clicked the radio button %s", no_locator)

											# assuming this question is asking if I have a Bachelor's degree
											elif (("You have" in text) or ("Have you" in text)) and "Bachelor's" in text:
												yesRadio = questionElement.find_element(By.XPATH, yes_locator[1])
												time.sleep(1)
												log.info("Attempting to click the radio button for %s", yes_locator)
												self.browser.execute_script("arguments[0].click()", yesRadio)
												log.info("Clicked the radio button %s", yes_locator)

											# assuming this question is asking if I have a Master's degree
											elif (("You have" in text) or ("Have you" in text)) and "Master's" in text:
												yesRadio = questionElement.find_element(By.XPATH, yes_locator[1])
												time.sleep(1)
												log.info("Attempting to click the radio button for %s", yes_locator)
												self.browser.execute_script("arguments[0].click()", yesRadio)
												log.info("Clicked the radio button %s", yes_locator)

											#TODO Issue where if there are multiple lines that ask for number of years experience then years experience will be written twice
											#TODO Need to add a configuration file with all the answer for these questions versus having them hardcoded.
											#Some questions are asking how many years of experience you have in a specific skill
											#Automatically put the number of years that I have worked.
											elif "How many years" in text and "experience" in text:
												textField = questionElement.find_element(By.XPATH, textInput_locator[1])
												time.sleep(1)
												log.info("Attempting to click the text field for %s", textInput_locator)
												self.browser.execute_script("arguments[0].click()", textField)
												log.info("Clicked the text field %s", textInput_locator)
												time.sleep(1)
												log.info("Attempting to send keys to the text field %s", textInput_locator)
												textField.send_keys("10")
												log.info("Sent keys to the text field %s", textInput_locator)

											#This should be updated to match the language you speak.
											elif "Do you" in text and "speak" in text:
												if "English" in text:
													yesRadio = questionElement.find_element(By.XPATH, yes_locator[1])
													time.sleep(1)
													log.info("Attempting to click the radio button for %s", yes_locator)
													self.browser.execute_script("arguments[0].click()", yesRadio)
													log.info("Clicked the radio button %s", yes_locator)
												#if not english then say no.
												else:
													noRadio = questionElement.find_element(By.XPATH, no_locator[1])
													time.sleep(1)
													log.info("Attempting to click the radio button for %s", no_locator)
													self.browser.execute_script("arguments[0].click()", noRadio)
													log.info("Clicked the radio button %s", no_locator)

											else:
												log.warning("Unable to find question in my tiny database")

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
						if button_locator == upload_locator:
							log.info("Uploading resume now")

							time.sleep(random.uniform(2.2, 4.3))
							driver.execute_script("arguments[0].click()", button)

							#TODO This can only handle Chrome right now. Firefox or other browsers will need to be handled separately
							# Chrome opens the file browser window with the title "Open"
							status = wsh.AppActivate("Open")
							log.debug("Able to find file browser dialog: %s", status)
							#Must sleep around sending the resume location so it has time to accept all keys submitted
							time.sleep(1)
							wsh.SendKeys(str(self.resume_loctn))
							time.sleep(1)
							wsh.SendKeys("{ENTER}")
							log.info("Just finished using button %s ", button_locator)

						else:
							try:
								log.info("attempting to click button: %s", str(button_locator))
								response = button.click()
								if (button_locator == submit_locator) or (button_locator == submit_application_locator):
									log.info("Clicked the submit button.")
									submitted = True
									return submitted
							except EC.StaleElementReferenceException:
								log.warning("Button was stale. Couldnt click")
					else:
						if (button_locator == submit_locator) or (button_locator == submit_application_locator):
							log.warning("Unable to submit. It appears none of the buttons were found.")
							break



			# After submitting the application, a dialog shows up, we need to close this dialog
			close_button_locator = (By.CSS_SELECTOR, "button[aria-label='Dismiss']")
			if is_present(close_button_locator):
				close_button = self.wait.until(EC.element_to_be_clickable(close_button_locator))
				close_button.click()

		except Exception as e:
			log.info(e)
			log.warning("cannot apply to this job")
			raise(e)

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
			position + location + "&start="+str(jobs_per_page))
		#self.avoid_lock()
		self.load_page()
		return (self.browser, jobs_per_page)


	def finish_apply(self):
		self.browser.close()


def setupLogger():
	dt = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")

	if not os.path.isdir('./logs'):
		os.mkdir('./logs')

	# TODO need to check if there is a log dir available or not
	logging.basicConfig(filename=('./logs/' + str(dt)+'applyJobs.log'), filemode='w', format='%(asctime)s::%(name)s::%(levelname)s::%(message)s', datefmt='./logs/%d-%b-%y %H:%M:%S')
	log.setLevel(logging.DEBUG)
	c_handler = logging.StreamHandler()
	c_handler.setLevel(logging.DEBUG)
	c_format = logging.Formatter('%(asctime)s::%(name)s::%(levelname)s::%(lineno)d- %(message)s')
	c_handler.setFormatter(c_format)
	log.addHandler(c_handler)


if __name__ == '__main__':

	setupLogger()

	with open("config.yaml", 'r') as stream:
		try:
			parameters = yaml.safe_load(stream)
		except yaml.YAMLError as exc:
			raise exc

	assert len(parameters['positions']) > 0
	assert len(parameters['locations']) > 0
	assert parameters['username'] is not None
	assert parameters['password'] is not None


	print(parameters)

	output_filename = [f for f in parameters.get('output_filename', ['output.csv']) if f != None]
	output_filename = output_filename[0] if len(output_filename) > 0 else 'output.csv'
	blacklist = parameters.get('blacklist', [])
	uploads = parameters.get('uploads', {})
	for key in uploads.keys():
		assert uploads[key] != None


	bot = EasyApplyBot(parameters['username'],
						parameters['password'],
						uploads=uploads,
						filename=output_filename,
						blacklist=blacklist
						)

	locations = [l for l in parameters['locations'] if l != None]
	positions = [p for p in parameters['positions'] if p != None]
	bot.start_apply(positions, locations)
