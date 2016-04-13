from flask import (render_template, url_for, flash, redirect, 
    request, g, session, abort, jsonify)
from flask.ext.login import login_user, logout_user, current_user, login_required
from . import app, lm, mail, db, aws
from werkzeug import secure_filename
import os
from .forms import (BookForm, LoginForm, RegistrationForm, EmailForm, 
    PasswordForm, SettingsForm, SearchForm, ProfileImageForm, ListForm, 
    ImageCropForm)
from .models import User, Book, List
from .utils.email import confirmation_email, password_reset_email, follow_user_email
from .utils.security import ts
from .utils.search import query, query_by_id, query_paginate
from .utils.image import ImageCropper
from sqlalchemy.sql.expression import or_
import time, shutil

@app.before_request
def before_request():
    """ Before each request get current user and global serach form """
    g.user = current_user
    g.search_form = SearchForm()

@app.route('/')
@app.route('/index')
def index():
    """ Home flag page for the app. Will redirect if logged in to dashboard. """
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/about')
def about():
    """ Load about page """
    return render_template('about.html', title = 'about')

@app.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def dashboard():
    """ Main page for logged in users. Displays user's books, 
        lists, and more. """
    form = ListForm()
    user = g.user
    books = user.books.all()
    lists = user.lists.all()
    if form.validate_on_submit():
        book = Book(title = form.title.data, 
                author = form.author.data,
                user_id = user.id)
        db.session.add(book)
        db.session.commit()
        user.add_book(book)
        db.session.add(user)
        db.session.commit()
        books = Book.query.filter_by(user_id = user.id).all()
        flash('Book added!')
        return render_template('dashboard.html', user = user,
                form = form,
                books = books)
    return render_template('dashboard.html', user = user,
        title = 'dashboard',
	    form = form,
        lists = lists,
        books = books)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    """ Log in user. """
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is not None and user.is_correct_password(form.password.data):
            if user.email_confirmed == False:
                flash('You must confirm your email in order to login. <a class="alert-link" href=' + url_for('confirm') + '>Resend confirm link</a>', 'danger')
                return redirect(url_for('login'))
            login_user(user)
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect username or password!', 'danger')
            return redirect(url_for('login'))
    return render_template('user/login.html',
            form = form)

@app.route('/delete/key', methods = ['POST'])
@login_required
def delete_key():
    """ Deletes a key from AWS S3. """
    key = request.form.get('key')
    aws.delete(key)
    return jsonify({
        'code': 'success'
        })

@app.route('/image_crop/<token>', methods = ['GET', 'POST'])
@login_required
def image_crop(token):
    """ Crop image. Called after profile image upload """
    aws_key = ts.loads(token, salt = 'tmp-img-key', max_age = 3600)
    img_src = aws.public_url(aws_key)
    form = ImageCropForm()
    if form.validate_on_submit():
        x1 = int(float(form.x1.data))
        y1 = int(float(form.y1.data))
        x2 = int(float(form.x2.data))
        y2 = int(float(form.y2.data))
        box = (x1, y1, x2, y2)
        new_key = aws_key.split(app.config['TEMP_AWS_DIR'])[1]
        new_key = app.config['PROFILE_DIR'] + new_key
        format = new_key.split('.')[-1:]
        format = 'JPEG' if format == 'jpg' else 'PNG'
        cropper = ImageCropper(aws_key)
        new_key = cropper.crop_and_store(new_key, box, format = format)
        cropper.destroy()
        aws.delete(aws_key)
        aws.make_public(new_key)
        user = g.user
        user.profile_url = aws.public_url(new_key)
        db.session.add(user)
        db.session.commit()
        flash('Profile image saved!')
        return redirect(url_for('dashboard'))
    return render_template('image_crop.html', form = form, img_src = img_src, key = aws_key)

