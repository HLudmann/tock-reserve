"""CLI Tool to make Restaurant reservation on Tock."""
import logging
import typing as t
from urllib.parse import urlencode, urljoin

import selenium.webdriver as w
import selenium.webdriver.support.expected_conditions as ec
from selenium.webdriver.common import by
from selenium.webdriver.support import wait

TOCK_URL = "https://www.exploretock.com"


class TockReserve:
    """Tock Reservation class."""

    def __init__(self: t.Self, restaurant: str) -> None:
        """Initialize TockReserve class."""
        self.driver = w.Firefox()
        self.restaurant = restaurant

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
            f"{urljoin(TOCK_URL, "{self.restaurant}/search")}"
            f"?{urlencode({'date': f"{year}-{month}-01", 'time': time, 'size': size})}"
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
            return 1

        return 0

    def login(self: t.Self, email: str, password: str) -> int:
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
            wait.WebDriverWait(self.driver, 30).until(
                ec.visibility_of_element_located((by.By.CSS_SELECTOR, ".css-118lam2")),
            )
        except Exception:
            logging.error("Login failed")
            return 1

        return 0
