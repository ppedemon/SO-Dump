
import os
import sys
import dateutil.parser
import xml.parsers.expat
import pymongo

from calendar import timegm
from HTMLParser import HTMLParser,HTMLParseError

from progress import Progress

class HTMLStripper(HTMLParser):
  def __init__(self):
    self.reset()
    self.buf = []
  def feed(self,s):
    try:
      HTMLParser.feed(self,s)
    except HTMLParseError:
      return s
  def handle_data(self,d):
    self.buf.append(d)
  def get_data(self):
    return self.unescape(''.join(self.buf))

class SoDumper():
  def __init__(self,batch_size):
    self.batch_size = batch_size
    self.questions = []
    self.answers = []
    self.parser = xml.parsers.expat.ParserCreate()
    self.parser.StartElementHandler = self._start_element
    self._init_mongo()
  
  def _init_mongo(self):
    client =  pymongo.MongoClient()
    self.db = client.so

  def _timestamp(self,isoDate):
    """Has to be a simpler way to do this... or not?"""
    d = dateutil.parser.parse(isoDate)
    return timegm(d.utctimetuple())*1000 + d.microsecond/1000

  def _start_element(self, name, attrs):
    if name == 'row':
      if attrs['PostTypeId'] == '1':
        self._dump_question(attrs)
      else:
        self._dump_answer(attrs)
    progress = self.parser.CurrentByteIndex
    if progress - self.old_progress >= self.interval:
      self.progress.progress(progress)
      self.old_progress = progress

  def _dump_question(self, attrs):
    s = HTMLStripper()
    s.feed(attrs['Body'])
    d = {
      'id': int(attrs['Id']),
      'creationDate': self._timestamp(attrs['CreationDate']),
      'lastActivityDate': self._timestamp(attrs['LastActivityDate']),
      'body': s.get_data().strip()
    }
    if 'AnswerCount' in attrs:
      d['answerCount'] = int(attrs['AnswerCount']),
    if 'AcceptedAnswerId' in attrs:
      d['acceptedAnswerId'] =  int(attrs['AcceptedAnswerId'])
    if 'CommentCount' in attrs:
      d['commentCount'] = int(attrs['CommentCount'])
    self.questions.append(d)
    if len(self.questions) >= self.batch_size: self.flush_questions()

  def _dump_answer(self, attrs):
    s = HTMLStripper()
    s.feed(attrs['Body'])
    d = {
      'id': int(attrs['Id']),
      'parentId': int(attrs['ParentId']),
      'creationDate': self._timestamp(attrs['CreationDate']),
      'lastActivityDate': self._timestamp(attrs['LastActivityDate']),
      'body': s.get_data().strip()
    }
    if 'CommentCount' in attrs:
      d['commentCount'] = int(attrs['CommentCount'])
    self.answers.append(d)
    if len(self.answers) >= self.batch_size: self.flush_answers()
  
  def flush_questions(self):
    self.db.questions.insert(self.questions)
    self.questions = []

  def flush_answers(self):
    self.db.answers.insert(self.answers)
    self.answers = []

  def parse(self, file, size):
    self.progress = Progress(size)
    self.interval = min(size/100.0,5000)
    self.old_progress = 0
    print 'Processing SO dump:'
    self.parser.ParseFile(file)
    if len(self.questions) > 0: self.flush_questions()
    if len(self.answers) > 0: self.flush_answers()
    self.progress.progress(self.parser.CurrentByteIndex)
    print '\n'

if __name__ == '__main__':
  p = SoDumper(1000)
  f = open(sys.argv[1])
  size = os.path.getsize(sys.argv[1])
  p.parse(f,size)