@app.route('/photo_upload', methods = ['POST'])
@login_required
def photo_upload():
    """ Upload new user profile image. """
    photo = ProfileImageForm()
    t = time.time()
    user = g.user
    if photo.validate(time = t):
        filename = secure_filename(photo.image_url.data.filename)
        filename = filename.lower()
        extention = os.path.splitext(filename)[1]
        source = app.config['TEMP_FOLDER'] + str(t) + '_' + filename
        base = user.username + '_profile' + extention
        tmp_dir = app.config.get('TEMP_AWS_DIR', '')
        aws_key = tmp_dir + base
        aws.store(aws_key, source)
        aws.make_public(aws_key)
        token = ts.dumps(aws_key, salt = 'tmp-img-key')
        return redirect(url_for('image_crop', token = token))
    else:
        flash('Error submitting photo. Image must be in \
            JPG or PNG format and less than 2MB in size.')
        return redirect(url_for('settings'))

@app.route('/settings', methods = ['GET', 'POST'])
@login_required
def settings():
    """ Edit user settings """
    form = SettingsForm(g.user)
    photo = ProfileImageForm()
    user = g.user
    t = time.time()
    if form.validate_on_submit():
        user.username = form.username.data
        user.nickname = form.nickname.data
        db.session.add(user)
        db.session.commit()
        flash('Saved changes!')
        return redirect(url_for('index'))
    return render_template('user/settings.html', title = "settings", 
        user = user, form = form, photo = photo)

@lm.user_loader
def load_user(userid):
    """ Callback method required for Flask-Login """
    return User.query.get(int(userid))

@app.route('/logout')
@login_required
def logout():
    """ Logout current user """
    logout_user()
    flash('You have successfully logged out!')
    return redirect(url_for('index'))

@app.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
    """ User profile page """
    user = User.query.filter_by(username = username).first_or_404()
    books = user.books.all()
    return render_template('user/user.html',
        title = username,
        user = user,
        current_user = g.user,
        books = books)

@app.route('/follow', methods = ['POST'])
@login_required
def follow():
    """ Follow user AJAX call """
    follow_id = request.form.get('id')
    follow_user = User.query.get(follow_id)
    g.user.follow(follow_user)
    db.session.add(g.user)
    db.session.commit()
    follow_user_email(follow_user, g.user)
    return jsonify({
        'code': 'success'
        })

@app.route('/unfollow', methods = ['POST'])
@login_required
def unfollow():
    """ Unfollow user AJAX call """
    unfollow_id = request.form.get('id')
    unfollow_user = User.query.get(unfollow_id)
    g.user.unfollow(unfollow_user)
    db.session.add(g.user)
    db.session.commit()
    return jsonify({
        'code': 'success'
    })

@app.route('/register', methods = ['GET', 'POST'])
def register():
    """ Register page to register a new user """
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        if User.query.filter_by(email = email).count() > 0:
            flash('There is already an account registered to that email.')
            return redirect(url_for('register'))
        user = User(email = form.email.data,
                password = form.password.data,
                email_confirmed = False, 
                profile_url = app.config['NO_PROFILE_IMAGE'])
        db.session.add(user)
        db.session.commit()
        token = ts.dumps(email, salt = 'email-confirm-key')
        confirm_url = url_for('confirm_email', token = token, _external = True)
        confirmation_email(user, confirm_url)
        flash('A confirmation email has been sent!')
        return redirect(url_for('login'))
    return render_template('register.html',
            form = form)

@app.route('/confirm/<token>')
def confirm_email(token):
    """ Confirmation email. Completes registration process. """
    try:
        email = ts.loads(token, salt = 'email-confirm-key', max_age = 86400)
    except:
        abort(404)
    user = User.query.filter_by(email = email).first_or_404()
    if not user.email_confirmed:
        user.email_confirmed = True
        user.username = user.email.split('@')[0]
        user.nickname = user.username
        user.username = User.make_unique_username(user.username)
        user.follow(user)
        list = List(title = user.nickname + "'s List", owner = user)
        db.session.add(user)
        db.session.add(list)
        db.session.commit() 
    flash('Email address confirmed!')
    return redirect(url_for('login'))

