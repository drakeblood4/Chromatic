import json
import time
import six
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from bs4 import BeautifulSoup

with open("config.json") as config:
    CONFIG = json.load(config)

##################

DRIVER = webdriver.Firefox()
#You may need to edit this if your computer can't find gecko

"""Consider using a headless browser if behavior is consistent
between headless and headed browsers.

That said, I'm like 70% sure headless browsers will just
randomly have jscript elements vanish for no reason.

That shit is $100% voodoo."""

START_TIME = datetime.now()

##################

def log(s):
    """Prints s with the date/time like Jul 16 09:15:48 PM CDT  Hello world"""
    print(u"{}  {}".format(time.strftime("%b %d %I:%M:%S %p %Z"), s))


def print_chromatic():
    """Print logo and version number."""

    print("""
    Chromatic v0.0.1

    Nice logo and twitter plug coming later

    Special thanks to Tom for writing Pucauto and helping make Cardsphere
    
    """)

#Write wait_for_load if necessary, not sure what CS being slow looks like

def log_in():
    DRIVER.get("http://www.cardsphere.com/login")
    email_form = DRIVER.find_element_by_id("email")
    email_form.send_keys(CONFIG["email"])
    pass_form = DRIVER.find_element_by_id("password")
    pass_form.send_keys(CONFIG["password"])
    DRIVER.find_element_by_class_name("btn-primary").click()

    while(DRIVER.current_url != "https://www.cardsphere.com/"):
        #keep checking until cardsphere is loaded
        continue

def goto_send():
    """Go to the send cards page."""
    
    DRIVER.get("http://www.cardsphere.com/send")

def check_runtime():
    """Return True if the main execution loop should continue.
    Selenium and Firefox eat up more and more memory after long periods of
    running so this will stop Pucauto after a certain amount of time. If Pucauto
    was started with the startup.sh script it will automatically restart itself
    again. I typically run my instance for 2 hours between restarts on my 2GB
    RAM cloud server.
    """

    hours_to_run = CONFIG.get("hours_to_run")
    if hours_to_run:
        return (datetime.now() - START_TIME).total_seconds() / 60 / 60 < hours_to_run
    else:
        return True

def build_trades_dict(soup):

    trades = {}

    number = 0
    for row in soup.find_all(class_="package"):

        #the number of the trade button
        #the easiest way to find the path is to find all send-button class
        #and then just find the nth one
        button_number = number
        number += 1
        

        ##Header has most of the shit we need
        header = row.find(class_="package-heading")

        ##User info
        user_raw = header.find("a")
        username = user_raw.string.strip()
        user_id = user_raw["href"].replace("/user/", "")
        user_id = int(user_id)

        ##Getting Country
        flag = row.find(class_="flag-icon")
        flag = flag["class"][1]
        flag = flag.replace("flag-icon-","")

        #Doing shit to find the multiplier
        multiplier = header.find(class_="negative")
        if multiplier == None:
            multiplier = header.find(class_="positive")
        if multiplier == None:
            multiplier = 0.0

        if multiplier != 0.0:
            multiplier = multiplier.text.strip()
            multiplier = multiplier[-6:-2]
            #This might break if someone has a cartoonishly large positive multiplier
            while not(multiplier.startswith('-') or multiplier.startswith('+')):
                multiplier = multiplier[1:]
            multiplier = float(multiplier)
            multiplier = multiplier/100

        #Doing shit to find the dollar value of the trade
        divs = header.find_all("div")
        value = divs[1].text
        i = value.find('$')
        value = value[i+1:i+10]
        value = value.strip()
        value = float(value)

                


        
        #print(button)

        #I'm not doing any of the single card stuff Tom did.
        #I'm a busy adult with important things to do.

        

        trades[user_id] = {
            "username" : username,
            "country" : flag,
            "multiplier" : multiplier,
            "value" : value,
            "button" : button_number
            }

    return(trades)
        
    
        

def find_trades():
    """this is the trade loop. I'm uncertain what the loop is gonna look like rn,
        it depends a bit on how I think the optimal cardsphere strategy looks,
        and on how many different options I can reasonably create"""
    goto_send()
    ###time.sleep(3) ###Maybe need sleep for load, not sure
    soup = BeautifulSoup(DRIVER.page_source, "html.parser")
    if CONFIG["debug"] == 1:
        print(soup)
    trades = build_trades_dict(soup)
    for i in trades:
        if trades[i]["country"] == CONFIG["country"]:
            if trades[i]["value"] >= CONFIG["min_domestic"]:
                if trades[i]["multiplier"] >= CONFIG["max_markdown"]:
                    to_click = DRIVER.find_elements_by_class_name("send-button")
                    to_click[(trades[i]["button"])].click()
                    time.sleep(5)
                    to_click = DRIVER.find_element_by_id("button-confirm")
                    to_click.click()
                    print("TRADE CONFIRMED")
                    log(u"Traded ${} worth of cards to {} with a {}x multiplier".format(
                        trades[i]["value"],trades[i]["username"],trades[i]["multiplier"]))
                else:
                    continue
            else:
                continue

            
        else:
            if trades[i]["value"] >= CONFIG["min_foreign"]:
                if trades[i]["multiplier"] >= CONFIG["max_markdown"]:
                    to_click = DRIVER.find_elements_by_class_name("send-button")
                    to_click[(trades[i]["button"])].click()
                    time.sleep(5)
                    to_click = DRIVER.find_element_by_id("button-confirm")
                    to_click.click()
                    print("TRADE CONFIRMED")
                    log(u"Traded ${} worth of cards to {} with a {}x multiplier".format(
                        trades[i]["value"],trades[i]["username"],trades[i]["multiplier"]))
                    

if __name__ == "__main__":

    """startup"""
    print_chromatic()
    log_in()
    goto_send()

    while(1):
        find_trades()
        time.sleep(9)

    
