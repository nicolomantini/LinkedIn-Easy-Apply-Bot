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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from application import application

wsh = comctl.Dispatch("WScript.Shell")

log = logging.getLogger(__name__)
driver = webdriver.Chrome(ChromeDriverManager().install())


# pyinstaller --onefile --windowed --icon=app.ico easyapplybot.py

class EasyApplyBot:
	MAX_SEARCH_TIME = 90 * 60

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

			log.info("Number of total IDs in search %s; Number of total jobs we can apply to %s;", len(IDs), len(jobIDs))

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
						result = self.apply(job)
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
			#if len(jobIDs) == 0 or i == (len(jobIDs) - 1):
			#	log.warning("We have run out of Jobs to apply to. Stopping applying early")
			#	break
		log.warning("We have run out of time applying for jobs. You will need to adjust the number of minutes next time")

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

		toWrite = [timestamp, jobID, job, company, attempted, result, ('https://www.linkedin.com/jobs/view/'+ str(jobID) + '/')]
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

	def apply(self, job):
		app = application.Application(job, self.browser)
		while(app.state != app.States.SUBMITTED and app.state != app.States.SUSPENDED):
			log.info("State: %s", app.state)
			app.next()

		if app.state == app.States.SUSPENDED:
			del app
			return False
		elif app.state == app.States.SUBMITTED:
			del app
			return True
		else:
			del app
			return False



		log.info("Exited the application pop up")

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
	log.setLevel(logging.INFO)
	c_handler = logging.StreamHandler()
	c_handler.setLevel(logging.INFO)
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

	# Prepare header for CSV file
	if not os.path.exists('./'+output_filename):
		toWrite = ['timestamp', 'jobID', 'job', 'company', 'attempted', 'success', 'joburl']
		with open(output_filename, 'a') as f:
			writer = csv.writer(f)
			writer.writerow(toWrite)

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
