import unittest

from packaging.version import Version

from kmuhelper.utils import package_version, python_version


class BuildInfoTest(unittest.TestCase):
    def test_package_version(self):
        django_version = package_version("django")

        self.assertIsNotNone(django_version["latest"])
        self.assertIsNotNone(django_version["current"])
        self.assertIsNotNone(django_version["uptodate"])
        self.assertGreater(Version(django_version["latest"]), Version("5.2"))
        self.assertGreater(Version(django_version["current"]), Version("6.0"))

    def test_package_version_does_not_exist(self):
        pkg_version = package_version("somerandompackagethatdoesntexist09234i2")

        self.assertIsNone(pkg_version["current"])
        self.assertIsNone(pkg_version["uptodate"])

    def test_python_version(self):
        py = python_version()

        self.assertIsNotNone(py)
        self.assertGreater(Version(py), Version("3.12"))
