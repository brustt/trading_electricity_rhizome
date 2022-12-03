from src.forecast.models import ForecastModel
from src.forecast.utils import SamplerSetForecast


class ForecastRunner:
    def __init__(
        self,
        model: ForecastModel,
        n_frames: int,
        sampler: SamplerSetForecast,
    ):
        self.model = model
        self.n_frames = n_frames
        self.sampler = sampler

    def init_sampler(self, df):
        return SamplerSetForecast(df)

    def run_forecast(self):
        pred_prices = self.model.forecast(n_frames=self.n_frames, sampler=self.sampler)
        return pred_prices

    def run_training(self):
        self.model.train_model(self.sampler.x_train, self.sampler.y_train)

    def run_sequential_window(self, n_periods):
        pass