@app.route('/confirm', methods = ['GET', 'POST'])
def confirm():
    """ Confirm user email. """
    form = EmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None:
            flash('The email you entered could not be found. Please try again.', 'warning')
            return redirect(url_for('confirm'))
        token = ts.dumps(user.email, salt = 'email-confirm-key')
        confirm_url = url_for('confirm_email', token = token, _external = True)
        confirmation_email(user, confirm_url)
        flash('A confirmation email has been sent!')
        return redirect(url_for('login'))
    return render_template('user/confirm.html', form = form)


@app.route('/reset', methods = ['GET', 'POST'])
def reset():
    """ Reset user password. """
    form = EmailForm() 
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None:
            flash('The email you entered could not be found. Please try again.')
            return redirect(url_for('reset'))
        if user.email_confirmed is False:
            flash('This account has not been confirmed. A password recovery ' \
                'email cannot be sent.')
            return redirect(url_for('confirm'))
        token = ts.dumps(user.email, salt = 'password-reset-key')
        reset_url = url_for('reset_with_token', token = token, _external = True)
        password_reset_email(user.email, reset_url)
        flash('A password recovery email has been sent.')
        return redirect(url_for('index'))
    return render_template('user/reset.html', form = form)

@app.route('/reset/<token>', methods = ['GET', 'POST'])
def reset_with_token(token):
    """ Password reset link. """
    try:
        email = ts.loads(token, salt = 'password-reset-key', max_age = 86400)
    except:
        abort(404)
    form = PasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = email).first_or_404()
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login')) 
    return render_template('reset_with_token.html', form = form, token = token)

@app.route('/book/id/<int:book_id>')
def book(book_id):
    """ Access book specific page """
    book = Book.query.get(book_id)
    if book is None:
        abort(404)
    users = book.users.all()
    return render_template('book_profile.html', book = book,
        title = book.title,
        users = users)

@app.route('/search', methods = ['GET', 'POST'])
@app.route('/search/<int:page>', methods = ['GET', 'POST'])
def search(page = 1):
    """ Search books and users """
    form = SearchForm()
    if g.search_form.validate_on_submit() or form.validate_on_submit():
        query_string = form.search.data
        return redirect(url_for('search', q = query_string))
    query_string = request.args.get('q')
    if query_string is None:
        return render_template('search.html', form = form)
    response = query_paginate(query_string, (page - 1) * app.config['MAX_RESULTS'])
    count = response['totalItems']
    if count < 1:
        return render_template('search_results.html', 
            count = count)
    items = response['items']
    books = {}
    for item in items:
        books[item['id']] = Book.query.filter_by(volume_id = item['id']).first()
    users = []
    users.extend(User.query.filter(or_(User.username.contains(query_string), 
        User.nickname.contains(query_string), 
        User.email == query_string)))
    users_set = set(users)
    return render_template('search_results.html',
        search_term = query_string,
        page = page,
        count = count,
        items = items,
        books = books, 
        users = users_set)

@app.route('/book/create/<volume_id>')
def create_book(volume_id):
    """ Adds book from Google Books API into database """
    _book_id = Book.query.filter_by(volume_id = volume_id).first()
    if _book_id is not None:
        return redirect(url_for('book', book_id = _book_id.id))
    response = query_by_id(volume_id)
    if response is None:
        abort(404)
    book_info = response['volumeInfo']
    properties = ['title', 'subtitle', 'authors', 'description','imageLinks', 'industryIdentifiers']
    new_book = {}
    for prop in properties:
        new_book[prop] = book_info.get(prop)
    if new_book['authors'] is not None:
        new_book['author'] = new_book['authors'][0]
    else:
        new_book['author'] = None
    if new_book['imageLinks'] is not None:
        new_book['image_url'] = new_book['imageLinks'].get('thumbnail')
    else:
        new_book['image_url'] = None
    if new_book['industryIdentifiers'] is not None:
        for identifier in book_info['industryIdentifiers']:
            if identifier['type'] == 'ISBN_13':
                new_book['isbn_13'] = identifier['identifier']
    else:
        new_book['isbn_13'] = None
    book = Book(title = new_book['title'],
                subtitle = new_book['subtitle'],
                author = new_book['author'],
                description = new_book['description'],
                volume_id = volume_id,
                image_url = new_book['image_url'],
                isbn_13 = new_book['isbn_13'])
    db.session.add(book)
    db.session.commit()
    return redirect(url_for('book', book_id = book.id))

