# pylint: disable=redefined-outer-name
import textwrap

import pytest

import slash

from .utils import run_tests_in_session


@pytest.fixture
def events_path(tmpdir):
    return tmpdir.join("events.txt")


@pytest.fixture
def write_tests(tmpdir, events_path):
    def _write(source):
        header = textwrap.dedent(
            f"""
            import slash

            def record(event):
                with open({str(events_path)!r}, "a") as f:
                    f.write(event + "\\n")

            def attempt_number(name):
                # How many times this test body has started so far, including now
                record("run:" + name)
                with open({str(events_path)!r}) as f:
                    return sum(1 for line in f if line.strip() == "run:" + name)
            """
        )
        path = tmpdir.join("test_sample.py")
        path.write(header + textwrap.dedent(source))
        return str(path)

    return _write


def _events(events_path):
    if not events_path.exists():
        return []
    return [line for line in events_path.read().splitlines() if line]


def _run(path):
    session = run_tests_in_session(path)
    return session, list(session.results.iter_test_results())


def test_flaky_test_passes_on_retry(write_tests, events_path):
    path = write_tests(
        """
        @slash.retry(2)
        def test_flaky():
            assert attempt_number("flaky") >= 2
        """
    )
    session, [result] = _run(path)
    assert result.is_success()
    assert session.results.is_success()
    assert result.get_num_retries() == 1
    [(errors, failures)] = result.get_retried_attempts()
    assert errors == [] and len(failures) == 1
    assert _events(events_path).count("run:flaky") == 2


def test_test_failing_every_attempt_fails_once(write_tests, events_path):
    path = write_tests(
        """
        @slash.retry(2)
        def test_broken():
            attempt_number("broken")
            raise RuntimeError("still broken")
        """
    )
    session, [result] = _run(path)
    assert result.is_error()
    assert len(result.get_errors()) == 1
    assert result.get_num_retries() == 2
    assert session.results.get_num_errors() == 1
    assert _events(events_path).count("run:broken") == 3


def test_passing_test_is_not_retried(write_tests, events_path):
    path = write_tests(
        """
        @slash.retry(3)
        def test_fine():
            attempt_number("fine")
        """
    )
    _, [result] = _run(path)
    assert result.is_success()
    assert result.get_num_retries() == 0
    assert _events(events_path).count("run:fine") == 1


def test_no_retries_by_default(write_tests, events_path):
    path = write_tests(
        """
        def test_flaky():
            assert attempt_number("flaky") >= 2
        """
    )
    _, [result] = _run(path)
    assert result.is_failure()
    assert result.get_num_retries() == 0
    assert _events(events_path).count("run:flaky") == 1


def test_retries_config_applies_to_every_test(write_tests, events_path, config_override):
    config_override("run.retries", 1)
    path = write_tests(
        """
        def test_a():
            assert attempt_number("a") >= 2

        def test_b():
            assert attempt_number("b") >= 2
        """
    )
    session, results = _run(path)
    assert session.results.is_success()
    assert [r.get_num_retries() for r in results] == [1, 1]


def test_marker_overrides_config(write_tests, events_path, config_override):
    config_override("run.retries", 3)
    path = write_tests(
        """
        @slash.retry(0)
        def test_flaky():
            assert attempt_number("flaky") >= 2
        """
    )
    _, [result] = _run(path)
    assert result.is_failure()
    assert _events(events_path).count("run:flaky") == 1


