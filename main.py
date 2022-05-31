from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from random import uniform as rand

url = "https://www.ea.com/en-gb/fifa/ultimate-team/web-app/"
FUT_player_list={}

edgedriver = "C:\\Users\\Sireena Mistry\\AppData\\Local\\Microsoft\\WindowsApps\\chromedriver.exe"


class Session(object):
    def __init__(self, FUT=False):
        self.url = url
        self.logged_in = False
        self.current_strategy = 'Logging In...'
        self.userdir = "user-data-dir=C:\\Users\\Sireena Mistry\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default"
        self.location = 'unknown'
        self.credits = 0
        self.buy = 0
        self.sell = 0
        self.player = ""
        self.too_late = 0
        self.transfer_expired_clean_required = True
        self.FUT=FUT
        print(FUT_player_list)
        while True:
            try:
                self.opts = Options()
                self.opts.use_chromium = True
                self.opts.add_argument(self.userdir)
                self.opts.add_argument('--disable-infobars')
                self.opts.add_argument('--disable-plugins-discovery')
                self.opts.add_argument('--window-size=1920,1080')
                self.opts.add_argument('--disable-offline-auto-reload-visible-only')
                self.opts.add_argument('--allow-http-background-page')
                self.driver = webdriver.Chrome(edgedriver, options=self.opts)
                self.wait = WebDriverWait(self.driver, 10)
                break
            except WebDriverException as e:
                if 'failed to start' in str(e).lower():
                    raise Exception(
                        'Please close all windows for this bot before trying again. You may need to close out of ALL chrome instances to continue')
                else:
                    raise Exception(e)
        self.__openpage__()

    def player_lookup(self, player):
        player_prices = {"Hugo Ayala": [450, 850], "Serdar Aziz": [400, 900],"Alejandro Donatti":[900, 1300]}
        try:
            prices = player_prices.get(player)
            self.buy = prices[0]
            self.sell = prices[1]
        except TypeError:
            return False
        return True

    def __openpage__(self):
        if self.FUT:
            self.driver.get("https://www.futbin.com/players?page=1&ps_price=700-900&version=gold_nr&sort=Player_Rating&order=asc")
            self.FUT_apply_criteria()

        else:
            print("Im now opening the page and sleeping")
            self.driver.get(url)
            time.sleep(10)
            self.logged_in = False
            while not self.logged_in:
                print("Going into the while loop...")
                progress = self.__login_progress__()
                print(progress)
                if progress == 'ea_account':
                    print(self, 'Attempting User/Pass...')
                    try:
                        self.__type_xpath__('//*[@id="email"]', "rups_54") #change this
                    except TimeoutException:
                        pass
                    try:
                        # noinspection PyUnresolvedReferences
                        self.__type_xpath__('//*[@id="password"]', 'xxx') #change this
                        print(self, 'Entering user/pass...')
                        self.__click_xpath__("//*[@id='btnLogin']")
                    except TimeoutException:
                        print('No user pass needed...')

    def __logged_in__(self):
        try:
            if self.get_credits() > 0:
                print(self, 'Successful Login!')
                self.credits = self.get_credits()
                # self.__check_for_errors__()
                # self.rate_limit()
                self.location = 'home'
                self.logged_in = True
                if self.transfer_expired_clean_required:
                    self.housekeeping('expired')
                return True
            else:
                self.logged_in = False
                return False
        except NoSuchElementException:
            self.logged_in = False
            return False

    def __login_progress__(self):
        if not self.__logged_in__():
            try:
                self.__click_xpath__("//*[@id='Login']/div/div/button[1]")
            except TimeoutException:
                pass
            try:
                self.__get_xpath__("//*[contains(text(), 'Sign in with your EA Account')]")
                return 'ea_account'
            except (TimeoutException, NoSuchElementException, ElementNotVisibleException):
                pass

    def get_credits(self):
        print("Trying to get coins..")
        try:
            found = self.driver.find_element_by_xpath("//div[@class='view-navbar-currency-coins']").text
            if found != '' and '-' not in found:
                print("Coins found!!")
                found = int(found.replace(',', ''))
                if found > 0:
                    self.credits = found
                    print("You have...", str(self.credits) + " coins")
        except TimeoutException:
            print("Couldnt find coins...")
            pass

        return self.credits

    def __click_xpath__(self, xpath):
        self.__check_for_errors__()
        wait = WebDriverWait(self.driver, 10)
        print("Clicking...", xpath)
        e = wait.until(ec.element_to_be_clickable((By.XPATH, xpath)))
        print("found it...")
        move = ActionChains(self.driver).move_to_element_with_offset(e, rand(1, 5), rand(1, 5))
        move.perform()
        e.click()
        time.sleep(1)
        self.__check_for_errors__()

    def __type_xpath__(self, xpath, text):
        self.__check_for_errors__()
        self.__click_xpath__(xpath)
        e = self.driver.find_element_by_xpath(xpath)
        e.send_keys(Keys.CONTROL + 'a')
        e.send_keys(Keys.DELETE)
        e.clear()
        e.send_keys(text)
        self.__check_for_errors__()

    def __get_xpath__(self, xpath, as_list=False):
        print(self, "Trying to get XPATH..", xpath)
        wait = WebDriverWait(self.driver, 10)
        if not as_list:
            return wait.until(ec.presence_of_element_located((By.XPATH, xpath)))
        else:
            return self.driver.find_elements_by_xpath(xpath)

    def __get_xpath_detail__(self, xpath, att=False, which_att=None):
        if not att:
            return self.driver.find_element_by_xpath(xpath).text
        else:
            return self.driver.find_element_by_xpath(xpath).get_attribute(which_att)

    def go_to(self, where):
        if where == 'transfers':
            self.__click_xpath__("//nav/button[3]")
            self.location = 'transfer_menu'
        elif where == 'search':
            self.go_to('transfers')
            self.__click_xpath__("//div[@class='tile col-1-1 ut-tile-transfer-market']")
            self.location = 'transfer_search'
        elif where == 'targets':
            self.go_to('transfers')
            time.sleep(3)
            self.__click_xpath__("//div[@class='tile col-1-2 ut-tile-transfer-targets']")
            self.location = 'transfer_search'
        elif where == 'list':
            self.go_to('transfers')
            self.__click_xpath__("//div[@class='tile col-1-2 ut-tile-transfer-list']")
            self.location = 'transfer_targets'

    def find_price(self, player):
        if not self.player_lookup(player):
            print("I couldnt find the price for..", player)
        else:
            self.player = player
            self.start_buying(self.player)

    def start_buying(self, player, as_snipper=False):
        self.go_to('search')
        self.__type_xpath__("//input[@class='ut-text-input-control']", player)
        self.__click_xpath__("//ul[@class='ut-button-group playerResultsList']")
        if as_snipper:
            self.__type_xpath__("//div[@class='price-filter'][4]//input", '116000')
            self.__click_xpath__("//button[text()='Search']")
        else:
            self.__click_xpath__("//button[text()='Search']")
            self.check_results()

    def check_results(self):
        time.sleep(3)
        items = self.__get_xpath__("//ul/li[contains(@class,'listFUTItem has-auction-data')]", as_list=True)
        if not items:
            print("No results found")
        else:
            self.process_items(items, self.buy)

    def process_items(self, items, buy):
        cycle = 0
        self.too_late=0
        while cycle < 7:
            time.sleep(7)
            i = 1
            for item in items:
                start_price_raw = self.__get_xpath_detail__(
                    "//ul/li[contains(@class,'listFUTItem has-auction-data')][" + str(
                        i) + "]//*/span[text()='Start Price:']/../span[2]")
                current_price_raw = self.__get_xpath_detail__(
                    "//ul/li[contains(@class,'listFUTItem has-auction-data')][" + str(
                        i) + "]/div/div[2]//div[2]/span[1]/../span[2]")
                auction_status = self.__get_xpath_detail__(
                    "//ul/li[contains(@class,'listFUTItem has-auction-data')][" + str(i) + "]", att=True,
                    which_att="class")
                start_price = start_price_raw.replace(',', '')
                current_price = current_price_raw.replace(',', '')
                print(start_price, buy, current_price, auction_status)
                bid = False
                if auction_status == "listFUTItem has-auction-data highest-bid" or auction_status == "listFUTItem has-auction-data selected highest-bid":
                    print("IM WINNING THIS!!")
                elif auction_status == "listFUTItem has-auction-data" or auction_status == "listFUTItem has-auction-data outbid" or auction_status == "listFUTItem has-auction-data selected" or auction_status == "listFUTItem has-auction-data selected outbid":
                    print(start_price, buy, current_price_raw)
                    if int(start_price) < int(buy):
                        if str(current_price) == '---':
                            print("Bidding at start price...")
                            bid = True
                        elif int(current_price) < int(buy):
                            print("I should bid current bid lower than my limit...")
                            print("My Limit..", buy)
                            print("Current Price..", current_price)
                            bid = True
                        else:
                            print("Start price was low but current price to high..")
                            print("My Limit..", buy)
                            print("Current Price..", current_price)
                    else:
                        print("Start price too high..")
                else:
                    print("Not considered - something went wrong")
                if bid:
                    self.__transfer_bid__(i)
                print("Cycle...", cycle)
                print("Counter...", i)
                i = i + 1
            cycle = cycle + 1
            self.__click_xpath__("//*[@class='ut-navigation-button-control']")
            self.__click_xpath__("//button[text()='Search']")
            time.sleep(7)
        self.list_players(self.player, self.sell, )

    def __transfer_bid__(self, i):
        self.__click_xpath__("//ul/li[contains(@class,'listFUTItem has-auction-data')][" + str(i) + "]")
        self.__click_xpath__("//button[text()='Make Bid']")
        time.sleep(2)
        bid_result = self.__get_xpath_detail__(
            "//ul/li[contains(@class,'listFUTItem has-auction-data')][" + str(i) + "]", att=True,
            which_att="class")
        if 'highest-bid' in bid_result:
            print("Bid successful")
            time.sleep(1)
        else:
            print("Bid unsuccessful, will review and attempt again..")
            time.sleep(1)
            current_price_raw = self.__get_xpath_detail__(
                "//ul/li[contains(@class,'listFUTItem has-auction-data')][" + str(
                    i) + "]/div/div[2]//div[2]/span[1]/../span[2]")
            if current_price_raw == '---':
                current_price = '0'
            else:
                current_price = current_price_raw.replace(',', '')
            if int(current_price) < int(self.buy):
                print("Current price is still low - re-attempting bid")
                self.__click_xpath__("//button[text()='Make Bid']")
                time.sleep(2)
                bid_result = self.__get_xpath_detail__(
                    "//ul/li[contains(@class,'listFUTItem has-auction-data')][" + str(i) + "]", att=True,
                    which_att="class")
                if 'highest-bid' in bid_result:
                    print("Bid successful")
                else:
                    self.too_late = self.too_late + 1
                    print("Too late count is ,", self.too_late)
                    if self.too_late > 5:
                        print("going into extended sleep")
                        time.sleep(120)
                        self.too_late = 0
            else:
                print("Price is too high now after reviewing - moving on")
        self.transfer_expired_clean_required = True

    def list_players(self, player, sellprice):
        self.housekeeping('expired')
        self.go_to('targets')
        print("Listing players for transfer...")
        time.sleep(2)
        # Only list players ontoo_ce active is
        try:
            self.driver.find_element_by_xpath("//*[@class='sectioned-item-list'][1]/ul/li")
            active_bids = True
            return False
        except NoSuchElementException:
            active_bids = False
        try:
            self.driver.find_element_by_xpath("//*[@class='sectioned-item-list'][1]/ul/li")
            active_bids = True
            return False
        except NoSuchElementException:
            active_bids = False
        if not active_bids:
            try:
                won_items = self.driver.find_element_by_xpath("//*[@class='sectioned-item-list'][3]/ul/li")
                while won_items:
                    self.__click_xpath__("//*[@class='sectioned-item-list'][3]/ul/li[1]")
                    self.__click_xpath__("//button[@class='accordian']")
                    time.sleep(1)
                    self.__type_xpath__("//div[@class='panelActionRow'][1]//input", sellprice)

                    self.__type_xpath__("//div[@class='panelActionRow'][2]//input", sellprice)

                    self.__click_xpath__("//button[@class='btn-standard call-to-action']")
                    time.sleep(3)
                    try:
                        won_items = self.driver.find_element_by_xpath("//*[@class='sectioned-item-list'][3]/ul/li")
                    except NoSuchElementException:
                        print("List cleared")
                        break

                    print("List cycle completed..")
            except NoSuchElementException:
                print("Happy days ....Nothing to list...")
                return True
        self.housekeeping('expired')

    def housekeeping(self, what_to_clean):
        if self.transfer_expired_clean_required:
            if what_to_clean == 'expired':
                if not self.location == 'transfer_targets':
                    self.go_to('targets')
            try:
                self.__click_xpath__("//button[text() = 'Clear Expired']")
                print("Cleared expired items...")
                self.transfer_expired_clean_required = False
            except (NoSuchElementException, TimeoutException):
                print("Nothing has expired to clear...")
        else:
            print("Transfer expired clean not required at this time...")

    def __check_for_errors__(self):
        try:
            known_errors = self.driver.find_element_by_xpath(
                "//h1[@class='dialog-title' and text() = 'Already Highest Bidder']")
            if known_errors:
                self.driver.find_element_by_xpath(
                    "//h1[@class='dialog-title' and text() = 'Already Highest Bidder']/../../..//button/span[1]").click()
                print("Continuing.....")
        except (NoSuchElementException, TimeoutException):
            pass

    def snipper(self):
        self.start_buying("Sergio Ramos", as_snipper=True)
        snip_cycle = 0
        while snip_cycle < 100:
            print(snip_cycle)
            try:
                snip_auction = self.driver.find_element_by_xpath("//ul/li[contains(@class,'listFUTItem has-auction-data')]")
                if snip_auction:
                    BIN = "//span[text()='Buy Now:']/../span[2]"
                    self.__click_xpath__("//ul/li[contains(@class,'listFUTItem has-auction-data')][last()]")
                    self.__click_xpath__("//button[@class='btn-standard buyButton currency-coins']")
                    self.__click_xpath__("//div[@class='ut-button-group']/button[1]/span[@class='btn-text' and text()= 'Ok']")
                    break
            except NoSuchElementException:
                print("Nothing found... moving on to next cycle..")
            self.__click_xpath__("//*[@class='ut-navigation-button-control']")
            self.__click_xpath__("//button[text()='Search']")
            snip_cycle = snip_cycle +1
        print("Snip cycle finished!!")

    def FUT_apply_criteria(self):
        items = self.__get_xpath__("//*[@id='repTb']/tbody/tr", as_list=True)
        i = 1
        for item in items:
            player_name = self.driver.find_element_by_xpath("//*[@id='repTb']/tbody/tr[" + str(i) + "]//div[2]/div/a").text
            player_rating = self.driver.find_element_by_xpath("//*[@id='repTb']/tbody/tr[" + str(i) + "]/td[2]/span").text
            player_BIN_price = self.driver.find_element_by_xpath("//*[@id='repTb']/tbody/tr[" + str(i) + "]/td[5]/span").text
            print(player_name, player_rating, player_BIN_price)
            FUT_player_list[player_name] = [player_rating, player_BIN_price]
            i = i + 1
        print(FUT_player_list)
        self.driver.close()

    def FUT_find_EA_bin(self):
        print(FUT_player_list)
        for x in FUT_player_list.keys():
            print(x)
            xxx = False
            bin_price = 750
            self.go_to('search')
            self.__type_xpath__("//input[@class='ut-text-input-control']", x)
            try:
                self.__click_xpath__("//ul[@class='ut-button-group playerResultsList']")
                while not xxx:
                    self.__type_xpath__("//div[@class='price-filter'][4]//input", bin_price)
                    self.__click_xpath__("//button[text()='Search']")
                    time.sleep(2)
                    items = self.__get_xpath__("//ul/li[contains(@class,'listFUTItem has-auction-data')]", as_list=True)
                    if items:
                        if bin_price > 750:
                            FUT_player_list[x].append(bin_price)
                        else:
                            #del FUT_player_list[x]
                            print("Deleted player , bin too low,", x, bin_price)
                        xxx=True
                    else:
                        self.__click_xpath__("//*[@class='ut-navigation-button-control']")
                        if bin_price >= 1000:
                            bin_price = bin_price + 100
                        else:
                            bin_price = bin_price + 50
            except TimeoutException:
                pass
        print(FUT_player_list)
        self.refine_fut_list()

    def refine_fut_list(self):
        new = {}
        for keys in FUT_player_list:
            live_price = FUT_player_list.get(keys)

            if len(live_prices) > 2 and prices[2] > 850:
                new[keys] = prices

        print(new)







bot1 = Session(FUT=True)
bot1 = Session()
bot1.FUT_find_EA_bin()



# q = 0
# while q < 10:
#    bot1.find_price("Hugo Ayala")
#    while not bot1.list_players(bot1.player, bot1.sell):
#        print("Sleeping 1")
#        time.sleep(30)
#        bot1.list_players(bot1.player, bot1.sell)
#    bot1.find_price("Serdar Aziz")
#    while not bot1.list_players(bot1.player, bot1.sell):
#        print("Sleeping 2")
#        time.sleep(30)
#        bot1.list_players(bot1.player, bot1.sell)
#    bot1.list_players(bot1.player, bot1.sell)
#    q = q + 10

# bot1.test()
# while n < 3
#    do buying
#    but also check transfer list
#    if greater than 30 put on market
#    but if list is 90 then stop byuing and selling
