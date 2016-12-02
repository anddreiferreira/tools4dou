#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import datetime
import urllib.request
import pymongo
import elasticsearch
import PyPDF2

class Collection:

  """ set of dou pages """

  def __init__(self, nosql_name, nosql_url, date_initial, date_final):
    """ public members """
    self.nosql_name = nosql_name
    self.nosql_url = nosql_url
    self.date_initial = date_initial
    self.date_final = date_final
    """ private members """
    self.__dou_url = 'http://pesquisa.in.gov.br/imprensa'
    self.__coding = 'ISO-8859-1'
    self.__mask_type = ('dot_folder', 'slash', 'dot_file')


  """ private methods"""

  def __reachability(self):
    response = urllib.request.urlopen(self.__dou_url)
    if response.getcode() in list(range(200, 300)):
      return True
    return False

  def __page_number(self, journal, date):
    pages = 0
    if self.__reachability():
      url = self.__dou_url + '/jsp/visualiza/index.jsp?jornal=' + journal + '&pagina=1&data=' + date + '&captchafield=firistAccess'
      response = urllib.request.urlopen(url)
      page = response.read()
      html = page.decode(self.__coding)
      match = re.search('totalArquivos=(\d{1,4})', html)
      if match:
        pages = int(match.group(1))
    return pages

  def __date_to_str(self, date):
    return '{:02}/{:02}/{:04}'.format(date.day, date.month, date.year)

  def __str_to_date(self, str_date):
    return datetime.date(int(str_date[6:10]), int(str_date[3:5]), int(str_date[0:2]))

  def __date_range(self, begin, end):
    begin_date = self.__str_to_date(begin)
    end_date = self.__str_to_date(end)
    period = []
    if begin_date <= end_date:
      for day in range((end_date - begin_date).days + 1):
        date = begin_date + datetime.timedelta(day)
        if date.weekday() <= 4:
          period.append(self.__date_time_mask(date, self.__mask_type[1]))
    return period

  def __date_time_mask(self, date_time, mask_type):
    if mask_type == 'dot_folder':
      return date_time.strftime('%Y.%m.%d.%Hh%Mm%Ss')
    elif mask_type == 'dot_file':
      return date_time.strftime('%Y.%m.%d')
    return date_time.strftime('%d/%m/%Y')

  def __mount_url(self, begin, end):
    days = self.__date_range(begin, end)
    urls = []
    for d in days:
        for j in range(1, 4):
          pages = self.__page_number(str(j), d)
          for p in range(1, (pages + 1)):
            urls.append((d, str(j), str(p), self.__dou_url + '/servlet/INPDFViewer?jornal=' + str(j) + '&pagina=' + str(p) + '&data=' + d + '&captchafield=firistAccess'))
    return urls



  """ public methods """

  def to_local(self, path):
    folder = self.__date_time_mask(path, self.__mask_type[0])
    os.mkdir(folder)
    urls = self.__mount_url(self.date_initial, self.date_final)
    for url in urls:
      filepath = folder + '/' + self.__date_time_mask(self.__str_to_date(url[0]), self.__mask_type[2]) + 'cad' + url[1] + 'pg' + url[2] + '.pdf'
      urllib.request.urlretrieve(url[3], filepath)
    return True