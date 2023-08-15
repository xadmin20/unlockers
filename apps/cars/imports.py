import json
from dataclasses import dataclass
from decimal import Decimal

from .models import Car, CarYears


@dataclass
class CarItem:
    manufacturer: str
    car_model: str


def parse_car():
    with open("apps/cars/cars.json", "r") as json_file:
        cars = json.loads(json_file.read())
        for car in cars:
            fields = car["fields"]
            if Car.objects.filter(import_id=car["pk"]).first():
                continue
            obj = Car.objects.create(
                car_model=fields["car_model"],
                manufacturer=fields["manufacturer"],
                import_id=car["pk"],
            )


def parse_car_years():
    with open("apps/cars/car_years.json", "r") as json_file:
        years = json.loads(json_file.read())
        for year in years:
            fields = year["fields"]
            if (
                not CarYears.objects.filter(import_id=year["pk"]).first()
                and (car:=Car.objects.filter(import_id=fields["car"]).first())
            ):
                obj = CarYears.objects.create(
                    year_from=fields["year_from"] ,
                    year_to=fields["year_to"],
                    price=Decimal(fields["price"]) if fields["price"] else None, 
                    car=car,
                )


def update_cars():
    for car in Car.objects.all():
        car.update_status()


def run():
    parse_car()
    parse_car_years()
