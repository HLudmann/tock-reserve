"""CLI Tool to make Restaurant reservation on Tock."""
import asyncio
import logging
import os
import random
import time
import typing as t
from datetime import datetime, timezone
from urllib.parse import urlencode, urljoin

import dotenv
import fire
import retry as r
import selenium.webdriver as w
import selenium.webdriver.support.expected_conditions as ec
import telegram as tg
from selenium.webdriver.common import by
from selenium.webdriver.support import wait

TOCK_URL = "https://www.exploretock.com"


class TockReserve:
    """Tock Reservation class."""

    def __init__(self: t.Self, restaurant: str) -> None:
        """Initialize TockReserve class."""
        self.restaurant = restaurant
        self._token = os.environ["TELEGRAM_BOT_TOKEN"]
        self._chat_id = os.environ["TELEGRAM_CHAT_ID"]
        self._username = os.environ["USERNAME"]
        self._password = os.environ["PASSWORD"]
        self._driver = None

    def __exit__(self: t.Self) -> None:
        """Exit the class."""
        if self._driver is not None:
            self._driver.quit()

    @property
    def driver(self: t.Self) -> w.Firefox:
        """Get the driver."""
        if self._driver is None:
            self._driver = w.Firefox()
        return self._driver

    def run(self: t.Self, size: int) -> None:
        """Run the Tock reservation.

        Args:
        ----
            email (str): email to login
            password (str): password to login
            size (int): size of the party
        """
        try:
            return self._run(size)
        except Exception:
            logging.exception("An error occurred")
            self._close()
            return self.run(size)

    def _close(self: t.Self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception:
                pass
        self._driver = None

    def _run(self: t.Self, size: int) -> None:
        self.gdpr()
        self.login()

        found = False
        while not found:
            # adjust for GMT+1 timezone
            if (now := datetime.now(timezone.utc)).hour >= 20:
                future = now.replace(day=now.day + 1, hour=8, minute=0, second=0)
                sleep_time = (future - now).total_seconds()
                logging.info("Sleeping during the night (21h-9h) for %s seconds", sleep_time)
                time.sleep(sleep_time)

            found = self.search_open_days(size)
            time.sleep(random.randint(1, 5) * 60)

    def search_open_days(self: t.Self, size: int) -> bool:
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month

        for m in range(month, month + 8):
            if m > 12:
                year += 1
                m = 1
            if res := self.reserve(year, m, "17:00", size):
                self.send_message(
                    message=f"{res}\nGo to https://www.exploretock.com/noma/checkout/options to finish the reservation.",
                )
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
            urljoin(TOCK_URL, f"{self.restaurant}/search")
            + "?"
            + urlencode({"date": f"{year}-{month:02d}-01", "time": time, "size": size})
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
            logging.info(f"No open days found for {year}-{month:02d}")
            return ""

        open_days[0].click()
        wait.WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located(
                (by.By.CSS_SELECTOR, "button.Consumer-resultsListItem.is-available")
            ),
        )
        hours = self.driver.find_elements(
            by.By.CSS_SELECTOR, "button.Consumer-resultsListItem.is-available"
        )

        logging.info(
            f"Found {len(hours)} open tables on {year}-{month:02d}-{open_days[0].text}: {', '.join([h.text for h in hours])}"
        )

        hours[0].click()

        msg = f"Found open table on {year}-{month:02d}-{open_days[0].text} at {hours[0].text.split()[0]} for {size} people."
        logging.info(msg)
        return msg

    def login(self: t.Self) -> None:
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
        self.driver.find_element(by.By.NAME, "email").send_keys(self._username)
        self.driver.find_element(by.By.NAME, "password").send_keys(self._password)

        self.driver.find_element(by.By.CSS_SELECTOR, ".MuiButton-fullWidth").click()

        # Checks for profile image css selector -> maybe not the best check but it works
        wait.WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((by.By.CLASS_NAME, "css-1wujmwl")),
        )

        return

    def gdpr(self: t.Self) -> None:
        """Accept GDPR cookies."""
        self.driver.get(TOCK_URL + "/noma")
        time.sleep(2)
        for button in self.driver.find_elements(by.By.CLASS_NAME, "truste-button2"):
            if button.text == "Reject All":
                button.click()
                break

    @r.retry(tries=5, delay=5, backoff=2, logger=logging.getLogger())
    def send_message(self: t.Self, message: str) -> None:
        coroutine = tg.Bot(token=self._token).send_message(chat_id=self._chat_id, text=message)
        asyncio.run(coroutine)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    dotenv.load_dotenv()
    fire.Fire(TockReserve)
