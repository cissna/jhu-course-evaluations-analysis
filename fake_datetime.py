class fake_datetime_now:
    def __init__(self, month, year):
        self.month = month
        self.year = year
    

class datetime:
    def __init__(self):
        pass

    @staticmethod
    def now():
        return fake_datetime_now(4, 2025)
    
