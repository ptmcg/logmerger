from datetime import datetime

from textual.validation import Validator, ValidationResult


class TimestampValidator(Validator):
    @staticmethod
    def convert_time_str(s: str) -> datetime:
        from ..log_merger import VALID_INPUT_TIME_FORMATS, parse_time_using
        return parse_time_using(s, VALID_INPUT_TIME_FORMATS)

    def __init__(self, min_time=None, max_time=None):
        super().__init__("Invalid timestamp")
        self.min_time = self.convert_time_str(min_time) if min_time else datetime.min
        self.max_time = self.convert_time_str(max_time) if max_time else datetime.max

    def validate(self, value: str) -> ValidationResult:
        try:
            ts = self.convert_time_str(value)
            if not self.min_time <= ts <= self.max_time:
                message = {
                    (True, True): f"value must be between {self.min_time} and {self.max_time}",
                    (True, False): f"value must be greater than {self.min_time}",
                    (False, True): f"value must be less than {self.max_time}",
                }[self.min_time != datetime.min, self.max_time != datetime.max]
                raise ValueError(message)
        except ValueError as ve:
            return self.failure(str(ve).capitalize())
        else:
            return self.success()
