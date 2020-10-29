from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from time import sleep
import boto3
import datetime
import time
import operator
import shutil
import os
import stat
from pyvirtualdisplay import Display
import schedule


# Variables
schedule_dict = {}
sorted_schedule_dict = {}
sms_message = ""
weekend_sms_message = ""
cutoff_time = datetime.time(16,0,0)

# Set up SMS Client
client = boto3.client(
    "sns",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=access_key,
    region_name="us-east-1"
)

# Receives URL, returns HTML
def get_raw_html(url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    display = Display(visible=0, size=(800, 800))
    display.start()
    browser = webdriver.Chrome("/app/chromedriver.exe",chrome_options=chrome_options)
    #browser = webdriver.Chrome("C:/Users/JKOLPAK/Downloads/chromedriver_win32/chromedriver.exe")
    browser.get(url)
    sleep(10)
    raw_html = browser.execute_script("return document.body.innerHTML")
    browser.quit()
    return raw_html

# Send SMS
def send_mesage(phone_number, message):
    client.publish(
        PhoneNumber=phone_number,
        Message=message
    )

# Returns a schedule dictionary (event name: event time) and the current date
def get_schedule_and_date():
    raw_html = get_raw_html("https://www.chicagoathleticclubs.com/locations/lincoln-park/")
    html = BeautifulSoup(raw_html, 'html.parser')
    schedule = html.find_all("li", {"class": "event"})
    date = html.find("h3", {"class": "agenda__date"}).get_text()


    # Create dictionary where key = event name, value = event time
    for event in schedule:
        print(event)
        if event_time is not None:
            event_time = event.time.get_text()
        else:
            event_time = 'N/A'
        event_time = datetime.datetime.strptime(event_time, '%I:%M%p').time()
        event_name = event.find('div',{"class":"event__body"}).h5.get_text()
        schedule_dict[event_name] = event_time

    # Sort dictionary by event time
    sorted_schedule_dict = sorted(schedule_dict.items(), key=operator.itemgetter(1))
    return sorted_schedule_dict, date

# Iterate over sorted dictionary and build SMS message string
def main():
    sms_message = ""
    print("Beginning web scraping.")
    schedule_and_date = get_schedule_and_date()
    sorted_schedule_dict = schedule_and_date[0]
    date = schedule_and_date[1]
    sms_message = sms_message + "Workout classes for " + date + "\n"

    date = datetime.datetime.strptime(date, '%A, %B %d, %Y')
    weekday = date.weekday()

    # TO DO: Fix weekday vs. weekend logic
    for event in sorted_schedule_dict:
        event_name = event[0]
        event_time = event[1]

        sms_message = sms_message + str(event[1].strftime('%I:%M%p')) + ": " + event_name + "\n"

    print(sms_message)
    print("Sending SMS.")
    send_mesage("+12244064823",sms_message)

print("Starting application.")
main()
schedule.every().day.at("7:00").do(main)


for i in range (0,3):
    while True:
        try:
            schedule.run_pending()
        except:
            continue
        break
