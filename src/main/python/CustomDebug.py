class CustomDebug():
    def __init__(self, _text_field):
        self._text_field = _text_field

    def write(self, prefix, msg):
        self._text_field.appendPlainText(F"{prefix}\t{msg}")