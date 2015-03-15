import copy
import datetime
import os
import urllib

from unittest import mock

from ..pack import json, create_zipball, collect, serialize_datetime


class TestCreateZipball(object):

    @classmethod
    def setup_class(cls):
        cls.meta = {'language': 'en',
                    'license': 'GFDL',
                    'url': 'http://en.wikipedia.org/wiki/Outernet',
                    'timestamp': datetime.datetime.utcnow()}
        cls.src_dir = '/tmp/some_random_folder'
        cls.base_out_dir = '/srv/zipballs'

        cls.expected_hash = 'an_md5_hash'
        cls.expected_size = 1024
        cls.expected_out_dir = os.path.join(cls.base_out_dir,
                                            cls.expected_hash)
        zip_filename = '{0}.zip'.format(cls.expected_hash)
        cls.expected_zipfile = os.path.join(cls.base_out_dir, zip_filename)

    @mock.patch('artexin.pack.hash_data')
    @mock.patch('artexin.pack.zipdir')
    @mock.patch('os.path.exists')
    @mock.patch('os.stat')
    @mock.patch('shutil.copytree')
    @mock.patch('shutil.rmtree')
    def test_create_zipball_no_crypto(self, shutil_rmtree, shutil_copytree,
                                      os_stat, os_path_exists, zipdir,
                                      hash_data):
        hash_data.return_value = self.expected_hash

        stat_result = mock.Mock(st_size=self.expected_size)
        os_stat.return_value = stat_result
        os_path_exists.return_value = True

        expected_meta = copy.copy(self.meta)
        expected_meta.update({'hash': self.expected_hash,
                              'size': self.expected_size,
                              'zipfile': self.expected_zipfile})

        expected_info = copy.copy(self.meta)
        str_timestamp = serialize_datetime(expected_info['timestamp'])
        expected_info['timestamp'] = str_timestamp
        str_expected_info = json.dumps(expected_info, indent=2)

        m_open = mock.mock_open()
        with mock.patch('builtins.open', m_open):
            meta = create_zipball(src_dir=self.src_dir,
                                  meta=self.meta,
                                  out_dir=self.base_out_dir)

        shutil_copytree.assert_called_once_with(self.src_dir,
                                                self.expected_out_dir)

        calls = [mock.call(self.expected_out_dir),
                 mock.call(self.expected_out_dir)]
        shutil_rmtree.assert_has_calls(calls)

        info_path = os.path.join(self.expected_out_dir, 'info.json')
        m_open.assert_called_once_with(info_path, 'w', encoding='utf-8')

        file_handle = m_open()
        file_handle.write.assert_called_once_with(str_expected_info)

        assert meta == expected_meta

    @mock.patch('artexin.pack.sign_content')
    @mock.patch('artexin.pack.hash_data')
    @mock.patch('artexin.pack.zipdir')
    @mock.patch('os.unlink')
    @mock.patch('os.path.exists')
    @mock.patch('os.stat')
    @mock.patch('shutil.copytree')
    @mock.patch('shutil.rmtree')
    def test_create_zipball_with_crypto(self, shutil_rmtree, shutil_copytree,
                                        os_stat, os_path_exists, os_unlink,
                                        zipdir, hash_data, sign_content):
        hash_data.return_value = self.expected_hash
        expected_signed_file = self.expected_zipfile.replace('.zip', '.sig')
        sign_content.return_value = expected_signed_file

        stat_result = mock.Mock(st_size=self.expected_size)
        os_stat.return_value = stat_result
        os_path_exists.return_value = True

        expected_meta = copy.copy(self.meta)
        expected_meta.update({'hash': self.expected_hash,
                              'size': self.expected_size,
                              'zipfile': expected_signed_file})

        expected_info = copy.copy(self.meta)
        str_timestamp = serialize_datetime(expected_info['timestamp'])
        expected_info['timestamp'] = str_timestamp
        str_expected_info = json.dumps(expected_info, indent=2)

        keyring = 'keyring'
        key = 'key'
        passphrase = 'passphrase'

        m_open = mock.mock_open()
        with mock.patch('builtins.open', m_open):
            meta = create_zipball(src_dir=self.src_dir,
                                  meta=self.meta,
                                  out_dir=self.base_out_dir,
                                  keyring=keyring,
                                  key=key,
                                  passphrase=passphrase)

        shutil_copytree.assert_called_once_with(self.src_dir,
                                                self.expected_out_dir)

        calls = [mock.call(self.expected_out_dir),
                 mock.call(self.expected_out_dir)]
        shutil_rmtree.assert_has_calls(calls)

        info_path = os.path.join(self.expected_out_dir, 'info.json')
        m_open.assert_called_once_with(info_path, 'w', encoding='utf-8')

        file_handle = m_open()
        file_handle.write.assert_called_once_with(str_expected_info)

        sign_content.assert_called_once_with(self.expected_zipfile,
                                             keyring,
                                             key,
                                             passphrase,
                                             output_dir=self.base_out_dir)

        os_unlink.assert_called_once_with(self.expected_zipfile)

        assert meta == expected_meta

    @mock.patch('artexin.pack.sign_content')
    @mock.patch('artexin.pack.hash_data')
    @mock.patch('artexin.pack.zipdir')
    @mock.patch('os.unlink')
    @mock.patch('os.path.exists')
    @mock.patch('os.stat')
    @mock.patch('shutil.copytree')
    @mock.patch('shutil.rmtree')
    def test_create_zipball_with_crypto_fail(self, shutil_rmtree,
                                             shutil_copytree, os_stat,
                                             os_path_exists, os_unlink, zipdir,
                                             hash_data, sign_content):
        hash_data.return_value = self.expected_hash
        expected_signed_file = self.expected_zipfile.replace('.zip', '.sig')
        sign_content.return_value = expected_signed_file

        stat_result = mock.Mock(st_size=self.expected_size)
        os_stat.return_value = stat_result
        os_path_exists.return_value = False

        expected_meta = copy.copy(self.meta)
        expected_err_msg = "Error signing '{0}'".format(self.expected_zipfile)
        expected_meta.update({'error': expected_err_msg})

        expected_info = copy.copy(self.meta)
        str_timestamp = serialize_datetime(expected_info['timestamp'])
        expected_info['timestamp'] = str_timestamp
        str_expected_info = json.dumps(expected_info, indent=2)

        keyring = 'keyring'
        key = 'key'
        passphrase = 'passphrase'

        m_open = mock.mock_open()
        with mock.patch('builtins.open', m_open):
            meta = create_zipball(src_dir=self.src_dir,
                                  meta=self.meta,
                                  out_dir=self.base_out_dir,
                                  keyring=keyring,
                                  key=key,
                                  passphrase=passphrase)

        shutil_copytree.assert_called_once_with(self.src_dir,
                                                self.expected_out_dir)

        shutil_rmtree.assert_called_once_with(self.expected_out_dir)

        info_path = os.path.join(self.expected_out_dir, 'info.json')
        m_open.assert_called_once_with(info_path, 'w', encoding='utf-8')

        file_handle = m_open()
        file_handle.write.assert_called_once_with(str_expected_info)

        sign_content.assert_called_once_with(self.expected_zipfile,
                                             keyring,
                                             key,
                                             passphrase,
                                             output_dir=self.base_out_dir)

        os_unlink.assert_called_once_with(self.expected_zipfile)

        assert meta == expected_meta


