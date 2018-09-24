import typing

import toml


class DbConfig:
    name: str
    user: str
    host: str
    port: int
    password: str

    def __init__(self, name, user=None, host='127.0.0.1', port=5432, password=None):
        self.name = name
        self.user = user
        self.host = host
        self.port = port
        self.password = password


class Config:
    host: str
    port: int
    ssl: bool = True
    reconnection_interval: int = 60

    encoding: str = 'utf-8'

    nick: str
    cmd_trigger: str

    channels: typing.List[str] = []

    db: DbConfig

    # https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
    logging: typing.Dict = {
        'version': 1,
    }

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        db = kwargs['db']
        self.db = DbConfig(
            name=db.pop('name'),
            user=db.pop('user', None),
            host=db.pop('host', '127.0.0.1'),
            port=db.pop('port', 5432),
            password=db.pop('password', None),
        )
        self.channels = self.channels or []

    @classmethod
    def from_toml(cls, path):
        data = toml.load(path)
        self = cls(**data)
        return self
