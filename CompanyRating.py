import time
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.support import wait


def GetCompanyRating(companyname):
    try:

        url = "https://www.ambitionbox.com/search?CompanyName=" + \
            str(companyname)+"&Type=CompanyReview"

        payload = {}
        headers = {
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'Cookie': '_t_ds=17ab4b2e1641887869-3117ab4b2e-017ab4b2e; PHPSESSID=04f9522a6710989af9d763482d91d89e'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        # print(response.text)

        soup = BeautifulSoup(response.text)
        time.sleep(3)
        ratingwrapper = soup.find("div", {"class": "rating-wrapper"})
        print(ratingwrapper.text)
        companydetails = soup.find("div", {"class": "content"})
        print(companydetails.text)
        return ratingwrapper
    except:
        return ''
# GetCompanyRating("Coforge")
