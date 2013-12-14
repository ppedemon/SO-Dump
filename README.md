SO-Dump
=======

Small script to save questions and answers from a StackOverflow dump to MongoDB. 
Requires python-dateutil and pymongo (and of course, MongoDB installed).

Small gotcha: expat represents byte offsets with a signed long. So in my 32 bits 
computer that spells trouble if file size is greater than 2Gb. Ouch!

