class ContentError(Exception):
    def __str__(self):
        return "Content of this email is not multipart and has wrong type"


class AppTypeError(Exception):
    def __init__(self, *args):
        self.wrong_app = args[0] if args else None

    def __str__(self):
        if self.wrong_app:
            return f"This type of app is not supported: {self.wrong_app}"
        else:
            return f"Try another type of app"
