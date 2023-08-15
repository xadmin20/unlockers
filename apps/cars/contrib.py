from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from apps.proxy.contrib import proxy_getter
from .models import Car as CarModel, CarYears

ua = UserAgent()

CAR_PARSING_URL = "https://www.cardatachecks.co.uk/carcheck/lookup.php"


class CarParsingException(Exception):
    pass


@dataclass
class Car:
    manufacturer: str
    car_model: str
    manufactured: str


class CarGetter:
    """Get car info from car registration"""

    def __init__(self, registration):
        self.registration = registration
        self._make_request()

    def _make_request(self):
        """Make request to car parsing site"""
        response = None
        for proxy in proxy_getter.proxies():
            print("p: ", proxy)
            try:
                response = requests.post(
                    CAR_PARSING_URL,
                    data={'vrm': self.registration, 'submit': 'Lookup'},
                    verify=False,
                    # proxies={
                    #     'http': f"http://{proxy}",
                    #     'https': f"http://{proxy}"
                    # },
                    headers={'User-Agent': ua.random},
                    timeout=15,
                )

                if response and response.status_code == 200:
                    print(response.content)
                    self.page_content = response.content
                    self.soup = bs(self.page_content, 'lxml')
                    break

            except requests.RequestException as e:
                print(f"Ошибка запроса: {e}")
                proxy_getter.write_as_invalid(proxy)
                continue
            except OSError as e:
                print("OSError:", e)
                raise

        if not response:
            raise CarParsingException("Something went wrong")

    def get_element(self, path):
        print('get_element')
        return self.soup.select(path)[0]

    def get_manufacturer(self):
        print('get_manufacturer')
        return self.get_element('#cc_box1 > div:nth-child(6) > div.col-xs-7.col-sm-7.col-md-7').get_text(strip=True)

    def get_car_model(self):
        print('get_car_model')
        return self.get_element('#cc_box1 > div:nth-child(7) > div.col-xs-7.col-sm-7.col-md-7').get_text(strip=True)

    def get_manufactured(self):
        print('get_manufactured')
        return self.get_element('#cc_box1 > div:nth-child(4) > div.col-xs-7.col-sm-7.col-md-7').get_text(strip=True)

    def get_car(self):
        try:
            new_car = CarModel.objects.create(
                car_model=self.get_car_model(),
                manufacturer=self.get_manufacturer(),
            )
            new_car.update_status()
            # делаем запись в booking/Order

            print(f"New car created: {new_car}")
            return Car(
                manufacturer=self.get_manufacturer(),
                car_model=self.get_car_model(),
                manufactured=self.get_manufactured(),
            )
        except Exception as e:
            print(e)
            raise CarParsingException("Something went wrong")


def get_car(registration):
    return CarGetter(registration).get_car()


def register_car(car: Car) -> (CarYears, bool):
    if (car_years := CarYears.objects.filter(
            year_from__lte=car.manufactured,
            year_to__gte=car.manufactured,
            car__manufacturer=car.manufacturer,
            car__car_model=car.car_model.split(' ', 1)[0], ).first()):
        return car_years

    car_kw = dict(
        manufacturer=car.manufacturer,
        car_model=car.car_model.split(' ', 1)[0],
    )
    car_object = CarModel.objects.filter(**car_kw).first()
    if not car_object:
        car_object = CarModel.objects.create(**car_kw)
    car_years = CarYears.objects.create(
        year_to=car.manufactured,
        year_from=car.manufactured,
        car=car_object
    )
    car_object.is_appreciated = False
    car_object.save()

    return car_years
