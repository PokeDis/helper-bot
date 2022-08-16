from custom_durations.constants import *
from custom_durations.exceptions import ScaleFormatError


class Scale(object):
    SCALES = (
        SCALE_CENTURY,
        SCALE_DECADE,
        SCALE_YEAR,
        SCALE_MONTH,
        SCALE_WEEK,
        SCALE_DAY,
        SCALE_HOUR,
        SCALE_MINUTE,
        SCALE_SECOND,
        SCALE_MILLISECOND
    )

    SCALES_CONVERTION_UNITS = {
        SCALE_CENTURY.short: SCALE_CENTURY_CONVERSION_UNIT,
        SCALE_DECADE.short: SCALE_DECADE_CONVERSION_UNIT,
        SCALE_YEAR.short: SCALE_YEAR_CONVERSION_UNIT,
        SCALE_MONTH.short: SCALE_MONTH_CONVERSION_UNIT,
        SCALE_WEEK.short: SCALE_WEEK_CONVERSION_UNIT,
        SCALE_DAY.short: SCALE_DAY_CONVERSION_UNIT,
        SCALE_HOUR.short: SCALE_HOUR_CONVERSION_UNIT,
        SCALE_MINUTE.short: SCALE_MINUTE_CONVERSION_UNIT,
        SCALE_SECOND.short: SCALE_SECOND_CONVERSION_UNIT,
        SCALE_MILLISECOND.short: SCALE_MILLISECOND_CONVERSION_UNIT
    }

    def __init__(self, str_representation, *args, **kwargs):
        self.representation = self.get(str_representation)
        self.conversion_unit = self.SCALES_CONVERTION_UNITS[self.representation.short]

    def __str__(self):
        return '<Scale {0}>'.format(self.representation.long_singular)

    def __repr__(self):
        return self.__str__()

    def get(self, str_representation):
        for scale in self.SCALES:
            if str_representation in scale:
                return scale
        raise ScaleFormatError("Unsupported scale format: {0}".format(str_representation))
