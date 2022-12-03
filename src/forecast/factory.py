from src.forecast.models import ARIMAModel, LGBMForecast
from src.forecast.utils import ForecastFeatureDummy, ForecastFeatureLGBM


class ModelForecastFactory:
    def get_model(self, **kwargs):
        name = kwargs["name"]
        choice_model = {
            "arima": {
                "builder": ARIMAModel,
                "params": [
                    "order",
                    "seasona_order",
                ],
            },
            "lgbm": {"builder": LGBMForecast, "params": []},
        }
        params = {k: v for k, v in kwargs.items() if k in choice_model[name]["params"]}
        return choice_model[name]["builder"](**params)


class ForecastFeatureFactory:
    def get_feature_builder(self, df, **kwargs):
        name_feature_builder = kwargs["name_feature_builder"]

        choice_feature_builder = {
            "lgbm": {
                "builder": ForecastFeatureLGBM,
                "params": ["n_frames", "n_lags_features"],
            },
            "arima": {"builder": ForecastFeatureDummy, "params": []},
        }
        params = {
            k: v
            for k, v in kwargs.items()
            if k in choice_feature_builder[name_feature_builder]["params"]
        }
        return choice_feature_builder[name_feature_builder]["builder"](
            **params
        ).create_features(df)