@app.route('/book/add/<int:book_id>')
@login_required
def add_book(book_id):
    """ Adds a book to current user's list """
    if g.user is None or not g.user.is_authenticated():
        abort(500)
    book = Book.query.get(book_id)
    user = g.user
    if book is None or user is None:
        abort(404)
    user.add_book(book)
    db.session.add(user)
    db.session.add(book)
    db.session.commit()
    flash('Book successfully added to your list!')
    return redirect(url_for('dashboard'))

@app.route('/book/add', methods = ['POST'])
@login_required
def add_book_to_list():
    """ Adds a book to a user's list """
    book_id = request.form['book_id']
    list_id = request.form['list_id']
    list = List.query.get(list_id)
    book = Book.query.get(book_id)
    list.add_book(book)
    db.session.add(list)
    db.session.commit()
    return jsonify({
        'code': 'success'
        })

@app.route('/book/remove', methods = ['POST'])
@login_required
def remove_book_from_list():
    """ Remove a book from a user's list """
    book_id = request.form['book_id']
    list_id = request.form['list_id']
    list = List.query.get(list_id)
    book = Book.query.get(book_id)
    list.remove_book(book)
    db.session.add(list)
    db.session.commit()
    return jsonify({
        'code': 'success'
        })

@app.route('/lists/add', methods = ['POST'])
@login_required
def add_list():
    """ Create a new empty list for user """
    title = request.form['listname']
    if title == '':
        flash('List names cannot be empty.')
        return redirect(url_for('dashboard'))
    method = request.form.get('method')
    owner = g.user
    list = List(title = title, owner = owner)
    db.session.add(list)
    db.session.add(owner)
    db.session.commit()
    flash('List successfully added.')
    if method is 'AJAX':
        return jsonify({
            'id': list.id, 
            'title': list.title
        })
    return redirect(url_for('dashboard'))

@app.route('/lists/remove', methods = ['POST'])
@login_required
def remove_list():
    """ Remove a list including all books """
    id = request.form['id']
    list = List.query.get(id)
    owner = g.user
    list.remove_all_books()
    db.session.delete(list)
    db.session.commit()
    flash("List successfully deleted.")
    return jsonify({
        'code': "success"
        })

@app.route('/lists/edit', methods = ['POST'])
@login_required
def edit_list():
    """ Edit list title """
    id = request.form['id']
    title = request.form['title']
    list = List.query.get(id)
    list.title = title
    db.session.add(list)
    db.session.commit()
    flash('List successfully renamed!')
    return jsonify({
        'id': id,
        'title': title
        })

@app.route('/book/remove/<int:book_id>')
@login_required
def remove_book(book_id):
    """ Removes a book from current user's books """
    if g.user is None or not g.user.is_authenticated():
        abort(500)
    book = Book.query.get(book_id)
    user = g.user
    if book is None or user is None:
        abort(404)
    user.remove_book(book)
    db.session.add(user)
    db.session.add(book)
    db.session.commit()
    flash('Book successfully removed from your list!')
    return redirect(url_for('dashboard'))

@app.route('/list/<int:list_id>/remove/<int:book_id>')
@login_required
def remove_list_book(list_id, book_id):
    """ Removes a book from list """
    list = List.query.get(list_id)
    book = Book.query.get(book_id)
    if list is None or book is None:
        abort(404)
    list.remove_book(book)
    db.session.add(list)
    db.session.commit()
    flash('Book successfully removed from your list!')
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found_error(error):
    """ 404 page not found """
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """ 500 internal code error """
    db.session.rollback()
    return render_template('500.html'), 500
