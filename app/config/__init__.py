import os
from app.config.base import Settings

# 1. Get and normalize the APP_ENV environment variable, default to 'local'
env = os.getenv("APP_ENV", "local")
if not env:
    env = "local"
env = env.lower()

# 2. Map APP_ENV to the corresponding configuration class
if env == "local":
    from app.config.local import LocalSettings as EnvSettings
elif env == "dev":
    from app.config.dev import DevSettings as EnvSettings
elif env == "sit":
    from app.config.sit import SitSettings as EnvSettings
elif env == "uat":
    from app.config.uat import UatSettings as EnvSettings
elif env == "prod":
    from app.config.prod import ProdSettings as EnvSettings
else:
    # Fallback to local configuration for any unknown environment
    from app.config.local import LocalSettings as EnvSettings

# 3. Locate the corresponding .env.<environment> file
# It should be loaded from the project root (current working directory)
env_file = f".env.{env}"

# 4. Instantiate the settings, loading values from the env file if it exists
if os.path.exists(env_file):
    settings = EnvSettings(_env_file=env_file)
else:
    settings = EnvSettings()
