from datetime import datetime

import selenium.webdriver as w
# import selenium.webdriver.common.by as by
# import selenium.webdriver.support.expected_conditions as expected_conditions
# import selenium.webdriver.support.wait as wait

TOCK_URL = "https://www.exploretock.com/"

class TockReserve:
    def __init__(self, restaurant: str):
        options = w.ChromeOptions()
        self.driver = w.Chrome(options=options)
        self.restaurant = restaurant

    def reserve(self, date: datetime, time: str, party_size: int):
        search_url = f"{TOCK_URL}{self.restaurant}/search?date={date.strftime('%Y-%m-%d')}&time={time}&size={party_size}"
        self.driver.get(search_url)

        # days = self.driver.find_elements(by.By.CSS_SELECTOR, "button.ConsumerCalendar-day")
