import pandas as pd


class ProcessData:
    def __init__(self, df):
        self.df = df

    def run_preprocess(self):
        self.df = self.format_data()
        self.df = self.replace_missing_values()

    def format_data(self):
        self.df["hour"] = self.df["Hours"].apply(lambda x: x[:2])
        self.df = self.df.drop("Hours", axis=1)
        self.df["time"] = pd.to_datetime(
            self.df["date"] + self.df["hour"], format="%d/%m/%Y%H"
        )
        self.df = self.df.set_index("time").sort_index()
        return self.df["value"].resample("H").last().sort_index()

    def replace_missing_values(self):
        # first method : fill with the value from 7 days ago
        return self.df.fillna(self.df.shift(7 * 24))


def split_train_test(data, prop=0.2):
    """Slit train/test set"""
    split_idx = int((1 - prop) * len(data))
    train_set = data[:split_idx]
    test_set = data[split_idx:]
    return train_set, test_set


def date_to_string(date, format_date="%d.%m.%Y+00:00"):
    return date.strftime(format_date)
