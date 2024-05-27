"""
Tests if there are changes detected that are not yet reflected in a migration
"""

import unittest

from django.core.management import call_command


class GeneralTest(unittest.TestCase):
    def test_detected_changes(self):
        try:
            call_command("makemigrations", "kmuhelper", "--check", "--dry-run")
        except SystemExit:
            self.fail("There are changes that are not yet reflected in a migration!")
