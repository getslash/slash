# pylint: disable=unused-argument
import slash
import logbook

def test_retained_logs_handler(unique_string1):

    with slash.log.RetainedLogHandler() as handler:
        slash.logger.info(unique_string1)

    other_handler = logbook.TestHandler()
    handler.flush_to_handler(other_handler)

    [r] = other_handler.records # pylint: disable=unbalanced-tuple-unpacking
    assert unique_string1 in r.message


def test_disable():
    with slash.log.RetainedLogHandler() as handler:
        handler.disable()
        slash.logger.info('hey')
    assert not handler.records
