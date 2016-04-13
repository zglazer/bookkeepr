from boto.s3.connection import S3Connection
from boto.s3.key import Key

class AWS(object):
    BASE_URL = 'https://s3.amazonaws.com/%s/%s'

    def __init__(self, app):
        self.conn = S3Connection(app.config.get('AWS_ACCESS_KEY_ID'), app.config.get('AWS_SECRET_KEY'))
        self.bucket = self.conn.get_bucket(app.config.get('BUCKET'))

    def store(self, name, file_path):
        """ Store a file on AWS S3. Requires a key and a path to the file. 
            Returns a temporary URL to the resource. """ 
        k = Key(self.bucket, name)
        k.set_contents_from_filename(file_path)
        return k.generate_url(10 * 60)

    def store_file(self, name, fp):
        """ Stores file on AWS S3 from file pointer fp. """
        k = Key(self.bucket, name)
        k.set_contents_from_file(fp)
        return self

    def delete(self, name):
        """ Delete key from S3. """
        k = Key(self.bucket, name)
        k.delete()
        return self

    def temp_url(self, name, expires = 10 * 60):
        """ Returns a temporary URL for the file at key. 
            Default expiration time is 10 minutes. """
        k = Key(self.bucket, name)
        return k.generate_url(expires_in = expires)

    def make_public(self, name):
        """ Makes a key public (i.e. access control to read-only). """
        k = Key(self.bucket, name)
        if k.exists():
            k.make_public()
            return self

    def get_file(self, name, file):
        """ Retrieves file contents from name and stores it in file. """
        k = Key(self.bucket, name)
        if k.exists():
            k.get_contents_to_file(file)
            return file

    def public_url(self, name):
        """ Returns the public URL for they given key name. """
        return self.BASE_URL % (self.bucket.name, name)


    def __repr__(self):
        return '<AWS %r>' % (self.bucket.name)