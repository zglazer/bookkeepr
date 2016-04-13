import os
import tempfile
from flask.ext.wtf import Form
from flask.ext.wtf.html5 import SearchField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import TextField, BooleanField, PasswordField, HiddenField
from wtforms.validators import Required, EqualTo, Email
from werkzeug.datastructures import MultiDict
from werkzeug import secure_filename


from .models import User
from . import app

class BookForm(Form):
    title = TextField('title', validators = [Required()])
    author = TextField('author', validators = [Required()])
    has_read = BooleanField('has_read', default = False)

    def reset(self):
	blank = MultiDict([ ('csrf', self.reset_csrf()  ) ])
	self.process(blank)

class SearchForm(Form):
    search = SearchField('Search', validators = [Required()])

class ListForm(Form):
    title = TextField('Title', validators = [Required()])

class EmailForm(Form):
    email = TextField('Email', validators = [Required(), Email()])

class PasswordForm(Form):
    password = PasswordField('Password', validators = [Required()])

class LoginForm(Form):
    email = TextField('Email', validators = [Required()])
    password = PasswordField('Password', validators = [Required()])

class RegistrationForm(Form):
    email = TextField('Email', validators = [Required(), Email()])
    password = PasswordField('Password', validators = [Required(), EqualTo('confirm',
                message = 'Passwords must match.')])
    confirm = PasswordField('Confirm password')

class ProfileImageForm(Form):
    image_url = FileField('image', validators = [FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self, time):
        """ Profile picture specific validation code. Check for 
            maximum file size. """
        rv = Form.validate(self)
        if not rv:
            return False
        filename = secure_filename(self.image_url.data.filename)
        filename = filename.lower()
        path = app.config['TEMP_FOLDER'] + str(time) + '_' + filename
        self.image_url.data.save(path)
        size = os.path.getsize(path)
        print size
        if size > app.config['MAX_IMAGE_SIZE']:
            return False
        return True

class ImageCropForm(Form):
    x1 = HiddenField('X1', validators = [Required()])
    y1 = HiddenField('Y1', validators = [Required()])
    x2 = HiddenField('X2', validators = [Required()])
    y2 = HiddenField('Y2', validators = [Required()])
    w = HiddenField('W', validators = [Required()])
    h = HiddenField('H', validators = [Required()])

class SettingsForm(Form):
    username = TextField('Username', validators = [Required()])
    nickname = TextField('Nickname', validators = [Required()])
    email = TextField('Email', validators = [Required(), Email()])

    def __init__(self, user, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_username = user.username
        self.original_email = user.email

    def validate(self):
        if not Form.validate(self):
            return False
        error = False
        if self.original_username != self.username.data:
            new_username = User.query.filter_by(username = self.username.data).first()
            if new_username is not None:
                error = True
                self.username.errors.append('This username is already in use.')
        if self.original_email != self.email.data:
            new_email = User.query.filter_by(email = self.email.data).first()
            if new_email is not None:
                error = True
                self.email.errors.append('This email is already in use.')
        if error:
            return False
        return True
