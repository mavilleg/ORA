from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    arena_models: str = ''
    arena_judge_model: str = ''
    model_timeout_seconds: int = 45

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def model_aliases(self) -> list[str]:
        return [x.strip() for x in self.arena_models.split(',') if x.strip()]


settings = AppSettings()
