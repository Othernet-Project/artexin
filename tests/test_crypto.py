"""
test_crypto.py: Unit tests for ``lib.content_crypto`` module

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""


from unittest import mock

import pytest

from lib.content_crypto import *


def raise_os(*args, **kwargs):
    raise OSError()


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_keyring(open_p, GPG):
    """ Uses specified keyring """
    import_key(keypath='foo', keyring='bar')
    GPG.assert_called_once_with(gnupghome='bar')


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_import(open_p, GPG):
    """ Opens specified file and imports key """
    gpg = GPG.return_value
    fd = open_p.return_value.__enter__.return_value
    import_key(keypath='foo', keyring='bar')
    open_p.assert_called_once_with('foo', 'r')
    gpg.import_keys.assert_called_once_with(fd.read.return_value)


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_os_error(open_p, GPG):
    """ Should raise on failure to open given key file """
    open_p.side_effect = OSError()
    with pytest.raises(KeyImportError):
        import_key(keypath='foo', keyring='bar')


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_import_failure(open_p, GPG):
    """ Should raise on failure to import given key """
    gpg = GPG.return_value
    result = gpg.import_keys.return_value
    result.count = 0
    with pytest.raises(KeyImportError):
        import_key(keypath='foo', keyring='bar')


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_process_uses_keyring(open_p, GPG):
    """ Should use provided keyring """
    gpg = GPG.return_value
    data = gpg.decrypt.return_value
    process_content('/foo/bar.sig', 'bar', '/baz', 'zip', 'decrypt')
    GPG.assert_called_once_with(gnupghome='bar')


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_action_selection(open_p, GPG):
    gpg = GPG.return_value
    file_content = open_p.return_value.__enter__.return_value.read.return_value
    process_content('/foo/bar.sig', 'bar', '/baz', 'zip', 'decrypt')
    gpg.decrypt.assert_called_with(file_content, output='/baz/bar.zip')
    process_content('/foo/bar.zip', 'bar', '/baz', 'sig', 'encrypt')
    gpg.encrypt.assert_called_with(file_content, output='/baz/bar.sig')


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_fails_if_bad_file(open_p, GPG):
    """ Should raise if file cannot be opened """
    open_p.side_effect = OSError()
    with pytest.raises(CryptoError):
        process_content('/foo/bar.zip', 'bar', '/baz', 'sig', 'encrypt')


@mock.patch('lib.content_crypto.GPG')
def test_fails_if_wrong_action(GPG):
    with pytest.raises(CryptoError):
        process_content('/foo/bar.sig', 'bar', '/baz', 'zip', 'foo')


@mock.patch('lib.content_crypto.GPG')
@mock.patch('builtins.open')
def test_process_return_value(open_p, GPG):
    """ Should return new file path with provided extension """
    gpg = GPG.return_value
    path = process_content('/foo/bar.zip', 'bar', '/baz', 'sig', 'encrypt')
    assert path == '/baz/bar.sig'


@mock.patch('lib.content_crypto.process_content')
def test_decrypt_action(process_p):
    """ Should return new file path with provided extension """
    extract_content('/foo/bar.sig', 'bar', '/baz', 'zip')
    process_p.assert_called_with('/foo/bar.sig', 'bar', '/baz', 'zip',
                                 'decrypt')

