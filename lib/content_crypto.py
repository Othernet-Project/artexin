"""
content_crypto.py: Deals with public keys and content signatures

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os.path

from gnupg import GPG


__version__ = 0.1
__author__ = 'Outernet Inc. <branko@outernet.is>'
__all__ = ('CryptoError', 'KeyImportError', 'import_key', 'process_content',
           'extract_content', 'sign_content',)


class CryptoError(BaseException):
    """ Base exception for all crypto-related errors """
    def __init__(self, msg, path=None):
        self.message = msg
        self.path = path
        super().__init__(msg)


class KeyImportError(CryptoError):
    """ Key import exception """
    pass


def import_key(keypath, keyring):
    """ Imports all keys from specified directory

    This function is idempotent, so importing the same key multiple times will
    always succeed.

    :param keypath:     path to armored key file
    :param keyring:     directory of the keyring
    """
    gpg = GPG(gnupghome=keyring)
    try:
        with open(keypath, 'r') as keyfile:
            result = gpg.import_keys(keyfile.read())
    except OSError:
        raise KeyImportError("Could not open '%s'" % keypath, keypath)
    if result.count == 0:
        raise KeyImportError("Could not import '%s'" % keypath, keypath)


def process_content(path, keyring, output_dir, output_ext, action):
    """ Use keyring to process a file by applying specified action

    This function automatically decrypts/encrypts into a new file that has the
    same filename as the original but with specified ``output_ext`` extension
    and in ``output_dir`` directory.

    :param path:        path of the content file
    :param keyring:     keyring path to use
    :param output_dir:  directory in which to write the output file
    :param output_ext:  extension of the output file
    :param action:      `'encrypt'` or `'decrypt'`
    """
    if action not in ['encrypt', 'decrypt']:
        raise CryptoError("Invalid action '%s'" % action, '')
    name = os.path.splitext(os.path.basename(path))[0]
    new_path = os.path.join(output_dir, name + '.' + output_ext)
    gpg = GPG(gnupghome=keyring)
    method = getattr(gpg, action)
    try:
        with open(path, 'rb') as content:
            method(content.read(), output=new_path)
    except OSError as err:
        raise CryptoError("Could not open '%s'" % path, path)
    return new_path


def extract_content(path, keyring, output_dir, output_ext='zip'):
    """ Use the keyring to decrypt a document

    :param path:        path of the signed file
    :param keyring:     keyring path to use
    :param output_dir:  directory in which to write the content file
    :param output_ext:  extension of the content file
    """
    return process_content(path, keyring, output_dir, output_ext, 'decrypt')


def sign_content(path, keyring, output_dir, output_ext='sig'):
    """ Sign the content at specified path using provided keyring

    :param path:        path of the content file
    :param keyring:     keyring path to use
    :param output_dir:  directory in which to write the signed file
    :param output_ext:  extension of the signed file
    """
    return process_content(path, keyring, output_dir, output_ext, 'encrypt')
