import pandas as pd

class ProcessData:
    def __init__(self, df):
        self.df = df
        
    def run_preprocess(self):
        return self.format_data()
    
    def format_data(self):
        self.df['hour'] = self.df['Hours'].apply(lambda x: x[:2])
        self.df = self.df.drop('Hours', axis=1)
        self.df['time'] = pd.to_datetime(self.df['date']+self.df['hour'], format="%d/%m/%Y%H")
        self.df = self.df.set_index('time').sort_index()
        return self.df['value'].resample("H").last().sort_index()


def split_train_test(data, prop=0.2):
    """Slit train/test set"""
    split_idx = int((1-prop)*len(data))
    train_set = data[:split_idx]
    test_set = data[split_idx:]
    return train_set, test_set