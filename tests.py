#! venv/bin/python

import os
import unittest

from config import basedir
from app import app, db
from app.models import Book, User, List


class AppTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class UserTest(AppTest):

    def test_password(self):
        """ test password hashing and testing """
        u = User(email='zach@example.com', password='test')
        self.assertTrue(u.password != 'test')
        self.assertTrue(u.is_correct_password('test'))
        old_password = u.password
        u.password = 'test2'
        db.session.add(u)
        db.session.commit()
        self.assertTrue(old_password != u.password)
        self.assertTrue(u.password != 'test2')

    def test_unique_username(self):
        u = User(email='email@example.com', password='test', 
            username='zachglazer', nickname='zachglazer')
        db.session.add(u)
        db.session.commit()
        username = User.make_unique_username(u.username)
        self.assertTrue(username != u.username)

    def test_login(self):
        u = User(email='email@example.com', password='test')
        db.session.add(u)
        db.session.commit()

class ListTest(AppTest):

    def test_list(self):
        """ test creating lists """
        u = User(email='email@example.com', password='test', username='example', nickname='example')
        db.session.add(u)
        db.session.commit()
        l = List(title = 'New List', owner = u)
        db.session.add(l)
        db.session.commit()
        self.assertTrue(u.lists.count() == 1)
        self.assertTrue(l.owner.nickname == 'example')
        self.assertTrue(l.owner == u)
        self.assertTrue(l.books.count() == 0)
        b = Book(title='Harry Potter', author='J.K. Rowling')
        db.session.add(b)
        db.session.commit()
        self.assertTrue(b.users.count() == 0)
        self.assertTrue(l.has_book(b) == False)

class FollowTest(AppTest):

    def test_follow_unfollow(self):
        """ test following new user """
        u = User(email ='test@example.com', username='test', nickname='test')
        u2 = User(email='zach@example.com', username='zach', nickname='zach')
        db.session.add(u)
        db.session.add(u2)
        db.session.commit()
        u.follow(u2)
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.is_following(u2))
        self.assertFalse(u2.is_following(u))
        u.follow(u)
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.is_following(u))
        u.unfollow(u2)
        db.session.add(u)
        db.session.commit()
        self.assertFalse(u.is_following(u2))

    def test_follow_unfollow_2(self):
        u = User(username='zach')
        u2 = User(username='jordan')
        u3 = User(username='corey')
        db.session.add(u)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()
        u.follow(u3)
        u.unfollow(u)
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.is_following(u3))
        self.assertFalse(u.is_following(u2))
        u3.follow(u)
        u3.follow(u2)
        u3.follow(u3)
        db.session.add(u3)
        db.session.commit()
        self.assertTrue(u3.is_following(u3))
        self.assertTrue(u3.is_following(u2))

if __name__ == '__main__':
    unittest.main()