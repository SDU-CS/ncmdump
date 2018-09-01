# -*- coding: utf-8 -*-
"""
Created on Sun Jul 15 01:05:58 2018
@author: Nzix
"""

import binascii
import struct
import base64
import json
import os
from Crypto.Cipher import AES

def dump(file_path):

    core_key = binascii.a2b_hex("687A4852416D736F356B496E62617857")
    meta_key = binascii.a2b_hex("2331346C6A6B5F215C5D2630553C2728")
    unpad = lambda s : s[0:-(s[-1] if type(s[-1]) == int else ord(s[-1]))]

    f = open(file_path,'rb')

    # magic header
    header = f.read(8)
    assert binascii.b2a_hex(header) == b'4354454e4644414d'

    # key data
    f.seek(2, 1)
    key_length = f.read(4)
    key_length = struct.unpack('<I', bytes(key_length))[0]

    key_data = f.read(key_length)
    key_data_array = bytearray(key_data)
    i = 0
    while i < len(key_data_array):
        key_data_array[i] ^= 0x64
        i += 1
    key_data = bytes(key_data_array)

    cryptor = AES.new(core_key, AES.MODE_ECB)
    key_data = unpad(cryptor.decrypt(key_data))[17:]
    key_length = len(key_data)

    # key box
    key_data = bytearray(key_data)
    key_box = bytearray(range(256))
    c = 0
    last_byte = 0
    key_offset = 0

    for i in range(256):
        swap = key_box[i]
        c = (swap + last_byte + key_data[key_offset]) & 0xff
        key_offset += 1
        if key_offset >= key_length:
            key_offset = 0
        key_box[i] = key_box[c]
        key_box[c] = swap
        last_byte = c

    # meta data
    meta_length = f.read(4)
    meta_length = struct.unpack('<I', bytes(meta_length))[0]

    meta_data = f.read(meta_length)
    meta_data_array = bytearray(meta_data)
    i = 0
    while i < len(meta_data_array):
        meta_data_array[i] ^= 0x63
        i += 1
    meta_data = bytes(meta_data_array)
    meta_data = base64.b64decode(meta_data[22:])

    cryptor = AES.new(meta_key, AES.MODE_ECB)
    meta_data = unpad(cryptor.decrypt(meta_data)).decode('utf-8')[6:]
    meta_data = json.loads(meta_data)

    # crc32
    crc32 = f.read(4)
    crc32 = struct.unpack('<I', bytes(crc32))[0]

    # album cover
    f.seek(5, 1)
    image_size = f.read(4)
    image_size = struct.unpack('<I', bytes(image_size))[0]
    image_data = f.read(image_size)

    # media data
    file_name = meta_data['musicName'] + '.' + meta_data['format']
    m = open(os.path.join(os.path.split(file_path)[0],file_name),'wb')
    print(os.path.join(os.path.split(file_path)[0],file_name))

    chunk = bytearray()
    while True:
        chunk = bytearray(f.read(0x8000))
        chunk_length = len(chunk)
        if not chunk:
            break

        for i in range(chunk_length):
            j = (i + 1) & 0xff
            chunk[i] ^= key_box[(key_box[j] + key_box[(key_box[j] + j) & 0xff]) & 0xff]

        m.write(chunk)

    m.close()
    f.close()

if __name__ == '__main__':
    #import sys
    #if len(sys.argv) > 1:
    import os

    g = os.walk(r"f:\新建文件夹")

    for path, dir_list, file_list in g:
        for file_name in file_list:
          if '.ncm' in file_name:
            try:
                dump(os.path.join(path, file_name))
                print(os.path.join(path, file_name))
            except:
                pass

    #for file_path in :
    #    dump(file_path)