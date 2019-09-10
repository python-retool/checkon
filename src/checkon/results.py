import datetime
import json
import pathlib
import textwrap
import typing as t

import attr
import dataclasses
import marshmallow
import marshmallow_dataclass
import pyrsistent
import xmltodict

import checkon.tox


@dataclasses.dataclass(frozen=True)
class Failure:
    message: str
    lines: t.List[str]

    @classmethod
    def from_dict(cls, data):
        return cls(**pyrsistent.freeze(data))


class FailureField(marshmallow.fields.Field):
    def _deserialize(self, value, attr, data, **kw):
        if isinstance(value, list):
            [value] = value

            return Failure(**value)
        return None


@dataclasses.dataclass(frozen=True)
class TestCaseRun:
    name: str
    classname: str
    file: str
    line: int
    time: str  # TODO pendulum
    failure: t.Optional[Failure] = dataclasses.field(
        metadata={"marshmallow_field": FailureField()}, default=None
    )


@attr.dataclass(frozen=True)
@dataclasses.dataclass(frozen=True)
class TestSuiteRun:
    errors: int
    failures: int
    skipped: int
    tests: int
    time: str  # TODO pendulum
    timestamp: datetime.datetime  # TODO pendulum
    hostname: str
    name: str
    test_cases: t.List[TestCaseRun] = dataclasses.field(
        metadata={"data_key": "testcase"}
    )
    envname: t.Optional[str]

    @classmethod
    def from_bytes(cls, data, envname):
        schema = marshmallow_dataclass.class_schema(cls)(many=True)
        parsed = xmltodict.parse(
            data,
            attr_prefix="",
            dict_constructor=dict,
            force_list=True,
            cdata_key="lines",
        )

        [suite] = parsed["testsuites"]

        return schema.load([{**ts, "envname": envname} for ts in suite["testsuite"]])

    @classmethod
    def from_path(cls, path):
        envname = path.parent.name
        return cls.from_bytes(pathlib.Path(path).read_bytes(), envname=envname)


@attr.dataclass(frozen=True)
class ToxTestSuiteRun:
    """A toxenv result."""

    suite: TestSuiteRun
    tox_run: checkon.tox.ToxRun
    envname: str

    @classmethod
    def from_dir(cls, toxenv_dir):
        [path] = toxenv_dir.glob("test_*.xml")
        [suite] = TestSuiteRun.from_path(path)

        [tox_data_path] = toxenv_dir.glob("tox_*.json")
        tox_run = checkon.tox.ToxRun.from_path(tox_data_path)
        return cls(suite, tox_run=tox_run, envname=toxenv_dir.name)


@attr.dataclass(frozen=True)
class DependentResult:
    url: str
    suite_runs: t.List[ToxTestSuiteRun]

    @classmethod
    def from_dir(cls, output_dir, url):
        runs = []
        for dir in pathlib.Path(output_dir).glob("*"):
            if not dir.is_dir():
                continue
            runs.append(ToxTestSuiteRun.from_dir(dir))

        return cls(url=url, suite_runs=runs)


@attr.dataclass(frozen=True)
class AppSuiteRun:
    injected: str
    dependent_result: DependentResult


@attr.dataclass(frozen=True)
class FailedTest:
    name: str
    classname: str
    file: str
    line: str
    failure: t.Sequence[Failure] = attr.ib(converter=Failure.from_dict)

    @classmethod
    def from_test_case(cls, test):
        return cls(
            **{
                k: v
                for k, v in dataclasses.asdict(test).items()
                if k in attr.fields_dict(FailedTest).keys()
            }
        )


@attr.dataclass(frozen=True)
class Comparison:
    base_requirement: str
    new_requirement: str
    base_failures: t.FrozenSet[FailedTest]
    new_failures: t.FrozenSet[FailedTest]


def format_suite_failures(requirement, test_cases):
    if not any(case.failure for case in test_cases):
        return "No failures\n"

    return "\n" + "\n".join(
        case.failure.message + "\n" + "\n".join(case.failure.lines)
        for case in test_cases
    )


def format_comparison(comparison):
    if comparison.base_failures == comparison.new_failures:
        return "No differences"

    pre = "There were differences: \n\n"
    base = format_suite_failures(comparison.base_requirement, comparison.base_failures)
    new = format_suite_failures(comparison.new_requirement, comparison.new_failures)
    return (
        pre
        + comparison.base_requirement
        + "\n\n"
        + textwrap.indent(base, " " * 4)
        + "\n\nCompared to: \n\n"
        + comparison.new_requirement
        + "\n\n"
        + textwrap.indent(new, " " * 4)
    )
