#!/usr/bin/python3
# coding: utf-8

"""
    Provides the LeboncoinManager class, used to manage your ads on leboncoin.fr.

    Usage:

    >>> from core import LeboncoinManager
    >>> manager = LeboncoinManager("username", "password")
    >>> manager.update("My ad title")
"""

import sys
import re
import os.path
import tempfile
import urllib.request
import logging
import datetime
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError

try:
    import selenium
    from selenium import webdriver
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
except ImportError as e:
    sys.exit(
        "Error during selenium import, please make sure that selenium is correctly installed: `pip install selenium`")


logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

file_handler = RotatingFileHandler('leboncoin.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
logger.addHandler(steam_handler)


class NavigationError(Exception):
    pass


class LeboncoinManager:
    def __init__(self, username=None, password=None):
        self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 10)

        if username is not None and password is not None:
            self.login(username, password)

    def login(self, username, password, login_url="https://compteperso.leboncoin.fr/account/index.html?ca=12_s"):
        """login(username, password[, login_url="https://compteperso.leboncoin.fr/account/index.html?ca=12_s]")
        Connect to your Leboncoin account using the given credentials. Owing an account
        is mandatory to perform any action."""

        logger.info("Connecting to leboncoin.fr with username: %s", username)

        self.driver.get(login_url)
        username_field = self.driver.find_element_by_name("st_username")
        password_field = self.driver.find_element_by_name("st_passwd")

        username_field.send_keys(username)
        password_field.send_keys(password)

        submit_button = self.driver.find_element_by_id("connect_button")
        submit_button.click()

    def delete(self, ad_title, recover_ad=False, recover_images=False):
        """
        delete(ad_title[, recover_ad=False, recover_images=False])
        Delete the ad based on its title.
        recover_ad: if True, recovers information about the ad before deleting it, and
                    returns it as a dict
        recover_images: if True, the ad images of the ad are saved in a temporary
        directory, and the corresponding paths are saved in the returned dict.
        """

        logger.debug("recover_ad: {}".format(recover_ad))
        logger.debug("recover_images: {}".format(recover_images))

        ads = self.driver.find_elements_by_xpath(
            "//form[@id='dashboard']/div[@class='list']/div[@class='element' or @class='element variant']")

        for ad in ads:
            a_tag = ad.find_element_by_tag_name("a")
            if a_tag.text in ad_title:
                break

        else:
            raise NavigationError("No ad with name '{}' was found".format(ad_title))

        try:
            price_string = getattr(ad.find_element_by_class_name("price"), "text")
            price_match = re.search(r"([0-9]+) €", price_string)

            if price_match is not None:
                price = price_match.group(1)

        except selenium.common.exceptions.NoSuchElementException as e:
            logger.info("No price field in the ad")
            price = None

        category_string = getattr(ad.find_element_by_class_name("category"), "text")
        category_match = re.search(r"catégorie : ([^\t\n\r\f\v]+)", category_string)

        if category_match is not None:
            category = category_match.group(1)

        self.driver.get(a_tag.get_attribute("href"))
        postal_code = getattr(self.driver.find_element_by_xpath("//td[@itemprop='postalCode']"), "text")
        description = getattr(self.driver.find_element_by_xpath("//div[@itemprop='description']"), "text")

        if recover_images:
            logger.info("Retrieving images...")
            image_list = self.driver.find_elements_by_xpath("//meta[@itemprop='image']")

            image_url_list = [image.get_attribute("content") for image in image_list]
            image_path_list = []

            tempdir = tempfile.mkdtemp()
            for image_url in image_url_list:
                try:
                    file_name = os.path.basename(urlparse(image_url).path)
                    logging.info("Downloading image from url: %s", image_url)
                    request = urllib.request.urlopen(image_url)
                    image_path = os.path.join(tempdir, file_name)

                    with open(image_path, 'wb') as f:
                        logger.debug("Saving image in {}".format(image_path))
                        f.write(request.read())

                    image_path_list.append(image_path)

                except HTTPError as e:
                    logger.error("HTTP Error: code {}, url: {}".format(e.code, image_url))
                except URLError as e:
                    logger.error("URL Error: ", e.reason, image_url)

        buttons = self.driver.find_elements_by_xpath("//div[@class='lbc_links']/a[@onclick]")

        for delete_button in buttons:
            if delete_button.text == "Supprimer":
                break

        else:
            raise NavigationError("No 'Delete' button.")

        logger.info("Deleting the ad '%s'", ad_title)
        delete_button.click()

        continue_xpath = "//input[@name='continue']"
        continue_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, continue_xpath)))

        continue_button.click()

        select_menu = self.driver.find_element_by_name("delete_reason")
        selector = Select(select_menu)
        selector.select_by_index(2)

        try:
            continue_button = self.driver.find_element_by_xpath("//input[@name='st_ads_continue']")
            continue_button.click()
        except selenium.common.exceptions.NoSuchElementException as e:
            raise NavigationError("The ad cannot be deleted, no 'Delete' button") from e

        logger.info("Ad deleted!")

        if recover_ad:
            logger.info("Recovering ad information...")
            ad_content = {"ad_title": ad_title,
                          "description": description,
                          "zipcode": postal_code,
                          "price": price,
                          "category": category}

            if recover_images:
                ad_content["image_path_list"] = image_path_list

            logger.debug("\n".join(["{}: {}".format(key, value) for key, value in ad_content.items()]))

            return ad_content

    def publish(self, ad_title, description, category, zipcode, price=None,
                publish_url="http://www2.leboncoin.fr/ai?ca=22_s", image_path_list=None):
        """
        publish(ad_title, description, category, zipcode[, price=None, publish_url="http://www2.leboncoin.fr/ai?ca=22_s", image_path_list=None])
        Publish an add on Leboncoin.
        """
        logger.info("Publishing the ad: '%s'", ad_title)
        self.driver.get(publish_url)
        select_category_menu = self.driver.find_element_by_name("category")
        selector = Select(select_category_menu)
        selector.select_by_visible_text(category)

        zipcode_field = self.driver.find_element_by_id("zipcode")
        zipcode_field.clear()
        zipcode_field.send_keys(zipcode)

        subject_field = self.driver.find_element_by_id("subject")
        subject_field.send_keys(ad_title)

        body = self.driver.find_element_by_id("body")
        body.send_keys(description)

        if price is not None:
            price_field = self.driver.find_element_by_id("price")
            price_field.send_keys(price)

        if image_path_list is not None:
            for image_nb, image_path in enumerate(image_path_list):
                if image_nb == 3:
                    logger.warn("No more than 3 images can be uploaded (number of images: %s)", len(image_path_list))
                    break

                image_field = self.driver.find_element_by_id("image{}".format(image_nb))

                image_field.send_keys(image_path)
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[@id='image_box_{}']//a[@class='remove_image']".format(image_nb))))

        logger.debug("All fields completed, validating the ad")
        validate_button = self.driver.find_element_by_name("validate")
        validate_button.click()

        logger.debug("Accepting the rule")
        cgu_accept = self.driver.find_element_by_name("accept_rule")
        cgu_accept.click()

        logger.debug("Sending the ad")
        create_button = self.driver.find_element_by_name("create")
        create_button.click()

        logger.info("Ad published!")

    def update(self, ad_title, recover_images=True, error_screenshot=True):
        """
        update(ad_title[, recover_images=True])
        Update an already existing ad on Leboncoin based on its title.
        recover_images: if True, the images of the original ad are kept
        """
        logging.info("Updating the ad '{}'".format(ad_title))
        try:
            ad_parameters = self.delete(ad_title, recover_images=recover_images, recover_ad=True)
        except NavigationError as e:
            logger.error(*e.args)
            if error_screenshot:
                filename = datetime.datetime.now().strftime("error_screenshot_%Y-%m-%d_%H:%M:%S.png")
                self.driver.get_screenshot_as_file(os.path.join(os.getcwd(), filename))
                logging.error("Saving the screenshot in {}".format(filename))
                logging.warning("Skipping ad")
        else:
            self.publish(**ad_parameters)

    def quit(self):
        self.driver.quit()
