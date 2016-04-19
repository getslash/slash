# pylint: disable=redefined-outer-name
import os
import sys

import pytest
import slash

try:
    from lxml import etree
except ImportError:
    if not hasattr(sys, 'pypy_version_info'):
        raise
    etree = None

_needs_lxml = pytest.mark.skipif(etree is None, reason='Requires lxml')

@_needs_lxml
def test_xunit_plugin(results, xunit_filename): # pylint: disable=unused-argument
    assert os.path.exists(xunit_filename), 'xunit file not created'

    schema_root = etree.XML(_XUNIT_XSD)
    schema = etree.XMLSchema(schema_root)

    parser = etree.XMLParser(schema=schema)
    with open(xunit_filename) as f:
        etree.parse(f, parser)


def test_session_errors(suite, xunit_filename):
    # pylint: disable=unused-argument

    @suite.slashconf.append_body
    def __code__():
        1/0

    for test in suite:
        # tests are not going to even be loaded
        test.expect_deselect()

    summary = suite.run()

    assert 'ZeroDivision' in summary.get_console_output()



@_needs_lxml
def test_xunit_plugin_test_details(suite, suite_test, xunit_filename, details):
    for key, value in details.items():
        suite_test.append_line('slash.context.result.set_test_detail({0!r}, {1!r})'.format(key, value))

    suite.run()
    testcase_xml = _get_testcase_xml(suite_test, xunit_filename)

    saved_details = dict((d.attrib['name'], d.attrib['value']) for d in testcase_xml.findall('detail'))
    assert saved_details


@_needs_lxml
@pytest.mark.parametrize('errtype', ['error', 'failure'])
def test_xunit_plugin_add_failure_error(suite, suite_test, xunit_filename, errtype):
    num_errors = 3
    for i in range(num_errors):
        suite_test.append_line('slash.add_{0}("some message")'.format(errtype))
    if errtype == 'error':
        suite_test.expect_error()
    else:
        suite_test.expect_failure()

    suite.run()
    testcase_xml = _get_testcase_xml(suite_test, xunit_filename)
    errors = testcase_xml.findall(errtype)
    assert len(errors) == num_errors
    for error in errors:
        assert error.attrib['message'] == 'some message'
        assert error.attrib['type'] == errtype
    assert errors



def _get_testcase_xml(suite_test, filename):
    with open(filename) as f:
        xml = etree.parse(f)
    match = [testcase for testcase in xml.findall('testcase') if testcase.attrib['name'].split('_')[-1] == suite_test.id]
    assert len(match) == 1
    return match[0]


@pytest.fixture
def details():
    return {'detail1': 'value1', 'detail2': 'value2'}


@pytest.fixture
def results(suite, suite_test, test_event, xunit_filename): #pylint: disable=unused-argument
    test_event(suite_test)
    summary = suite.run()
    assert 'Traceback' not in summary.get_console_output()

@pytest.fixture(params=['normal', 'skip_decorator_without_reason', 'skip_without_reason', 'skip_with_reason', 'error', 'failure', 'add_error', 'add_failure'])
def test_event(request):
    flavor = request.param

    def func(test):
        if flavor != 'normal':
            if flavor == 'skip_without_reason':
                test.when_run.skip(with_reason=False)
            elif flavor == 'skip_decorator_without_reason':
                test.when_run.skip(with_reason=False, decorator=True)
            elif flavor == 'skip_with_reason':
                test.when_run.skip(with_reason=True)
            elif flavor == 'error':
                test.when_run.error()
            elif flavor == 'failure':
                test.when_run.fail()
            elif flavor == 'add_error':
                test.append_line('slash.add_error("error")')
                test.expect_error()
            elif flavor == 'add_failure':
                test.append_line('slash.add_failure("failure")')
                test.expect_failure()
            else:
                raise NotImplementedError()  # pragma: no cover
    return func


@pytest.fixture
def xunit_filename(tmpdir, request, config_override):
    xunit_filename = str(tmpdir.join('xunit.xml'))
    slash.plugins.manager.activate('xunit')

    slash.config.root.plugin_config.xunit.filename = xunit_filename

    @request.addfinalizer
    def deactivate():
        slash.plugins.manager.deactivate('xunit')

    return xunit_filename


