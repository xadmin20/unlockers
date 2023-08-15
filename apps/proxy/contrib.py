import requests
from bs4 import BeautifulSoup as bs

from django.conf import settings
from constance import config

from apps.proxy.models import Proxy


PROXY_URL = "https://www.sslproxies.org/"
TEST_URL = "https://www.google.com/"


class ProxyGetter:

    def __init__(self):
        self.getters = {
            settings.PROXY_TYPE_CHOICES.auto: self._auto_proxies,
            settings.PROXY_TYPE_CHOICES.manual: self._manual_proxies,
        }

    def remote_proxies(self):
        response = requests.get(PROXY_URL)
        soup = bs(response.content, "lxml")
     
        trs = soup.select('tr', {'role': 'row'})

        for tr in trs[1:21]:
            tds = tr.select('td')
            yield tds[0].text + ':' + tds[1].text

    def _auto_proxies(self):
        # Get valid proxies from db
        for proxy in Proxy.objects.auto().valid():
            yield proxy.host
        # Iterate remote proxies
        for remote_host in self.remote_proxies():
            # Check is proxy exists in db proxies
            if (exists_proxy := Proxy.objects.filter(host=remote_host).first()):
                # If valid proxy yield it
                if exists_proxy.check_is_valid():
                    yield exists_proxy.host
                continue
            proxy = Proxy.objects.create(host=remote_host)
            yield proxy.host

    def _manual_proxies(self):
        for proxy in Proxy.objects.manual().valid().order_by("?"):
            yield proxy.host

    def proxies(self):
        for host in self.getters.get(config.PROXY_TYPE)():
            yield host

    def test_request(self, host):
        try:
            response = requests.get(
                TEST_URL, timeout=30, 
                proxies={
                    'http': f"http://{host}", 
                    'https': f"https://{host}"
                }
            )
            return True
        except:
            return False

    def update_proxies(self):
        """
            Update proxy list
            Iterate hosts make test request and save invalid status failed request
            Get actual remote list of proxies and save not exists in db
        """
        if config.PROXY_TYPE == settings.PROXY_TYPE_CHOICES.manual:
            return

        for proxy in Proxy.objects.auto().valid():
            if (is_valid := self.test_request(proxy.host)):
                proxy.is_valid = False
                proxy.save()

        for remote_host in self.remote_proxies():
            if not Proxy.objects.auto().filter(host=remote_host).exists():  
                Proxy.objects.create(
                    host=remote_host, 
                    is_valid=self.test_request(remote_host)
                )

    def write_as_invalid(self, host):
        proxy = Proxy.objects.filter(host=host).first()
        if not proxy:
            proxy = Proxy.objects.create(host=host)
        if proxy.is_valid:
            proxy.is_valid = False
            proxy.save()


proxy_getter = ProxyGetter()
