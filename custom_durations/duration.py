from collections import namedtuple

from custom_durations.constants import *
from custom_durations.exceptions import ScaleFormatError
from custom_durations.parser import extract_tokens
from custom_durations.scales import Scale

DurationRepresentation = namedtuple("DurationRepresentation", ["value", "scale"])


class Duration(object):
    def __init__(self, representation, *args, **kwargs):
        self.representation = representation
        self.parsed_durations = self.parse(self.representation)
        self.seconds = self._compute_seconds_value()

    def __str__(self):
        return "<Duration {0}>".format(self.representation)

    def __repr__(self):
        return self.__str__()

    def _compute_seconds_value(self):
        seconds = 0

        for duration in self.parsed_durations:
            seconds += duration.value * duration.scale.conversion_unit

        return seconds

    def parse(self, representation):
        elements = extract_tokens(representation)

        try:
            scales = [
                DurationRepresentation(float(p[0]), Scale(p[1])) for p in elements
            ]
        except ValueError:
            raise ScaleFormatError(
                "Malformed duration representation: {0}".format(representation)
            )

        return scales

    def to_centuries(self):
        return round(self.seconds / float(SCALE_CENTURY_CONVERSION_UNIT), 2)

    def to_decades(self):
        return round(self.seconds / float(SCALE_DECADE_CONVERSION_UNIT), 2)

    def to_years(self):
        return round(self.seconds / float(SCALE_YEAR_CONVERSION_UNIT), 2)

    def to_months(self):
        return round(self.seconds / float(SCALE_MONTH_CONVERSION_UNIT), 2)

    def to_weeks(self):
        return round(self.seconds / float(SCALE_WEEK_CONVERSION_UNIT), 2)

    def to_days(self):
        return round(self.seconds / float(SCALE_DAY_CONVERSION_UNIT), 2)

    def to_hours(self):
        return round(self.seconds / float(SCALE_HOUR_CONVERSION_UNIT), 2)

    def to_minutes(self):
        return round(self.seconds / float(SCALE_MINUTE_CONVERSION_UNIT), 2)

    def to_seconds(self):
        return round(self.seconds / float(SCALE_SECOND_CONVERSION_UNIT), 2)

    def to_milliseconds(self):
        return round(self.seconds / float(SCALE_MILLISECOND_CONVERSION_UNIT), 2)
