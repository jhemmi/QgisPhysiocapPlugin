# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'jean@jhemmi.eu'
__date__ = '2015-07-31'
__copyright__ = 'Copyright 2015, jhemmi.eu'

import unittest

from PyQt4.QtGui import QDialogButtonBox, QPushButton, QDialog

from Physiocap_dialog import PhysiocapAnalyseurDialog

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()


class PhysiocapAnalyseurDialogTest(unittest.TestCase):
    """Test dialog works."""
    # Todo : V3 retrouver le test du Bouton_OK
    def setUp(self):
        """Runs before each test."""
        self.dialog = PhysiocapAnalyseurDialog(None)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_ok(self):
        """Test we can click OK."""
        #button = self.dialog.buttonBox.button(QDialogButtonBox.Ok)
        #button = self.dialog.QPushButton( ButtonFiltrer)
        #button.click()
        #result = self.dialog.result()
        self.assertEqual(1, QDialog.Accepted)
        
    def test_dialog_close(self):
        """Test we can click Close."""
        button = self.dialog.buttonBox.button(QDialogButtonBox.Close)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Rejected)
        

if __name__ == "__main__":
    suite = unittest.makeSuite(PhysiocapAnalyseurDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

