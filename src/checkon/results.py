import datetime
import pathlib
import typing as t

import dataclasses
import marshmallow_dataclass
import xmltodict


@dataclasses.dataclass(frozen=True)
class TestCase:
    name: str
    classname: str
    file: str
    line: int
    time: str  # TODO pendulum


@dataclasses.dataclass(frozen=True)
class TestSuite:
    errors: int
    failures: int
    skipped: int
    tests: int
    time: str  # TODO pendulum
    timestamp: datetime.datetime  # TODO pendulum
    hostname: str
    name: str
    test_cases: t.List[TestCase] = dataclasses.field(metadata={"data_key": "testcase"})


@dataclasses.dataclass(frozen=True)
class SuiteGroup:
    """A group of test suites, such as from a run of ``tox`` with multiple envs."""

    test_suites: t.List[TestSuite] = dataclasses.field(
        metadata={"data_key": "testsuite"}
    )

    @classmethod
    def from_bytes(cls, data):
        schema = marshmallow_dataclass.class_schema(SuiteGroup)(many=True)
        parsed = xmltodict.parse(
            data, attr_prefix="", dict_constructor=dict, force_list=True
        )
        return schema.load(parsed["testsuites"])

    @classmethod
    def from_path(cls, path):
        return cls.from_bytes(pathlib.Path(path).read_bytes())