class TestCollect(object):

    @classmethod
    def setup_class(cls):
        cls.meta = {'language': 'en',
                    'license': 'GFDL'}
        cls.url = 'http://en.wikipedia.org/wiki/Outernet'
        cls.timestamp = datetime.datetime.utcnow()

    @mock.patch('artexin.pack.fetch_rendered')
    def test_collect_fail(self, fetch_rendered):
        exc = Exception("Bad luck")
        fetch_rendered.side_effect = exc

        meta = collect(self.url, meta=self.meta, javascript=True)

        expected_meta = copy.copy(self.meta)
        expected_meta.update({'url': self.url,
                              'domain': urllib.parse.urlparse(self.url).netloc,
                              'error': str(exc)})

        assert len(meta) == len(expected_meta) + 1

        for key, value in expected_meta.items():
            assert meta[key] == value

        assert isinstance(meta['timestamp'], datetime.datetime)

    @mock.patch('shutil.rmtree')
    @mock.patch('tempfile.mkdtemp')
    @mock.patch('artexin.pack.create_zipball')
    @mock.patch('artexin.pack.process_images')
    @mock.patch('artexin.pack.strip_links')
    @mock.patch('artexin.pack.extract')
    @mock.patch('artexin.pack.fetch_rendered')
    def test_collect(self, fetch_rendered, extract, strip_links,
                     process_images, create_zipball, tempfile_mkdtemp,
                     shutil_rmtree):
        page = 'html page'
        page_title = 'page title'
        page_source = 'page source'
        processed_source = 'processed source'
        images = range(5)
        temp_dir = '/tmp/some_folder'

        prep_func = mock.Mock()
        prep_func.side_effect = lambda x: x
        fetch_rendered.return_value = page
        extract.return_value = (page_title, page_source)
        strip_links.return_value = page_source
        process_images.return_value = (processed_source, images)
        tempfile_mkdtemp.return_value = temp_dir

        def mocked_create_zipball(meta, **kwargs):
            return meta
        create_zipball.side_effect = mocked_create_zipball

        m_open = mock.mock_open()
        with mock.patch('builtins.open', m_open):
            meta = collect(self.url,
                           meta=self.meta,
                           javascript=True,
                           do_extract=True,
                           prep=[prep_func])

        expected_meta = copy.copy(self.meta)
        expected_meta.update({'url': self.url,
                              'domain': urllib.parse.urlparse(self.url).netloc,
                              'title': page_title,
                              'images': len(images)})

        assert len(meta) == len(expected_meta) + 1

        for key, value in expected_meta.items():
            assert meta[key] == value

        assert isinstance(meta['timestamp'], datetime.datetime)

        extract.assert_called_once_with(page)
        prep_func.assert_called_once_with(page)
        strip_links.assert_called_once_with(page_source)
        tempfile_mkdtemp.assert_called_once_with()
        shutil_rmtree.assert_called_once_with(temp_dir)
        assert create_zipball.call_count == 1

        html_path = os.path.join(temp_dir, 'index.html')
        m_open.assert_called_once_with(html_path, 'w', encoding='utf-8')

        file_handle = m_open()
        file_handle.write.assert_called_once_with(processed_source)

    @mock.patch('shutil.rmtree')
    @mock.patch('tempfile.mkdtemp')
    @mock.patch('artexin.pack.create_zipball')
    @mock.patch('artexin.pack.process_images')
    @mock.patch('artexin.pack.strip_links')
    @mock.patch('artexin.pack.extract')
    @mock.patch('artexin.pack.fetch_rendered')
    def test_collect_override_title(self, fetch_rendered, extract, strip_links,
                                    process_images, create_zipball,
                                    tempfile_mkdtemp, shutil_rmtree):
        page = 'html page'
        page_title = 'page title'
        page_source = 'page source'
        processed_source = 'processed source'
        images = range(5)
        temp_dir = '/tmp/some_folder'
        overridden_title = 'overridden title'
        custom_meta = copy.copy(self.meta)
        custom_meta['title'] = overridden_title

        prep_func = mock.Mock()
        prep_func.side_effect = lambda x: x
        fetch_rendered.return_value = page
        extract.return_value = (page_title, page_source)
        strip_links.return_value = page_source
        process_images.return_value = (processed_source, images)
        tempfile_mkdtemp.return_value = temp_dir

        def mocked_create_zipball(meta, **kwargs):
            return meta
        create_zipball.side_effect = mocked_create_zipball

        m_open = mock.mock_open()
        with mock.patch('builtins.open', m_open):
            meta = collect(self.url,
                           meta=custom_meta,
                           javascript=True,
                           do_extract=True,
                           prep=[prep_func])

        expected_meta = copy.copy(self.meta)
        expected_meta.update({'url': self.url,
                              'domain': urllib.parse.urlparse(self.url).netloc,
                              'title': overridden_title,
                              'images': len(images)})

        assert len(meta) == len(expected_meta) + 1

        for key, value in expected_meta.items():
            assert meta[key] == value

        assert isinstance(meta['timestamp'], datetime.datetime)

        extract.assert_called_once_with(page)
        prep_func.assert_called_once_with(page)
        strip_links.assert_called_once_with(page_source)
        tempfile_mkdtemp.assert_called_once_with()
        shutil_rmtree.assert_called_once_with(temp_dir)
        assert create_zipball.call_count == 1

        html_path = os.path.join(temp_dir, 'index.html')
        m_open.assert_called_once_with(html_path, 'w', encoding='utf-8')

        file_handle = m_open()
        file_handle.write.assert_called_once_with(processed_source)
