from PIL import Image
import tempfile
from .. import aws


class ImageCropper(object):

    def __init__(self, key):
        self.tmp = tempfile.TemporaryFile()
        aws.get_file(key, self.tmp)
        self.tmp.seek(0, 0)
        self.img = Image.open(self.tmp)

    def crop(self, box):
        return self.img.crop(box)
        
    def crop_and_store(self, key, box, format = 'JPEG'):
        tmp_store = tempfile.TemporaryFile()
        cropped_image = self.crop(box)
        cropped_image.save(tmp_store, format = format)
        tmp_store.seek(0, 0)
        aws.store_file(key, tmp_store)
        tmp_store.close()
        return key

    def destroy(self):
        self.img.close()
        self.tmp.close()

    def __repr__(self):
        return '<ImageCropper: %s>' % (self.img)