# Taken from https://gist.github.com/jzelenkov/959290
_XUNIT_XSD = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
   elementFormDefault="qualified"
   attributeFormDefault="unqualified">
  <xs:annotation>
    <xs:documentation xml:lang="en">Jenkins xUnit test result schema.
    </xs:documentation>
  </xs:annotation>
  <xs:element name="testsuite" type="testsuite"/>
  <xs:simpleType name="ISO8601_DATETIME_PATTERN">
    <xs:restriction base="xs:dateTime">
      <xs:pattern value="[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="testsuites">
    <xs:annotation>
      <xs:documentation xml:lang="en">Contains an aggregation of testsuite results</xs:documentation>
    </xs:annotation>
    <xs:complexType>
      <xs:sequence>
        <xs:element name="testsuite" minOccurs="0" maxOccurs="unbounded">
          <xs:complexType>
            <xs:complexContent>
              <xs:extension base="testsuite">
                <xs:attribute name="package" type="xs:token" use="required">
                  <xs:annotation>
                    <xs:documentation xml:lang="en">Derived from testsuite/@name in the non-aggregated documents</xs:documentation>
                  </xs:annotation>
                </xs:attribute>
                <xs:attribute name="id" type="xs:int" use="required">
                  <xs:annotation>
                    <xs:documentation xml:lang="en">Starts at '0' for the first testsuite and is incremented by 1 for each following testsuite</xs:documentation>
                  </xs:annotation>
                </xs:attribute>
              </xs:extension>
            </xs:complexContent>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="testsuite">
    <xs:annotation>
      <xs:documentation xml:lang="en">Contains the results of exexuting a testsuite</xs:documentation>
    </xs:annotation>
    <xs:sequence>
      <xs:element name="testcase" minOccurs="0" maxOccurs="unbounded">
        <xs:complexType>
          <xs:choice minOccurs="0">
            <xs:element name="error">
      <xs:annotation>
        <xs:documentation xml:lang="en">Indicates that the test errored.  An errored test is one that had an unanticipated problem. e.g., an unchecked throwable; or a problem with the implementation of the test. Contains as a text node relevant data for the error, e.g., a stack trace</xs:documentation>
      </xs:annotation>
              <xs:complexType>
                <xs:simpleContent>
                  <xs:extension base="pre-string">
                    <xs:attribute name="message" type="xs:string">
                      <xs:annotation>
                        <xs:documentation xml:lang="en">The error message. e.g., if a java exception is thrown, the return value of getMessage()</xs:documentation>
                      </xs:annotation>
                    </xs:attribute>
                    <xs:attribute name="type" type="xs:string" use="required">
                      <xs:annotation>
                        <xs:documentation xml:lang="en">The type of error that occured. e.g., if a java execption is thrown the full class name of the exception.</xs:documentation>
                      </xs:annotation>
                    </xs:attribute>
                  </xs:extension>
                </xs:simpleContent>
              </xs:complexType>
            </xs:element>
            <xs:element name="failure">
      <xs:annotation>
        <xs:documentation xml:lang="en">Indicates that the test failed. A failure is a test which the code has explicitly failed by using the mechanisms for that purpose. e.g., via an assertEquals. Contains as a text node relevant data for the failure, e.g., a stack trace</xs:documentation>
      </xs:annotation>
              <xs:complexType>
                <xs:simpleContent>
                  <xs:extension base="pre-string">
                    <xs:attribute name="message" type="xs:string">
                      <xs:annotation>
                        <xs:documentation xml:lang="en">The message specified in the assert</xs:documentation>
                      </xs:annotation>
                    </xs:attribute>
                    <xs:attribute name="type" type="xs:string" use="required">
                      <xs:annotation>
                        <xs:documentation xml:lang="en">The type of the assert.</xs:documentation>
                      </xs:annotation>
                    </xs:attribute>
                  </xs:extension>
                </xs:simpleContent>
              </xs:complexType>
            </xs:element>
    <xs:element name="error">
      <xs:annotation>
        <xs:documentation xml:lang="en">Indicates that the test failed. A failure is a test which the code has explicitly failed by using the mechanisms for that purpose. e.g., via an assertEquals. Contains as a text node relevant data for the failure, e.g., a stack trace</xs:documentation>
      </xs:annotation>
              <xs:complexType>
                <xs:simpleContent>
                  <xs:extension base="pre-string">
                    <xs:attribute name="message" type="xs:string">
                      <xs:annotation>
                        <xs:documentation xml:lang="en">The message specified in the assert</xs:documentation>
                      </xs:annotation>
                    </xs:attribute>
                    <xs:attribute name="type" type="xs:string" use="required">
                      <xs:annotation>
                        <xs:documentation xml:lang="en">The type of the assert.</xs:documentation>
                      </xs:annotation>
                    </xs:attribute>
                  </xs:extension>
                </xs:simpleContent>
              </xs:complexType>
            </xs:element>
            <xs:element name="skipped">
      <xs:annotation>
        <xs:documentation xml:lang="en">Indicates that the test was skipped. A skipped test is a test which was ignored using framework mechanisms. e.g., @Ignore annotation.</xs:documentation>
      </xs:annotation>
              <xs:complexType>
                <xs:simpleContent>
                  <xs:extension base="pre-string">
                    <xs:attribute name="type" type="xs:string" use="required">
                      <xs:annotation>
                        <xs:documentation xml:lang="en">Skip type.</xs:documentation>
                      </xs:annotation>
                    </xs:attribute>
                  </xs:extension>
                </xs:simpleContent>
              </xs:complexType>
            </xs:element>
          </xs:choice>
          <xs:attribute name="name" type="xs:token" use="required">
            <xs:annotation>
              <xs:documentation xml:lang="en">Name of the test method</xs:documentation>
            </xs:annotation>
          </xs:attribute>
          <xs:attribute name="classname" type="xs:token" use="required">
            <xs:annotation>
              <xs:documentation xml:lang="en">Full class name for the class the test method is in.</xs:documentation>
            </xs:annotation>
          </xs:attribute>
          <xs:attribute name="time" type="xs:decimal" use="required">
            <xs:annotation>
              <xs:documentation xml:lang="en">Time taken (in seconds) to execute the test</xs:documentation>
            </xs:annotation>
          </xs:attribute>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
    <xs:attribute name="name" use="required">
      <xs:annotation>
        <xs:documentation xml:lang="en">Full class name of the test for non-aggregated testsuite documents. Class name without the package for aggregated testsuites documents</xs:documentation>
      </xs:annotation>
      <xs:simpleType>
        <xs:restriction base="xs:token">
          <xs:minLength value="1"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute name="timestamp" type="ISO8601_DATETIME_PATTERN" use="required">
      <xs:annotation>
        <xs:documentation xml:lang="en">when the test was executed. Timezone may not be specified.</xs:documentation>
      </xs:annotation>
    </xs:attribute>
    <xs:attribute name="hostname" use="required">
      <xs:annotation>
        <xs:documentation xml:lang="en">Host on which the tests were executed. 'localhost' should be used if the hostname cannot be determined.</xs:documentation>
      </xs:annotation>
      <xs:simpleType>
        <xs:restriction base="xs:token">
          <xs:minLength value="1"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute name="tests" type="xs:int" use="required">
      <xs:annotation>
        <xs:documentation xml:lang="en">The total number of tests in the suite</xs:documentation>
      </xs:annotation>
    </xs:attribute>
    <xs:attribute name="failures" type="xs:int" use="required">
      <xs:annotation>
        <xs:documentation xml:lang="en">The total number of tests in the suite that failed. A failure is a test which the code has explicitly failed by using the mechanisms for that purpose. e.g., via an assertEquals</xs:documentation>
      </xs:annotation>
    </xs:attribute>
    <xs:attribute name="errors" type="xs:int" use="required">
      <xs:annotation>
        <xs:documentation xml:lang="en">The total number of tests in the suite that errored. An errored test is one that had an unanticipated problem. e.g., an unchecked throwable; or a problem with the implementation of the test.</xs:documentation>
      </xs:annotation>
    </xs:attribute>
    <xs:attribute name="skipped" type="xs:int">
      <xs:annotation>
        <xs:documentation xml:lang="en">The total number of tests in the suite that skipped. A skipped test is a test which was ignored using framework mechanisms. e.g., @Ignore annotation.</xs:documentation>
      </xs:annotation>
    </xs:attribute>
    <xs:attribute name="time" type="xs:decimal" use="required">
      <xs:annotation>
        <xs:documentation xml:lang="en">Time taken (in seconds) to execute the tests in the suite</xs:documentation>
      </xs:annotation>
    </xs:attribute>
  </xs:complexType>
  <xs:simpleType name="pre-string">
    <xs:restriction base="xs:string">
      <xs:whiteSpace value="preserve"/>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>
"""
