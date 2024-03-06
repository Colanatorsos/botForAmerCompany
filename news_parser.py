import requests
import json
from bs4 import BeautifulSoup


class NewsParser:
    def __init__(self) -> None:
        self.last_news = {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.96 Mobile Safari/537.36"
        })
        self.parsers = {
            "finviz": self.finviz_get_last_news_url,
            "benzinga": self.benzinga_get_last_news_url,
            "investing": self.investing_get_last_news_url,
            "ru.investing": self.ru_investing_get_last_news_url
        }
        self._load_last_news_data()

    def _parse(self, url: str, attrs: dict[str, any]):
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.find("a", attrs=attrs).attrs["href"]

    def _load_last_news_data(self):
        try:
            self.last_news = json.load(open("last_news_data.json", "r"))
        except FileNotFoundError:
            print("[NewsParser] No saved data")

    def _save_last_news_data(self):
        json.dump(self.last_news, open("last_news_data.json", "w"))

    def parse(self, site: str, subpath: str = ""):
        key = f"{site}/{subpath}"
        url = self.parsers[site](subpath)

        last_news = self.last_news.get(key)

        if last_news != url:
            self.last_news[key] = url
            self._save_last_news_data()

            if last_news is not None:
                return url

    def finviz_get_last_news_url(self, subpath: str):
        return self._parse(f"https://finviz.com/{subpath}", {"class": "tab-link-news"})

    def benzinga_get_last_news_url(self, subpath: str):
        return self._parse(f"https://www.benzinga.com/topic/{subpath}", {"class": "newsfeed-card"})

    def investing_get_last_news_url(self, subpath: str):
        return "https://investing.com" + self._parse(f"https://investing.com/indices/{subpath}",
                                                     {"data-test": "article-title-link"})

    def ru_investing_get_last_news_url(self, subpath: str):
        return "https://ru.investing.com" + self._parse(f"https://ru.investing.com/indices/{subpath}",
                                                        {"data-test": "article-title-link"})
