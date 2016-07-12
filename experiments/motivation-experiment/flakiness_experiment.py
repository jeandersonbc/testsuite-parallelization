#!/usr/bin/env python2
import os
import time
import datetime
import xml.etree.ElementTree

from os import path
from subprocess import check_call, call
from shutil import rmtree
from sys import argv

FAILED_LABEL = 'F'
IGNORED_LABEL = 'S'
PASSED_LABEL = 'P'

class SetupError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class TestResults:
    def __init__(self):
        self.failed = []
        self.ignored = []
        self.passed = []

    def addFailed(self, test):
        if test not in self.failed:
            self.failed.append(test)

    def addIgnored(self, test):
        if test not in self.ignored:
            self.ignored.append(test)

    def addPassed(self, test):
        if test not in self.passed:
            self.passed.append(test)

    def failures(self):
        return self.failed

    def ignores(self):
        return self.ignored

    def __str__(self):
        output = "TESTS - All: {total}, Ignored: {ignored}, Runs: {runs}, Failed: {failed}, Passed: {passed}"
        ignoredCnt = len(self.ignored)
        failedCnt= len(self.failed)
        passedCnt= len(self.passed)
        totalCnt = (ignoredCnt + failedCnt + passedCnt)
        runsCnt = totalCnt - ignoredCnt
        return output.format(total=totalCnt, ignored=ignoredCnt, \
                failed=failedCnt, passed=passedCnt, runs=runsCnt)

class MavenBuilder:
    def compile(self, logPath):
        with open(logPath, "a") as log:
            check_call(['mvn', '-DskipTests', '-Dmaven.javadoc.skip', 'clean', 'install'], stdout=log)

    def testIndividual(self, test, logPath):
        reportsDir = self._setupReportDir()

        # It's not appropriated to use check_call because the status code might be
        # different from zero if tests fail
        with open(logPath, "a") as log:
            call(['mvn', '-Dtest=' + test, 'test'], stdout=log, stderr=log)
        return self._colectResults(reportsDir)

    def test(self, logPath):
        reportsDir = self._setupReportDir()

        # It's not appropriated to use check_call because the status code might be
        # different from zero if tests fail
        with open(logPath, "a") as log:
            startedTime = time.time()
            call(['mvn', '-Dmaven.javadoc.skip', 'test'], stdout=log, stderr=log)
            elapsedTime = time.time() - startedTime
            print "Elapsed time: %.2f s" %(elapsedTime)

        return self._colectResults(reportsDir)

    def _setupReportDir(self):
        baseDir = path.abspath(os.curdir)
        reportsDir = path.join(baseDir, 'target', 'surefire-reports')
        if path.exists(reportsDir):
            rmtree(reportsDir)
        return reportsDir

    def _colectResults(self, reportsDir):
        xmlReports = []
        for root, dir, files in os.walk(reportsDir):
            xmlReports = [fi for fi in files if fi.startswith('TEST') and fi.endswith('.xml')]

        results = TestResults()
        for xmlReport in xmlReports:
            xmlReportPath = path.join(reportsDir, xmlReport)

            # Parsing XML report
            xmlParseNode = xml.etree.ElementTree.parse(xmlReportPath).getroot()
            for testCaseNode in xmlParseNode.findall('testcase'):
                testName = testCaseNode.get('classname') + "#" + testCaseNode.get('name')
                resultLabel = self._parseTestResult(testCaseNode)
                if resultLabel == IGNORED_LABEL:
                    results.addIgnored(testName)
                elif resultLabel == FAILED_LABEL:
                    results.addFailed(testName)
                else:
                    results.addPassed(testName)

        return results

    def _parseTestResult(self, testCaseNode):
        if len(list(testCaseNode)) == 0:
            return PASSED_LABEL
        if testCaseNode.find('skipped') is not None:
            return IGNORED_LABEL
        return FAILED_LABEL


class BuildSystem:
    def __init__(self, projectPath):
        # TODO: detect build system
        self.builder = MavenBuilder()

    def compile(self, logPath=os.devnull):
        self.builder.compile(logPath)

    def test(self, logPath=os.devnull):
        return self.builder.test(logPath)

    def testIndividual(self, test, logPath=os.devnull):
        return self.builder.testIndividual(test, logPath)


class FlakinessExperiment:
    def __init__(self, projectName, projectPath, testPath):
        projectAbsPath = path.abspath(projectPath)
        testAbsPath = path.join(projectAbsPath, testPath)
        if not path.exists(projectAbsPath):
            raise SetupError(projectAbsPath)
        if not path.exists(testAbsPath):
            raise SetupError(testAbsPath)

        self.projectName = projectName
        self.projectPath = projectAbsPath
        self.testPath= testAbsPath
        self.builder = BuildSystem(projectAbsPath)

        self.baseDir = path.abspath(os.curdir)

        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%m%d%H%M')
        version = path.basename(self.projectPath)
        self.logPrefix = "{0}-{1}-{2}".format(self.projectName, version, timestamp)

        print "Subject: \"{0}\"\nProject dir: \"{1}\"\nTest dir: \"{2}\"" \
                .format(self.projectName, self.projectPath, self.testPath)

    def run(self):
        print "Compiling project"
        os.chdir(self.projectPath)
        self.builder.compile()

        print "Running tests"
        os.chdir(self.testPath)
        testLogPath = path.join(self.baseDir, self.logPrefix + "-testLog.txt")
        results = self.builder.test(testLogPath)
        print results

        if not len(results.failures()):
            print "All tests passed"
        else:
            print "Checking Sequential Flakiness"
            self._checkFailures(results.failures())

    def _checkFailures(self, failures):
        testLogPath = path.join(self.baseDir, self.logPrefix + "-testLog-individual.txt")
        RERUNS = 10
        sequentialFlakiness = []
        for test in failures:
            for run in range(RERUNS):
                result = self.builder.testIndividual(test, testLogPath)
                if len(result.failures()):
                    sequentialFlakiness.extend(result.failures())
                    break

                if not len(result.ignores()) == 0:
                    warning_msg = "WARNING: failed test \"{0}\" was skipped! Ignored"
                    print warning_msg.format(test)
                    break

        output = "FLAKINESS - All: {all}, Pass: {passes}, Fail: {fail}"
        seqFlakinessCnt = len(sequentialFlakiness)
        allCnt = len(failures)
        print output.format(all=allCnt, fail=seqFlakinessCnt, passes=(allCnt - seqFlakinessCnt))

if __name__ == "__main__":
    projectName = argv[1]
    projectPath = argv[2]
    testPath = argv[3]

    experiment = FlakinessExperiment(projectName, projectPath, testPath)
    experiment.run()
