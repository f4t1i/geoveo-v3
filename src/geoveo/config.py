from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    geoveo_env: str = "dev"
    geoveo_log_level: str = "INFO"
    geoveo_output_root: str = "./runs"

    routing_provider: str = "osrm_stub"
    imagery_provider: str = "mapillary_stub"
    depth_provider: str = "zoedepth_stub"
    default_video_backend: str = "cogvideox_stub"

    mapillary_access_token: str = ""
    google_maps_api_key: str = ""
    veo_api_key: str = ""
    veo_base_url: str = ""
    cogvideox_base_url: str = ""
    cogvideox_api_key: str = ""

settings = Settings()
