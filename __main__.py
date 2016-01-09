#!/usr/bin/env python2.7

"""
A client for Resmio's REST API. Currently only supports ordering seats.
>>> client = ResmioClient('your favorite bar')
>>> client.request_seats(datetime.now(), number=10, name='Ron')
"""

import requests
import json
import sys

from datetime import datetime, timedelta
from pytz import timezone

from docopt import docopt

__version__ = "0.1"


class ResmioClient(object):
    """
    A client for Remio's REST API.
    """
    APIV1_URL = "https://app.resmio.com/v1/facility/"

    def __init__(self, facility):
        """
        Create a new ResmioClient object.
        :param facility: The name of the restaurant.
        """
        self._facility = facility
        self._base_url = self.APIV1_URL + facility + '/'

    def _get_timezone(self):
        """
        Get this facility's timezone.
        """
        res = requests.get(self._base_url)
        return res.json()["timezone"]

    def _get_availabilties(self, date):
        """
        Get available places for a specific day.
        :param date: The day to get available places for.
        """
        datestr = date.strftime("%F")
        res = requests.get(self._base_url + "availability?date__gte=" + datestr)
        return res.json()["objects"]

    def _get_availablity(self, date):
        """
        Get availablity for specific date and time.
        :param date: The date and time to get available places for.
        """
        tz = timezone(self._get_timezone())
        tz_utc_offset = tz.utcoffset(datetime.now()).seconds
        delta = timedelta(seconds=tz_utc_offset)
        date = date - delta
        datestr = date.isoformat() + '+00:00'
        availabilities = self._get_availabilties(date)
        for availablity in availabilities:
            if availablity["date"] == datestr:
                return availablity

    def _create_data(self, date, number=2,
                     name="", email="", phone="", comment=""):
        """
        Generate a data dict for the HTTP request payload.
        :param date: The date to include in the playload.
        :param number: The amount of seats to request.
        :param name: The name to use.
        :param email: The email address to use.
        :param phone: The phone number to use.
        :param comment: A comment to attach to the order.
        """
        data = {
            "comment": comment,
            "email": email,
            "facility_resources": [],
            "name": name,
            "newsletter_subscribe": False,
            "price_change": 0,
            "num": number,
            "phone": phone,
            "source": "localhost"
        }
        availablity = self._get_availablity(date)
        if availablity["available"] < number:
            raise ValueError("No space available for %d people on %s" %
                             (number, availablity["date"]))
        data["date"] = availablity["date"]
        data["checksum"] = availablity["checksum"]
        return data

    def request_seats(self, date, number=2, name="",
                      email="", phone="", comment=""):
        """
        Requests seats using the REST API.
        :param date: The date to include in the playload.
        :param number: The amount of seats to request.
        :param name: The name to use.
        :param email: The email address to use.
        :param phone: The phone number to use.
        :param comment: A comment to attach to the order.
        """
        data = self._create_data(date, number, name, email, phone, comment)
        res = requests.post(self._base_url + "bookings",
                            data=json.dumps(data))
        if res.status_code == 201:
            return res.json()["ref_num"]
        else:
            raise EnvironmentError(
                "Server returned non-201 status code: %s, text was: %s" %
                (res.status_code, res.text))

    def __repr__(self):
        return "<ResmioClient v1/%s>" % self._facility


if __name__ == "__main__":
    doc = """
resmioclient: A Python client for Resmio.

Usage:
    resmioclient <facility> [options]
    resmioclient (-h | --help | --version)

Options:
    -d DAY --day=DAY     The day to order. [default: today]
    -t TIME --time=TIME  The time to order. [default: 22:00]
    -n NUM --number NUM  The amount of seats to order. [default: 2]

    --name NAME          Your name.
    --email EMAIL        Your email address.
    --phone PHONE        Your phone number.
    --comment COMMENT    A comment to send with the order.
"""
    opts = docopt(doc, version=__version__)
    if opts["--day"] == "today":
        day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            day = datetime.strptime(opts["--day"], "%Y-%m-%d")
        except ValueError:
            print "Error: day should be in format: YYYY-MM-DD"
            sys.exit(2)
    try:
        time = datetime.strptime(opts["--time"], "%H:%M")
    except ValueError:
        print "Error: time should be in format: HH:MM"
        sys.exit(2)
    date = day.replace(hour=time.hour, minute=time.minute)
    client = ResmioClient(opts["<facility>"])
    try:
        ref_num = client.request_seats(date,
                                       number=int(opts["--number"]),
                                       name=opts["--name"],
                                       email=opts["--email"],
                                       phone=opts["--phone"],
                                       comment=opts["--comment"])
    except EnvironmentError, e:
        print "Error:", e.message
        sys.exit(1)
    print "Your seats have been reserved, your reference number is:", ref_num
