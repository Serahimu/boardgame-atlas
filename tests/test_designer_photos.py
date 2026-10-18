"""Reject missing or external designer images before publishing the static site."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_site

class DesignerPhotoTests(unittest.TestCase):
    def test_missing_photo_record_can_keep_explicit_fallback(self):
        validate_site.validate_designers({'designers':{'alex':{'image':'','status':'no-image'}}})

    def test_photo_must_be_published_local_asset(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(validate_site,'ROOT',Path(directory)):
            image=Path(directory)/'assets/designers/12.webp'
            image.parent.mkdir(parents=True)
            image.write_bytes(b'photo fixture')
            record={'image':'assets/designers/12.webp','bggId':'12','status':'ok'}
            validate_site.validate_designers({'designers':{'alex':record}})
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                validate_site.validate_designers({'designers':{'alex':dict(record,bggId='13')}})
            with self.assertRaisesRegex(ValueError,'Generic placeholder'):
                validate_site.validate_designers({'designers':{'alex':dict(record,imageid='1657690')}})
            image.unlink()
            with self.assertRaisesRegex(ValueError,'Missing designer photo'):
                validate_site.validate_designers({'designers':{'alex':record}})

    def test_rejects_external_and_escaped_image_paths(self):
        for image in ['https://example.org/photo.webp','//example.org/photo.webp','/assets/designers/12.webp','assets/designers/../12.webp','assets/designers/%2e%2e/12.webp','assets/covers/12.webp']:
            with self.subTest(image=image),self.assertRaisesRegex(ValueError,'Unsafe designer photo'):
                validate_site.validate_designers({'designers':{'alex':{'image':image}}})
