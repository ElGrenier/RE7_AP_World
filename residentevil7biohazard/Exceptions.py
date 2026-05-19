from Options import OptionError

class RE7ROptionError(OptionError):
    def __init__(self, msg):
        msg = f"There was a problem with your RE7R YAML options. {msg}"

        super().__init__(msg)

