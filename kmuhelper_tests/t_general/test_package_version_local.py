from importlib import metadata
from unittest import mock

from django.test import SimpleTestCase
from packaging.version import Version

from kmuhelper.utils import _package_version_local


class PackageVersionLocalTest(SimpleTestCase):
    @mock.patch("kmuhelper.utils.metadata.version", return_value="1.2.3")
    def test_uses_importlib_metadata_version(self, _mock_version):
        self.assertEqual(_package_version_local("Django"), Version("1.2.3"))

    @mock.patch(
        "kmuhelper.utils.metadata.version",
        side_effect=metadata.PackageNotFoundError("not installed"),
    )
    @mock.patch("kmuhelper.utils.subprocess.run")
    def test_falls_back_to_pip_show(self, mock_run, _mock_version):
        mock_run.return_value = mock.Mock(stdout="Name: Django\nVersion: 5.2.0\n", returncode=0)

        self.assertEqual(_package_version_local("Django"), Version("5.2.0"))

    @mock.patch(
        "kmuhelper.utils.metadata.version",
        side_effect=metadata.PackageNotFoundError("not installed"),
    )
    @mock.patch("kmuhelper.utils.subprocess.run")
    def test_returns_none_if_no_version_found(self, mock_run, _mock_version):
        mock_run.return_value = mock.Mock(stdout="Name: Django\n", returncode=1)

        self.assertIsNone(_package_version_local("Django"))
