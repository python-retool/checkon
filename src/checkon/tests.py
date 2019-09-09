import datetime
import typing as t

import attr
import dataclasses


@dataclasses.dataclass(frozen=True)
class TestCase:
    name: str
    classname: str
    file: str
    line: int


@dataclasses.dataclass(frozen=True)
class TestCaseRun:
    duration: str  # TODO pendulum
    test_case: TestCase


@dataclasses.dataclass(frozen=True)
class FailureOutput:
    message: str
    lines: t.List[str]


@dataclasses.dataclass(frozen=True)
class TestFailure:
    output: FailureOutput
    test_case_run: TestCaseRun


@dataclasses.dataclass(frozen=True)
class TestSuite:
    test_cases: t.List[TestCase]


@dataclasses.dataclass(frozen=True)
class TestSuiteRun:
    test_suite: TestSuite
    start_time: datetime.datetime
    duration: t.Any


@dataclasses.dataclass(frozen=True)
class Application:
    name: str


@dataclasses.dataclass(frozen=True)
class ToxEnv:
    name: str
    application: Application


@dataclasses.dataclass(frozen=True)
class ToxEnvRun:
    toxenv: ToxEnv
    test_suite_run: TestSuiteRun
    start_time: datetime.datetime


@dataclasses.dataclass(frozen=True)
class ToxRun:
    toxenv_runs: t.List[ToxEnvRun]


@dataclasses.dataclass(frozen=True)
class Provider:
    requirement: str


@dataclasses.dataclass(frozen=True)
class ProviderApplicationToxEnvRun:
    provider: Provider
    application: Application
    toxenv_run: ToxEnvRun
