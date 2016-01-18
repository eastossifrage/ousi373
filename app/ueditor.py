# -*- coding:utf-8 -*-
__author__ = u'东方鹗'

import os
import re
import base64
import random
import urllib
import datetime
from flask import url_for, current_app
from flask.ext.login import current_user, request
from werkzeug.utils import secure_filename


class Uploader(object):
    """
    UEditor编辑器通用上传类
    """
    stateMap = {
        # 上传状态映射表，国际化用户需考虑此处数据的国际化
        "SUCCESS": u"SUCCESS",  # 上传成功标记，在UEditor中内不可改变，否则flash判断会出错
        "BEYOND_UPLOAD_MAX_FILE_SIZE": u"文件大小超出 upload_max_file_size 限制",
        "BEYOND_MAX_FILE_SIZE": u"文件大小超出 MAX_FILE_SIZE 限制",
        "INCOMPLETE_UPLOADED": u"文件未被完整上传",
        "NO_FILE_UPLOADED": u"没有文件被上传",
        "FILE_REQUIRED": u"上传文件为空",
        "ERROR_SIZE_EXCEED": u"文件大小超出网站限制",
        "ERROR_TYPE_NOT_ALLOWED": u"文件类型不允许",
        "ERROR_CREATE_DIR": u"目录创建失败",
        "ERROR_DIR_NOT_WRITEABLE": u"目录没有写权限",
        "ERROR_FILE_MOVE": u"文件保存时出错",
        "ERROR_FILE_NOT_FOUND": u"找不到上传文件",
        "ERROR_WRITE_CONTENT": u"写入文件内容错误",
        "ERROR_UNKNOWN": u"未知错误",
        "ERROR_DEAD_LINK": u"链接不可用",
        "ERROR_HTTP_LINK": u"链接不是http链接",
        "ERROR_HTTP_CONTENTTYPE": u"链接contentType不正确"
        }

    def __init__(self, fileField, config, _type=None):
        """
        :param fileField: FileStorage, Base64Encode Data or Image URL
        :param config: 配置信息
        :param static_folder: 文件保存的目录
        :param _type: 上传动作的类型，base64，remote，其它
        """
        self.fileField = fileField
        self.config = config
        self._type = _type
        if _type == 'base64':
            self.upBase64()
        elif _type == 'remote':
            self.saveRemote()
        else:
            self.upFile()
        """
        self.fileName = None  # 新文件名
        self.oriName = None  # 原始文件名
        self.fullName = None  # 完整文件名,即从当前配置目录开始的URL
        self.filePath = None  # 完整文件名,即从当前配置目录开始的URL
        self.fileSize = None  # 文件大小
        self.fileType = None  # 文件类型
        self.stateInfo = None  # 上传状态信息
        """
        
    def upFile(self):
        # 上传文件的主处理方法
        self.oriName = self.fileField.filename
        # 获取文件大小
        self.fileField.stream.seek(0, 2)
        self.fileSize = self.fileField.stream.tell()
        self.fileField.stream.seek(0, 0)
        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()        
        # 检查文件大小是否超出限制
        if not self.checkSize():
            self.stateInfo = self.getStateInfo('ERROR_SIZE_EXCEED')
            return
        # 检查是否不允许的文件格式
        if not self.checkType():
            self.stateInfo = self.getStateInfo('ERROR_TYPE_NOT_ALLOWED')
            return
        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(self.filePath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.stateInfo = self.getStateInfo('ERROR_CREATE_DIR')
                return
        elif not os.access(dirname, os.W_OK):
            self.stateInfo = self.getStateInfo('ERROR_DIR_NOT_WRITEABLE')
            return
        # 保存文件
        try:
            self.fileField.save(self.filePath)
            self.stateInfo = self.getStateInfo('SUCCESS')
        except:
            self.stateInfo = self.getStateInfo('ERROR_FILE_MOVE')
            return

    def upBase64(self):
        # 处理base64编码的图片上传
        img = base64.b64decode(self.fileField)
        self.oriName = self.config['oriName']
        self.fileSize = len(img)
        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()
        # 检查文件大小是否超出限制
        if not self.checkSize():
            self.stateInfo = self.getStateInfo('ERROR_SIZE_EXCEED')
            return
        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(self.filePath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.stateInfo = self.getStateInfo('ERROR_CREATE_DIR')
                return
        elif not os.access(dirname, os.W_OK):
            self.stateInfo = self.getStateInfo('ERROR_DIR_NOT_WRITEABLE')
            return
        try:
            with open(self.filePath, 'wb') as fp:
                fp.write(img)
            self.stateInfo = self.getStateInfo('SUCCESS')
        except:
            self.stateInfo = self.getStateInfo('ERROR_FILE_MOVE')
            return

    def saveRemote(self):
        _file = urllib.urlopen(self.fileField)
        self.oriName = self.config['oriName']
        self.fileSize = 0
        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()
        # 检查文件大小是否超出限制
        if not self.checkSize():
            self.stateInfo = self.getStateInfo('ERROR_SIZE_EXCEED')
            return
        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(self.filePath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                self.stateInfo = self.getStateInfo('ERROR_CREATE_DIR')
                return
        elif not os.access(dirname, os.W_OK):
            self.stateInfo = self.getStateInfo('ERROR_DIR_NOT_WRITEABLE')
            return
        try:
            with open(self.filePath, 'wb') as fp:
                fp.write(_file.read())
            self.stateInfo = self.getStateInfo('SUCCESS')
        except:
            self.stateInfo = self.getStateInfo('ERROR_FILE_MOVE')
            return

    def getStateInfo(self, error):
        # 上传错误检查
        return self.stateMap.get(error, 'ERROR_UNKNOWN')

    def getFileExt(self):
        # 获取文件扩展名
        return ('.%s' % self.oriName.split('.')[-1]).lower()

    def getFullName(self):
        # 重命名文件
        now = datetime.datetime.now()
        _time = now.strftime('%H%M%S')
        # 替换日期事件
        _format = self.config['pathFormat']
        _format = _format.replace('{yyyy}', str(now.year))
        _format = _format.replace('{mm}', str(now.month))
        _format = _format.replace('{dd}', str(now.day))
        _format = _format.replace('{user_id}', str(current_user.id).zfill(12))
        _format = _format.replace('{hh}', str(now.hour))
        _format = _format.replace('{ii}', str(now.minute))
        _format = _format.replace('{ss}', str(now.second))
        _format = _format.replace('{ss}', str(now.second))
        _format = _format.replace('{time}', _time)
        # 过滤文件名的非法自负,并替换文件名
        _format = _format.replace('{filename}',
                                  secure_filename(self.oriName))
        # 替换随机字符串
        rand_re = r'\{rand\:(\d*)\}'
        _pattern = re.compile(rand_re, flags=re.I)
        _match = _pattern.search(_format)
        if _match is not None:
            n = int(_match.groups()[0])
            _format = _pattern.sub(str(random.randrange(10**(n-1), 10**n)), _format)
        _ext = self.getFileExt()
        return '%s%s' % (_format, _ext)

    def getFilePath(self):
        # 获取文件完整路径
        rootPath = current_app._get_current_object().static_folder
        filePath = ''
        for path in self.fullName.split('/'):
            filePath = os.path.join(filePath, path)
        return os.path.join(rootPath, filePath)

    def checkType(self):
        # 文件类型检测
        return self.fileType.lower() in self.config['allowFiles']

    def checkSize(self):
        # 文件大小检测
        return self.fileSize <= self.config['maxSize']

    def getFileInfo(self):
        # 获取当前上传成功文件的各项信息
        filename = re.sub(r'^/', '', self.fullName)
        return {
            'state': self.stateInfo,
            'url': url_for('static', filename=filename, _external=True),
            'title': self.oriName,
            'original': self.oriName,
            'type': self.fileType,
            'size': self.fileSize,
        }


class List(object):
    """
    UEditor编辑器通用文件展示列表类
    """
    def __init__(self, config):
        """
        :param config: 配置信息
        """
        self.config = config
        self.listPath = self.getFilesListPath()
        self.files = self.getFiles()

    def getFilesListPath(self):
        # 获取文件完整路径
        rootPath = current_app._get_current_object().static_folder
        fileListPath = ''
        for path in self.config['pathFormat'].split('/'):
            fileListPath = os.path.join(fileListPath, path)
        return os.path.join(rootPath, fileListPath)

    def checkType(self, fileobj):
        # 文件类型检测
        return ('.%s' % fileobj.split('.')[-1]).lower() in self.config['allowFiles']

    def getFiles(self):
        """
        遍历获取目录下的指定类型的文件
        :return:
        """
        files = []
        if os.path.isdir(self.listPath):
            for currentDirName in os.listdir(self.listPath):
                if str(current_user.id).zfill(12) == currentDirName:  # 权限判定
                    current_dir = os.path.join(self.listPath, currentDirName)
                    for parentDir, dirNames, fileNames in os.walk(current_dir):
                        for fileName in fileNames:
                            filedict = {}
                            if self.checkType(fileName):
                                http_url = re.sub(r'^/', '', os.path.join(self.config['pathFormat'], currentDirName,
                                                                          parentDir.split('/')[-1], fileName))
                                filedict['url'] = url_for('static', filename=http_url, _external=True)
                                filedict['mtime'] = os.path.getmtime(os.path.join(current_dir, parentDir, fileName))
                            files.append(filedict)
        return files

    def getFilesInfo(self):
        size = int(request.args.get('size'))
        start = int(request.args.get('start'))
        self.size = size if size else int(self.config['listSize'])
        self.start = start if start else 0
        self.end = self.start + self.size
        if not self.files:
            return {
                'state': "no match file",
                'list': self.files,
                'start': self.start,
                'total': len(self.files)
            }
        else:
            fileList = []
            i = min(self.end, len(self.files))
            while i > 0 and i > self.start:
                i -= 1
                fileList.append(self.files[i])
            return {
                'state': "SUCCESS",
                'list': fileList,
                'start': self.start,
                'total': len(self.files)
            }