def test_test_scoped_fixtures_and_cleanups_are_fresh_for_each_attempt(write_tests, events_path):
    path = write_tests(
        """
        @slash.fixture(scope="module")
        def rig():
            record("rig:setup")
            slash.add_cleanup(record, args=("rig:cleanup",))
            return "rig"

        @slash.fixture
        def connection(this, rig):
            record("connection:setup")
            this.add_cleanup(lambda: record("connection:cleanup"))
            return {"used": False}

        @slash.retry(2)
        def test_uses_hardware(connection):
            # A test-scoped fixture must never leak state from a failed attempt
            assert not connection["used"]
            connection["used"] = True
            slash.add_cleanup(record, args=("test:cleanup",))
            assert attempt_number("hw") >= 3
        """
    )
    _, [result] = _run(path)
    assert result.is_success()
    assert result.get_num_retries() == 2
    assert _events(events_path) == [
        "rig:setup",
        "connection:setup",
        "run:hw",
        "test:cleanup",
        "connection:cleanup",
        "connection:setup",
        "run:hw",
        "test:cleanup",
        "connection:cleanup",
        "connection:setup",
        "run:hw",
        "test:cleanup",
        "connection:cleanup",
        "rig:cleanup",
    ]


def test_hooks_fire_per_attempt(write_tests, events_path):
    path = write_tests(
        """
        @slash.retry(1)
        def test_flaky():
            assert attempt_number("flaky") >= 2
        """
    )
    hook_events = []

    @slash.hooks.register
    def test_start():
        hook_events.append("test_start")

    @slash.hooks.register
    def test_end():
        hook_events.append("test_end")

    @slash.hooks.register
    def test_retry(attempt, max_attempts):
        hook_events.append(("test_retry", attempt, max_attempts))

    @slash.hooks.register
    def test_success():
        hook_events.append("test_success")

    @slash.hooks.register
    def test_failure():
        hook_events.append("test_failure")

    _, [result] = _run(path)
    assert result.is_success()
    assert hook_events == [
        "test_start",
        "test_end",
        ("test_retry", 2, 2),
        "test_start",
        "test_success",
        "test_end",
    ]


def test_skips_are_not_retried(write_tests, events_path):
    path = write_tests(
        """
        @slash.retry(3)
        def test_skipping():
            attempt_number("skip")
            slash.skip_test("not today")
        """
    )
    _, [result] = _run(path)
    assert result.is_skip()
    assert _events(events_path).count("run:skip") == 1


def test_errors_in_test_cleanups_trigger_retry(write_tests, events_path):
    path = write_tests(
        """
        @slash.retry(1)
        def test_bad_cleanup():
            if attempt_number("cleanup") == 1:
                slash.add_cleanup(lambda: 1 / 0)
        """
    )
    _, [result] = _run(path)
    assert result.is_success()
    assert result.get_num_retries() == 1
    [(errors, _)] = result.get_retried_attempts()
    assert len(errors) == 1


def test_class_based_test_is_retried(write_tests, events_path):
    path = write_tests(
        """
        class FlakyTest(slash.Test):
            def before(self):
                record("before")

            def after(self):
                record("after")

            @slash.retry(1)
            def test_method(self):
                assert attempt_number("method") >= 2
        """
    )
    _, [result] = _run(path)
    assert result.is_success()
    assert _events(events_path) == ["before", "run:method", "after", "before", "run:method", "after"]


def test_duration_covers_all_attempts(write_tests):
    path = write_tests(
        """
        import time

        @slash.retry(1)
        def test_slow_flaky():
            time.sleep(0.2)
            assert attempt_number("slow") >= 2
        """
    )
    _, [result] = _run(path)
    assert result.get_duration().total_seconds() >= 0.4


@pytest.mark.parametrize("bad", [-1, 1.5, "2", True])
def test_retry_rejects_invalid_counts(bad):
    with pytest.raises(ValueError):
        slash.retry(bad)


def test_stop_on_error_counts_only_the_final_attempt(write_tests, events_path, config_override):
    config_override("run.stop_on_error", True)
    path = write_tests(
        """
        @slash.retry(1)
        def test_1_flaky():
            assert attempt_number("first") >= 2

        def test_2_after():
            attempt_number("second")
        """
    )
    session, results = _run(path)
    assert session.results.is_success()
    assert len(results) == 2
    assert _events(events_path).count("run:second") == 1
