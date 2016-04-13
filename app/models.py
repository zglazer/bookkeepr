from . import db, flask_bcrypt
from sqlalchemy.ext.hybrid import hybrid_property

users_books = db.Table('users_books',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('book_id', db.Integer, db.ForeignKey('book.id')))

lists_books = db.Table('lists_books', 
        db.Column('list_id', db.Integer, db.ForeignKey('list.id')), 
        db.Column('book_id', db.Integer, db.ForeignKey('book.id')))

followers = db.Table('followers', 
        db.Column('follower_id', db.Integer, db.ForeignKey('user.id')), 
        db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(128), index = True, unique = True)
    nickname = db.Column(db.String(64), index = True)
    email = db.Column(db.String(128), index = True, unique = True)
    _password = db.Column(db.String(128))
    email_confirmed = db.Column(db.Boolean, default = False)
    profile_url = db.Column(db.String(256))
    books = db.relationship('Book', 
            secondary = users_books,
            backref = db.backref('users', lazy = 'dynamic'),
            lazy = 'dynamic')
    lists = db.relationship('List', backref = 'owner', lazy = 'dynamic')
    followed = db.relationship('User', 
        secondary = followers, 
        primaryjoin = (followers.c.follower_id == id), 
        secondaryjoin = (followers.c.followed_id == id), 
        backref = db.backref('followers', lazy = 'dynamic'), 
        lazy = 'dynamic')

    def add_book(self, book):
        """ Add specified book to User """
        if not self.has_book(book):
            self.books.append(book)
            return self

    def remove_book(self, book):
        """ Remove the specified book from User """
        if self.has_book(book):
            self.books.remove(book)
            return self

    def has_book(self, book):
        """ Return true if User has book in books """
        return self.books.filter(users_books.c.book_id == book.id).count() > 0

    def lists_with_book_count(self, book):
        """ Returns the number of lists in which this book appears """
        return self.lists.filter(List.books.contains(book)).count()

    def lists_with_book_all(self, book):
        """ Returns a list of list objects in which this book appears """
        return self.lists.filter(List.books.contains(book)).all()

    def follow(self, user):
        """ Follow a new user. """
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        """ Unfollow a user. """
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def following_count(self):
        pass

    def is_following(self, user):
        """ Return true if self is following user. """
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def is_correct_password(self, plaintext_candidate):
        if flask_bcrypt.check_password_hash(self._password, plaintext_candidate):
            return True
        return False

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = flask_bcrypt.generate_password_hash(plaintext)

    @staticmethod
    def make_unique_username(username):
        """ Returns a new unique username if username already exists
            in the system. """
        if User.query.filter_by(username = username).first() is None:
            return username
        version = 2
        new_username = None
        while True:
            new_username = username + str(version)
            if User.query.filter_by(username = new_username).first() is None:
                break
            version += 1
        return new_username

    def __repr__(self):
        return '<User %r>' % (self.username)

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(140))
    subtitle = db.Column(db.String(140))
    author = db.Column(db.String(140), index = True)
    description = db.Column(db.Text)
    isbn_13 = db.Column(db.String(13), unique = True, index = True)
    volume_id = db.Column(db.String(64), unique = True, index = True)
    image_url = db.Column(db.String(256))

    def __repr__(self):
        return '<Book %r>' % (self.title)

class List(db.Model):
    __tablename__ = 'list'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    books = db.relationship('Book', 
            secondary = lists_books,
            backref = db.backref('books', lazy = 'dynamic'), 
            lazy = 'dynamic')

    def add_book(self, book):
        """ Add book to list """
        if not self.owner.has_book(book):
            self.owner.add_book(book)
            self.books.append(book)
            return self
        if not self.has_book(book):
            self.books.append(book)
            return self

    def remove_book(self, book):
        """ Remove book from list """
        if self.has_book(book):
            self.books.remove(book)
            if self.owner.lists_with_book_count(book) <= 1:
                self.owner.remove_book(book)
            return self

    def remove_all_books(self):
        """ Removes all books from a list """
        for book in self.books:
            self.remove_book(book)
        return self

    def has_book(self, book):
        """ Returns True if book is in list """
        return self.books.filter(lists_books.c.book_id == book.id).count() > 0

    # List.query.filter(List.books.contains([book object]))

    def __repr__(self):
        return '<List %r>' % (self.title)

# class Review(db.Model):
#     __tablename__ = 'review'
#     id = db.Column(db.Integer, primary_key = True)
#     stars = db.Column()
#     book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     body = db.Column(db.Text)

#     def __repr__(self):
#         return '<Review: %d %d>' % (user_id, book_id)

