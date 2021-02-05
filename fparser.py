import logging
import time

import requests
from bs4 import BeautifulSoup

import settings


class WrongResponse(Exception):
    pass


def get_html(url, params=None):
    r = requests.get(url, params=params, headers=settings.HEADERS)
    if r.status_code == 200:
        return r.text
    else:
        raise WrongResponse(f"Server response: {r}")


def get_project_budget(project):
    budget = project.find("td", class_="project-budget")
    if budget is None:
        return ""
    return budget.get_text(strip=True)


class FreelanceHuntParser:

    def __init__(self, categories, eventloop=None, on_project_listener=None):
        logging.info("Initializing parser...")
        self.on_project_listener = on_project_listener
        self.url = categories
        self.loop = eventloop
        self.categories = categories

    def listen(self):
        logging.info("Starting listening...")
        while True:
            for category in self.categories:
                project = self.parse(category)
                if project is not None:
                    self.loop.create_task(self.on_project_listener(project))
            time.sleep(settings.LISTENING_TIMEOUT)

    @staticmethod
    def parse(category):
        logging.info(f"Parsing {category['url']}...")
        html = get_html(category["url"])
        soup = BeautifulSoup(html, "html.parser")
        project = soup.find("table", class_="project-list").find("tr", class_=None)
        title_ref = project.find("a", class_="visitable")
        name = title_ref.get_text(strip=True)
        last_project = FreelanceHuntParser.load_last_project(category["name"])
        if name != last_project:
            logging.info(f"New project found: \"{last_project}\" -> \"{name}\"")
            FreelanceHuntParser.save_last_project(name, category["name"])
            url = title_ref.get("href")
            result = {
                "name": name,
                "url": url,
                "budget": get_project_budget(project),
                "description": FreelanceHuntParser.load_project_description(url),
            }
            return result

    @staticmethod
    def load_project_description(url):
        html = get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        result = soup.find("div", id="project-description").find_all("p")
        return "\n".join([item.get_text() for item in result])

    @staticmethod
    def load_last_project(filename):
        try:
            with open(settings.CACHE_DIR + filename, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return ""

    @staticmethod
    def save_last_project(project, filename):
        with open(settings.CACHE_DIR + filename, "w", encoding="utf-8") as file:
            file.write(project)
