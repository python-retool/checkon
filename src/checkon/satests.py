import functools
import typing as t

import attr
import inflection
import sqlalchemy as sa
import sqlalchemy.ext.declarative
import sqlalchemy.orm

import checkon.results


Base = sqlalchemy.ext.declarative.declarative_base()


def relation(cls=None, name=None):
    def build(cls):
        if name is None:
            table_name = inflection.underscore(cls.__name__)
        else:
            table_name = name

        # Add the columns.
        mapping = {
            k: v
            for k, v in cls.__dict__.items()
            if isinstance(v, (sa.Column, sa.orm.relationships.RelationshipProperty))
        }

        # Add the table name.
        mapping["__tablename__"] = table_name

        # Add the primary key.
        mapping[table_name + "_id"] = sa.Column(
            sa.Integer, primary_key=True, autoincrement=True
        )

        # Add the references.
        for ref, v in cls.__dict__.items():
            if isinstance(v, sa.orm.relationships.RelationshipProperty):
                foreign_name = inflection.underscore(v.argument)
                mapping[f"{ref}_id"] = sa.Column(
                    sa.Integer, sa.ForeignKey(f"{foreign_name}.{foreign_name}_id")
                )

        return type(cls.__name__, (Base,), mapping)

    if cls is None:
        # Called with kwargs `@relation(name="foo")`.
        return build

    # Called as `@relation` without parens.
    return build(cls)


@relation
class TestCase:

    name = sa.Column(sa.String)
    classname = sa.Column(sa.String)
    file = sa.Column(sa.String)
    line = sa.Column(sa.Integer)


@relation
class TestCaseRun:

    duration = sa.Column(sa.String)
    test_case = sa.orm.relationship("TestCase", uselist=False)


@relation
class FailureOutput:

    message = sa.Column(sa.String)
    text = sa.Column(sa.String)


@relation
class TestFailure:
    failure_output = sa.orm.relationship("FailureOutput", uselist=False)


@relation
class TestSuite:
    test_cases = sa.orm.relationship("TestCase", uselist=True)


@relation
class TestSuiteRun:
    test_case_runs = sa.orm.relationship("TestCaseRun", uselist=True)
    start_time = sa.Column(sa.DateTime)
    duration = sa.Column(sa.String)


@relation
class Application:
    name = sa.Column(sa.String)


@relation
class Toxenv:
    name = sa.Column(sa.String)
    application = sa.orm.relationship("Application", uselist=False)


@relation
class ToxenvRun:
    toxenv = sa.orm.relationship("Toxenv")
    test_suite_run = sa.orm.relationship("TestSuiteRun", uselist=False)
    start_time = sa.Column(sa.DateTime)


@relation
class ToxRun:
    toxenv_runs = sa.orm.relationship("ToxenvRun", uselist=True)


@relation
class Provider:
    requirement = sa.Column(sa.String)


@relation
class ProviderApplicationToxenvRun:
    provider = sa.orm.relationship("Provider", uselist=False)
    application = sa.orm.relationship("Application", uselist=False)
    toxenv_run = sa.orm.relationship("ToxenvRun", uselist=False)


@attr.dataclass
class Database:
    engine: t.Any
    session: t.Any

    @classmethod
    def from_string(cls, connection_string="sqlite:///:memory:", echo=False):
        engine = sa.create_engine(connection_string, echo=echo)
        session = sa.orm.sessionmaker(bind=engine)()
        return cls(engine, session)


@functools.singledispatch
def transform(result: object):
    raise NotImplementedError(result, type(result).__name__, vars(result))


@transform.register
def _(result: checkon.results.DependentResult):
    return [transform(tox_suite_run) for tox_suite_run in result.suite_runs]


@transform.register
def _(run: checkon.results.ToxSuiteRun):
    return ToxenvRun(test_suite_run=transform(run.suite))


@transform.register
def _(run: checkon.results.TestSuiteRun):
    suite = TestSuite(
        test_cases=[transform(case, cls=TestCase) for case in run.test_cases]
    )
    test_case_runs = [transform(case, cls=TestCaseRun) for case in run.test_cases]
    return TestSuiteRun(
        test_case_runs=test_case_runs, duration=run.time, start_time=run.timestamp
    )


@transform.register
def _(run: checkon.results.TestCaseRun, cls: t.Type):
    if cls == TestCaseRun:
        return TestCaseRun(duration=run.time, test_case=transform(run, cls=TestCase))
    return TestCase(
        name=run.name, classname=run.classname, file=run.file, line=run.line
    )


def insert_result(db: Database, result: checkon.results.DependentResult):
    [out] = transform(result)

    db.session.add(out)
    db.session.commit()


if __name__ == "__main__":
    from . import tmp

    db = Database.from_string(echo=True)
    Base.metadata.bind = db.engine
    Base.metadata.create_all()
    insert_result(db, tmp.res)
