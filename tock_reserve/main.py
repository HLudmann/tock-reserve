"""CLI Tool to make Restaurant reservation on Tock."""
import asyncio
import logging
import os
import random
import time
import typing as t
from datetime import datetime, timezone
from urllib.parse import urlencode, urljoin

import fire
import selenium.webdriver as w
import selenium.webdriver.support.expected_conditions as ec
import telegram as tel
from selenium.webdriver.common import by
from selenium.webdriver.support import wait

TOCK_URL = "https://www.exploretock.com"


class TockReserve:
    """Tock Reservation class."""

    def __init__(self: t.Self, restaurant: str) -> None:
        """Initialize TockReserve class."""
        self.restaurant = restaurant
        self.telebot = tel.Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
        self.username = os.environ["USERNAME"]
        self.password = os.environ["PASSWORD"]

    def run(self: t.Self, size: int) -> None:
        """Run the Tock reservation.

        Args:
        ----
            email (str): email to login
            password (str): password to login
            size (int): size of the party
        """
        self.driver = w.Firefox()

        if self.login(self.username, self.password) == 0:
            if not self.search_open_days(size):
                logging.info("No open days found for the next 6 months")
        else:
            logging.error("Login failed")

        found = False
        while not found:
            found = self.search_open_days(size)
            time.sleep(random.randint(1, 5) * 60)

        self.driver.quit()

    def search_open_days(self: t.Self, size: int) -> bool:
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month

        for m in range(month, month + 8, 2):
            if m > 12:
                year += 1
                m = 1
            if (day := self.reserve(year, m, "17%3A00", size)) > 0:
                msg = self.send_message(
                    message=f"Open days found for {year}-{m:02d}-{day} for {size} people.\n"
                    "Go to https://www.exploretock.com/noma/checkout/options to finish the reservation.",
                )
                asyncio.run(msg)
                return True
            time.sleep(random.randint(1, 5))
        return False

    def reserve(self: t.Self, year: int, month: int, time: str, size: int) -> int:
        """Reserve a table on Tock.

        Args:
        ----
            year (int): year to reserve
            month (int): month to reserve
            time (str): time to reserve
            size (int): size of the party

        Returns:
        -------
            int: 1 if no open days found, 0 otherwise
        """
        search_url = (
            f"{urljoin(TOCK_URL, '{self.restaurant}/search')}"
            f"?{urlencode({'date': f'{year}-{month}-01', 'time': time, 'size': size})}"
        )
        self.driver.get(search_url)

        wait.WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((by.By.CLASS_NAME, "ConsumerCalendar-month")),
        )

        open_days = self.driver.find_elements(
            by.By.CSS_SELECTOR,
            "button.ConsumerCalendar-day.is-available",
        )
        if not open_days:
            logging.info("No open days found")
            return 0

        open_days[0].click()

        return open_days[0].text

    def login(self: t.Self, email: str, password: str) -> bool:
        """Login to Tock.

        Args:
        ----
            email (str): email to login
            password (str): password to login

        Returns:
        -------
            int: 1 if login failed, 0 otherwise
        """
        self.driver.get(TOCK_URL + "/login")
        wait.WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((by.By.NAME, "email")),
        )
        self.driver.find_element(by.By.NAME, "email").send_keys(email)
        self.driver.find_element(by.By.NAME, "password").send_keys(password)

        self.driver.find_element(by.By.CSS_SELECTOR, ".MuiButton-fullWidth").click()

        # Checks for profile image css selector -> maybe not the best check but it works
        try:
            wait.WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((by.By.CLASS_NAME, "css-1wujmwl")),
            )
        except Exception:
            logging.error("Login failed")
            return False

        return True

    async def send_message(self: t.Self, message: str) -> None:
        chat_id = (await self.telebot.get_updates())[-1].message.chat_id
        await self.telebot.send_message(chat_id=chat_id, text=message)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    fire.Fire(TockReserve)
