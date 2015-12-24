import os
import application
import unittest
import tempfile

class DiscrTestCase(unittest.TestCase):

    def setUp(self):
        application.app.config['TESTING'] = True
        self.app = application.app.test_client()


    def test_main_page(self):
        rv = self.app.get('/')
        assert "The main page" in rv.data

    def test_login_page(self):
        rv = self.app.get('/login')
        assert "This login page" in rv.data


    def returnUserPage(self, userID):
        return self.app.get('/user/%s' % userID)

    def test_user_page(self):
        rv = self.returnUserPage('12')
        assert "Display 12 user's dashboard"


    def returnDiscPage(self, manufacturerID, discID):
        return self.app.get('/discs/%s/%s' % (manufacturerID, discID))

    def test_disc_page(self):
        rv = self.returnDiscPage('4', '3')
        assert "unique disc with the disc ID of 3" in rv.data


    def returnDiscType(self, discType):
        return self.app.get('/discs/%s' % discType)

    def test_disc_type(self):
        rv = self.returnDiscType('putter')
        assert "discs in the putter category" in rv.data
        rv = self.returnDiscType('flying-pig')
        assert "flying-pig is not a type" in rv.data

if __name__ == '__main__':
    unittest.main()
