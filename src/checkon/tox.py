import typing as t

import attr
import marshmallow_dataclass
import pyrsistent


@attr.s(auto_attribs=True)
class VersionInfo:
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

    @classmethod
    def from_tuple(cls, tup):
        return cls(tup)


@attr.s(auto_attribs=True)
class Python:
    is_64: bool
    version_info: t.Tuple[int, int, int, str, int]
    executable: str
    name: str
    sysplatform: str
    version: str


@attr.s(auto_attribs=True)
class Setup:
    retcode: int
    output: str
    command: t.List[str] = attr.ib(converter=pyrsistent.freeze)


@attr.s(auto_attribs=True)
class Test:
    retcode: int
    output: str
    command: t.List[str] = attr.ib(converter=pyrsistent.freeze)


@attr.s(auto_attribs=True)
class TestEnv:
    test: t.List[Test]
    installed_packages: t.List[str] = attr.ib(converter=pyrsistent.freeze)
    python: Python
    setup: t.List[Setup]


@attr.s(auto_attribs=True, frozen=True)
class ToxRun:
    toxversion: str
    commands: t.List[t.Any] = attr.ib(converter=pyrsistent.freeze)
    platform: str
    host: str
    testenvs: t.Dict[str, TestEnv]
    reportversion: str

    @classmethod
    def from_path(cls, path):
        schema = marshmallow_dataclass.class_schema(cls)()
        with open(path) as f:
            return schema.loads(f.read())
