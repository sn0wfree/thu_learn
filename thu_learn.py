# -*- coding: utf-8 -*-
__author__ = 'kehao'
import requests
from bs4 import BeautifulSoup
import re
import os



# global vars
_session = requests.session()
_URL_BASE = 'https://learn.tsinghua.edu.cn'
_URL_LOGIN = _URL_BASE + '/MultiLanguage/lesson/teacher/loginteacher.jsp'

# 学期
_URL_CURRENT_SEMESTER = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/MyCourse.jsp?typepage=1'
_URL_PAST_SEMESTER = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/MyCourse.jsp?typepage=2'

# 课程不同板块前缀
# 课程公告
_PREF_NTF = 'http://learn.tsinghua.edu.cn/MultiLanguage/public/bbs/getnoteid_student.jsp?course_id='
# 课程信息
_PREF_INFO = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/course_info.jsp?course_id='
# 课程文件
_PREF_DOWN = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/download.jsp?course_id='
# 教学资源
_PREF_LIST = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/ware_list.jsp?course_id='
# 课程作业
_PREF_WORK = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/hom_wk_brw.jsp?course_id='


def login(user_id=None, user_pass=None):
    """
    login to get cookies in _session
    :param user_id: your Tsinghua id "keh13" for example
    :param user_pass: your password
    :return:None
    """
    if user_id is None or user_pass is None:
        user_id = input("TsinghuaId:")
        user_pass = input("Password:")
    data = dict(
        userid=user_id,
        userpass=user_pass,
    )
    _session.post(_URL_LOGIN, data)


def make_soup(url):
    """
    _session.GET the page, handle the encoding and return the BeautifulSoup
    :param url: Page url
    :return: BeautifulSoup
    """
    r = _session.get(url)
    r.encoding = 'bgk'
    soup = BeautifulSoup(r.content, "html.parser")
    return soup


class Semester:
    """
    Class Semester have all courses in it
    """
    def __init__(self, current=True):
        """
        set the current flag to get current/past Semester
        :param current: Boolean True/False for Current/Past semester
        :return: None
        """
        if _session is None:
            raise RuntimeError("Call login(userid, userpass) before anything else")
        if current:
            self.url = _URL_CURRENT_SEMESTER
        else:
            self.url = _URL_PAST_SEMESTER
        self.soup = make_soup(self.url)
        pass

    @property
    def courses(self):
        """
        return all the courses under the semester
        :return: Courses generator
        """

        list = []
        for i in self.soup.find_all('tr', class_='info_tr2'):
            list.append(i.find('a'))
        for i in self.soup.find_all('tr', class_='info_tr'):
            list.append(i.find('a'))
        for i in list:
            url = i['href']
            if url.startswith('/Mult'):
                url = _URL_BASE + url
            else:
                # !!important!! ignore the new WebLearning Courses At This moment
                continue
            name = i.contents[0]
            name = re.sub(r'[\n\r\t ]', '', name)
            id = url[-6:]
            yield Course(name=name, url=url, id=id)


class Course:
    """
    this is the Course class
    """

    def __init__(self, id, url=None, name=None):
        self._id = id
        self._url = url
        self._name = name
        self.r = None

    @property
    def url(self):
        """course url"""
        return self._url

    @property
    def name(self):
        """course name"""
        return self._name

    @property
    def id(self):
        """courses id"""
        return self._id

    @property
    def works(self):
        """
        get all the work in course
        :return: Work generator
        """
        url = _PREF_WORK + self._id
        soup = make_soup(url)
        list = []
        for i in soup.find_all('tr', class_='tr1'):
            list.append(i)
        for i in soup.find_all('tr', class_='tr2'):
            list.append(i)
        for i in list:
            # TODO
            tds = i.find_all('td')
            url = 'http://learn.tsinghua.edu.cn/MultiLanguage/lesson/student/' + i.find('a')['href']
            id = re.search(r'(\d+)', url).group(0)
            title = i.find('a').contents[0]
            start_time = tds[1].contents[0]
            end_time = tds[2].contents[0]
            yield Work(id=id, title=title, url=url, start_time=start_time, end_time=end_time)

    @property
    def messages(self):
        """
        get all messages in course
        :return: Message generator
        """
        pass
        # TODO

    @property
    def files(self):
        """
        get all files in course
        :return: File generator
        """
        pass
        # TODO


class Work:
    """
    the homework class
    """

    def __init__(self, url=None, id=None, title=None, start_time=None, end_time=None):
        self._url = url
        self._id = id
        self._title = title
        self._details = None
        self._file = None
        self._start_time = start_time
        self._end_time = end_time
        self.soup = make_soup(self.url)
        pass

    @property
    def url(self):
        """work url"""
        return self._url

    @property
    def id(self):
        """work id"""
        return self._id

    @property
    def title(self):
        """work title"""
        return self._title

    @property
    def start_time(self):
        """
        start date of the work
        :return:str time 'yyyy-mm-dd'
        """
        return self._start_time

    @property
    def end_time(self):
        """
        end date of the work
        :return: str time 'yyyy-mm-dd'
        """
        return self._end_time

    @property
    def details(self):
        """
        the description of the work
        :return:str details /None if not exists
        """
        if self._details is None:
            try:
                self._details = self.soup.find_all('td', class_='tr_2')[1].textarea.contents[0]
            except:
                pass
        return self._details

    @property
    def file(self):
        """
        the file attached to the work
        :return: Instance of File/None if not exists
        """
        if self._file is None:
            try:
                fname = self.soup.find_all('td', class_='tr_2')[2].a.contents[0]
                furl = 'http://learn.tsinghua.edu.cn' + self.soup.find_all('td', class_='tr_2')[2].a['href']
                self._file = File(url=furl, name=fname)
            except:
                pass
        return self._file


class File:
    def __init__(self, url, name=None, note=None):
        self._name = name
        self._url = url
        self._note = note

    def save(self, root='.'):
        if not os.path.exists(root):
            os.makedirs(root)
        r = requests.get(self.url)
        with open(root + '/' + self.name, 'wb') as f:
            f.write(r.content)

    @property
    def name(self):
        """file name
        Note! the file name is the name on the web but not the name in the download link
        """
        return self._name

    @property
    def url(self):
        """download url"""
        return self._url

    @property
    def note(self):
        """the description of the file
        this will exits under the CourseFile area but not in work area
        # considering take course.details as note
        """
        return self._note


def main():
    import test
    test.main()


if __name__ == '__main__':
    main()
