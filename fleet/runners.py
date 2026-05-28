import unittest
from django.test.runner import DiscoverRunner

class ColoredTestResult(unittest.TextTestResult):
    def getDescription(self, test):
        return test.shortDescription() or str(test)

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        if self.showAll:
            self.stream.writeln("\033[92mOK\033[0m")
        elif self.dots:
            self.stream.write('.')
            self.stream.flush()

    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        if self.showAll:
            self.stream.writeln("\033[91mFAIL\033[0m")
        elif self.dots:
            self.stream.write('F')
            self.stream.flush()

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        if self.showAll:
            self.stream.writeln("\033[91mERROR\033[0m")
        elif self.dots:
            self.stream.write('E')
            self.stream.flush()

class CustomRunner(DiscoverRunner):
    def get_resultclass(self):
        return ColoredTestResult