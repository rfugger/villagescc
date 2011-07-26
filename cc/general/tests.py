from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

class AdvancedTestSuiteRunner(DjangoTestSuiteRunner):
    """
    Test runner that only runs tests from certain packages.
    Useful for excluding django and 3rd-party apps from test runs.

    Adapted from http://djangosnippets.org/snippets/2211/.
    """
    def build_suite(self, *args, **kwargs):
        suite = super(AdvancedTestSuiteRunner, self).build_suite(*args, **kwargs)
        test_packages = getattr(settings, 'TEST_PACKAGES', None)
        if not test_packages or args[0]:  # Allow specifying any package on CL.
            return suite

        test_packages = list(test_packages) + ['unittest']  # Allow for doctests.
        tests = []
        for case in suite:
            pkg = case.__class__.__module__.split('.')[0]
            if pkg in test_packages:
                tests.append(case)
        suite._tests = tests
        return suite
                                                                                                                                                
