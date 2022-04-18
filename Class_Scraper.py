import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from twilio.rest import Client
from webdriver_manager.chrome import ChromeDriverManager

#YOU SHOULD GO TO MY WEBSITE
#https://www.grantreidy.com

# user's username and password
usernameStr = '{username}' # gatech sso username wihtout brackets
passwordStr = '{password}' # gatech password without brackets
phone = '{your_phone_num}' # your phone number with country code e.x. +14041234567
# I'm not stealing ur passwords and shit I promise

# ENSURE YOU HAVE DUO AUTO-PUSH ENABLED OTHERWISE YOU WILL NOT BE ABLE TO VERIFY, SEE BELOW
# https://help.duo.com/s/article/2236?language=en_US

# registration lookup parameters as appear in OSCAR
regSem = 'Fall 2022' # Semester of Registration in exact format (e.x. 'Spring 2023')
subj = 'Physics' # exact format as appears on the 'Lookup' Section in OSCAR
classNum = '2211' # class 4-digit number
secCode = 'N' # Section Code

# twilio SMS API keys and phone number
# just google how to do this
account_sid = '{API_SID}'
auth_token = '{API_AUTH}'
twilio_phone = '' #twilio phone number with country code e.x. +14041234567

# open debugging session on localhost: 9222

# False if only noftify don't auto register for class
register = False

# DONT MESS WITH SHIT PAST HERE
# -------------------------------------------------------------------

# twilio oauth
client = Client(account_sid, auth_token)

def parse_to_list(input):
        list = []
        for i in range(len(input)):
            try:
                list.append(str(input[i].text))
            except:
                continue
        return list

def send_notification(s):
    message = client.messages .create(
        body =  s,
        from_ = twilio_phone,
        to = phone) 
    return message.sid

# random params
maxRange = 100 # assumes that there are no more than 100 instances of a specific class

# install and manage chrome driver
config = Options()
config.add_argument("--headless")
config.add_argument('--remote-debugging-port=9222')
driver = webdriver.Chrome(ChromeDriverManager().install(), options= config)

# load gatech sso
driver.get('https://sso.sis.gatech.edu/ssomanager/c/SSB')

# parse and pass in username
username = driver.find_element(by=By.ID, value='username')
username.send_keys(usernameStr)

# parse and pass in password
password = driver.find_element(by=By.ID, value='password')
password.send_keys(passwordStr)

# parse login location
login = driver.find_element(by=By.NAME, value='submit')
login.click()

# wait for DUO 2FA
# Duo 2FA times out afer 10 seconds 
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, 'submenulinktext2 ')
        )
    )
except:
    print("Error: Unable to perform DUO 2FA")
    sys.exit()

# ss&fa
selector = driver.find_element(
    By.XPATH, 
    value= '/html/body/div[3]/table[1]/tbody/tr[1]/td[2]/a')
selector.click()

# registration
selector = driver.find_element(
    By.XPATH, 
    value= '/html/body/div[3]/table[1]/tbody/tr[2]/td[2]/a')
selector.click()

# look up
selector = driver.find_element(
    By.XPATH,
    value= '/html/body/div[3]/table[1]/tbody/tr[3]/td[2]/a'
)
selector.click()

# get regSem from selector table
select = Select(driver.find_element(
    By.XPATH, 
    value= '/html/body/div[3]/form/table/tbody/tr/td/select'))
select.select_by_visible_text(regSem)

# submit button
selector = driver.find_element(By.XPATH, value='/html/body/div[3]/form/input[2]')
selector.click()

# get subject id
select = Select(driver.find_element(
    By.XPATH, 
    value= '//*[@id="subj_id"]'))
select.select_by_visible_text(subj)

# course search button
selector = driver.find_element(By.XPATH, value= '/html/body/div[3]/form/input[17]')
selector.click()

# assuming index i begins at 3 in OSCAR XPATH
final_xpath = ''
for i in range(3, maxRange):
    try:
        xpath = '/html/body/div[3]/table[2]/tbody/tr[' + str(i) + ']/td[1]'
        selector = driver.find_element(By.XPATH, value= xpath)
        course = selector.get_attribute('innerHTML')
        if str(course) == classNum:
            final_xpath = '/html/body/div[3]/table[2]/tbody/tr[' + str(i) + ']/td[3]/form/input[30]'
            break
    except:
        break

selector = driver.find_element(By.XPATH, value= final_xpath)
selector.click()

send_notification('YOUR CLASS IS NOW BEING WATCHED')
# loop after this
while (True):
    table_id = driver.find_element(By.XPATH, '/html/body/div[3]/form/table')
    rows = table_id.find_elements(By.TAG_NAME, 'tr') # get all of the rows in the table
    fin_class = ""
    row_value = 0
    for i in range(len(rows)):
        # Get the columns (all the column 2)        
        try:
            sec = rows[i].find_elements(By.TAG_NAME, "td")[4].text
            if (str(sec) == secCode):
                # print('Section ' + str(sec)+ ' has been initiallized.')
                row_value = i
                break
        except:
            continue
        
    fin_class = parse_to_list(rows[row_value].find_elements(By.TAG_NAME, "td"))

    capacity = int(fin_class[11]) # index corresponds to associated column
    filled = int(fin_class[12]) # index corresponds to associated column
    wl_capacity = int(fin_class[14]) # index corresponds to associated column
    wl_filled = int(fin_class[15]) # index corresponds to associated column   
    print("Class " + fin_class[2] + " " + fin_class[3] + " is " + str(filled) + " of " + str(capacity) + ", Waitlist is " + str(wl_filled) + " of " + str(wl_capacity))

    # register for course
    if (filled < capacity):
        print("A SPOT HAS OPENED!!!!!!")
        print("Twilio sent: " + send_notification(
            "Class " + fin_class[2] + " " + fin_class[3] + " is " + str(filled) + " of " + str(capacity)
            + ", Waitlist is " + str(wl_filled) + " of " + str(wl_capacity) + '. TIME TO REGISTER BOZO'
            )
        )
        if register:
            box = driver.find_element(By.XPATH, value= '/html/body/div[3]/form/table/tbody/tr[' + str(row_value + 1) + ']/td[1]')
            selector = box.find_element(By.NAME, value='sel_crn')
            selector.click()
            selector = driver.find_element(By.XPATH, value= '/html/body/div[3]/form/input[7]')
            selector.click()
            break
    
    # waitlist course
    if (wl_filled < wl_capacity):
        print("A SPOT HAS OPENED!!!!!!")
        print(send_notification(
            "Class " + fin_class[2] + " " + fin_class[3] + " is " + str(filled) + " of " + str(capacity)
            + ", Waitlist is " + str(wl_filled) + " of " + str(wl_capacity) + '. TIME TO REGISTER BOZO'
            )
        )
        if register:
            box = driver.find_element(By.XPATH, value= '/html/body/div[3]/form/table/tbody/tr[' + str(row_value + 1) + ']/td[1]')
            selector = box.find_element(By.NAME, value='sel_crn')
            selector.click()
            selector = driver.find_element(By.XPATH, value= '/html/body/div[3]/form/input[7]')
            selector.click()
            break   


    time.sleep(10)
    driver.refresh()

print('Tried to register. Program exiting.')
# Just wait for user to confirm
while(True):
    time.sleep(60)
    driver.refresh()
