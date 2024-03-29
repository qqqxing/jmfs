#!/usr/bin/env python

import socket
import struct
import time
import traceback
import urllib
import cgi
import cgitb
import sys

PROTO_BASE = 0

CLTOMA_CSERV_LIST = (PROTO_BASE+500)
MATOCL_CSERV_LIST = (PROTO_BASE+501)
CLTOCS_HDD_LIST_V1 = (PROTO_BASE+502)
CSTOCL_HDD_LIST_V1 = (PROTO_BASE+503)
CLTOMA_SESSION_LIST = (PROTO_BASE+508)
MATOCL_SESSION_LIST = (PROTO_BASE+509)
CLTOMA_INFO = (PROTO_BASE+510)
MATOCL_INFO = (PROTO_BASE+511)
CLTOMA_FSTEST_INFO = (PROTO_BASE+512)
MATOCL_FSTEST_INFO = (PROTO_BASE+513)
CLTOMA_CHUNKSTEST_INFO = (PROTO_BASE+514)
MATOCL_CHUNKSTEST_INFO = (PROTO_BASE+515)
CLTOMA_CHUNKS_MATRIX = (PROTO_BASE+516)
MATOCL_CHUNKS_MATRIX = (PROTO_BASE+517)
CLTOMA_QUOTA_INFO = (PROTO_BASE+518)
MATOCL_QUOTA_INFO = (PROTO_BASE+519)
CLTOMA_EXPORTS_INFO = (PROTO_BASE+520)
MATOCL_EXPORTS_INFO = (PROTO_BASE+521)
CLTOMA_MLOG_LIST = (PROTO_BASE+522)
MATOCL_MLOG_LIST = (PROTO_BASE+523)
CLTOCS_HDD_LIST_V2 = (PROTO_BASE+600)
CSTOCL_HDD_LIST_V2 = (PROTO_BASE+601)

cgitb.enable()

fields = cgi.FieldStorage()

try:
	if fields.has_key("masterhost"):
		masterhost = fields.getvalue("masterhost")
	else:
		masterhost = '127.0.0.1'
except Exception:
	masterhost = '127.0.0.1'
try:
	masterport = int(fields.getvalue("masterport"))
except Exception:
	masterport = 9421
try:
	if fields.has_key("mastername"):
		mastername = fields.getvalue("mastername")
	else:
		mastername = 'MooseFS'
except Exception:
	mastername = 'MooseFS'

thsep = ''
html_thsep = ''

def htmlentities(str):
	return str.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'",'&apos;').replace('"','&quot;')

def urlescape(str):
	return urllib.quote_plus(str)

def mysend(socket,msg):
	totalsent = 0
	while totalsent < len(msg):
		sent = socket.send(msg[totalsent:])
		if sent == 0:
			raise RuntimeError, "socket connection broken"
		totalsent = totalsent + sent

def myrecv(socket,leng):
	msg = ''
	while len(msg) < leng:
		chunk = socket.recv(leng-len(msg))
		if chunk == '':
			raise RuntimeError, "socket connection broken"
		msg = msg + chunk
	return msg

def decimal_number(number,sep=' '):
	parts = []
	while number>=1000:
		number,rest = divmod(number,1000)
		parts.append("%03u" % rest)
	parts.append(str(number))
	parts.reverse()
	return sep.join(parts)

def humanize_number(number,sep=''):
	number*=100
	scale=0
	while number>=99950:
		number = number//1024
		scale+=1
	if number<995 and scale>0:
		b = (number+5)//10
		nstr = "%u.%u" % divmod(b,10)
	else:
		b = (number+50)//100
		nstr = "%u" % b
	if scale>0:
		return "%s%s%si" % (nstr,sep,"-KMGTPEZY"[scale])
	else:
		return "%s%s" % (nstr,sep)

#def timeduration_to_shortstr(timeduration):
#	for l,s in ((86400,'day'),(3600,'hour'),(60,'minute'),(1,'second')):
#		if timeduration>=l:
#			n = float(timeduration)/float(l)
#			rn = round(n,0)
#			irn = int(rn)
#			return "%s%u&nbsp;%s%s" % (("about " if n!=rn else ""),irn,s,("" if irn==1 else "s"))
#	return "0&nbsp;seconds"

def timeduration_to_shortstr(timeduration):
	for l,s in ((86400,'d'),(3600,'h'),(60,'m'),(1,'s')):
		if timeduration>=l:
			n = float(timeduration)/float(l)
			rn = round(n,1)
			if n==round(n,0):
				return "%.0f%s" % (n,s)
			else:
				return "%s%.1f%s" % (("~" if n!=rn else ""),rn,s)
	return "0s"

def timeduration_to_fullstr(timeduration):
	if timeduration>=86400:
		days,dayseconds = divmod(timeduration,86400)
		daysstr = "%u day%s, " % (days,("s" if days!=1 else ""))
	else:
		dayseconds = timeduration
		daysstr = ""
	hours,hourseconds = divmod(dayseconds,3600)
	minutes,seconds = divmod(hourseconds,60)
	return "%u second%s (%s%u:%02u:%02u)" % (timeduration,("" if timeduration==1 else "s"),daysstr,hours,minutes,seconds)


# check version
masterversion = (0,0,0)
try:
	s = socket.socket()
	s.connect((masterhost,masterport))
	mysend(s,struct.pack(">LL",CLTOMA_INFO,0))
	header = myrecv(s,8)
	cmd,length = struct.unpack(">LL",header)
	data = myrecv(s,length)
	if cmd==MATOCL_INFO:
		if length==52:
			masterversion = (1,4,0)
		elif length==60:
			masterversion = (1,5,0)
		elif length==68 or length==76:
			masterversion = struct.unpack(">HBB",data[:4])
except Exception:
	print "Content-Type: text/html; charset=UTF-8"
	print
	print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
	print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
	print """<head>"""
	print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
	print """<title>MFS Info (%s)</title>""" % (htmlentities(mastername))
	print """<link rel="stylesheet" href="/mfs.css" type="text/css" />"""
	print """</head>"""
	print """<body>"""
	print """<h1 align="center">Can't connect to MFS master (IP:%s ; PORT:%u)</h1>""" % (htmlentities(masterhost),masterport)
	print """</body>"""
	print """</html>"""
	exit()

if masterversion==(0,0,0):
	print "Content-Type: text/html; charset=UTF-8"
	print
	print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
	print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
	print """<head>"""
	print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
	print """<title>MFS Info (%s)</title>""" % (htmlentities(mastername))
	print """<link rel="stylesheet" href="/mfs.css" type="text/css" />"""
	print """</head>"""
	print """<body>"""
	print """<h1 align="center">Can't detect MFS master version</h1>"""
	print """</body>"""
	print """</html>"""
	exit()


def createlink(update):
	global fields,urlescape
	c = []
	for k in fields:
		if k not in update:
			c.append("%s=%s" % (k,urlescape(fields.getvalue(k))))
	for k,v in update.iteritems():
		if v!="":
			c.append("%s=%s" % (k,urlescape(v)))
	return "mfs.cgi?%s" % ("&amp;".join(c))

def createorderlink(prefix,columnid):
	global fields,createlink
	ordername = "%sorder" % prefix
	revname = "%srev" % prefix
	try:
		orderval = int(fields.getvalue(ordername))
	except Exception:
		orderval = 0
	try:
		revval = int(fields.getvalue(revname))
	except Exception:
		revval = 0
	return createlink({revname:"1"}) if orderval==columnid and revval==0 else createlink({ordername:str(columnid),revname:"0"})

if fields.has_key("sections"):
	sectionstr = fields.getvalue("sections")
	sectionset = set(sectionstr.split("|"))
else:
	sectionset = set(("IN",))

if masterversion<(1,5,14):
	sectiondef={
		"IN":"Info",
		"CS":"Chunk Servers",
		"HD":"Hard Disks",
		"ML":"Mount List",
		"MC":"Master Charts",
		"CC":"Chunk Servers Charts"
	}
	sectionorder=["IN","CS","HD","ML","MC","CC"];
elif masterversion<(1,7,0):
	sectiondef={
		"IN":"Info",
		"CS":"Servers",
		"HD":"Disks",
		"EX":"Exports",
		"MS":"Mounts",
		"MO":"Operations",
		"MC":"Master Charts",
		"CC":"Server Charts"
	}
	sectionorder=["IN","CS","HD","EX","MS","MO","MC","CC"];
else:
	sectiondef={
		"IN":"Info",
		"CS":"Servers",
		"HD":"Disks",
		"EX":"Exports",
		"MS":"Mounts",
		"MO":"Operations",
		"QU":"Quotas",
		"MC":"Master Charts",
		"CC":"Server Charts"
	}
	sectionorder=["IN","CS","HD","EX","MS","MO","QU","MC","CC"];

print "Content-Type: text/html; charset=UTF-8"
print
# print """<!-- Put IE into quirks mode -->
print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
print """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">"""
print """<head>"""
print """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
print """<title>MFS Info (%s)</title>""" % (htmlentities(mastername))
print """<link rel="stylesheet" href="/mfs.css" type="text/css" />"""
print """</head>"""
print """<body>"""

#MENUBAR
print """<div id="header">"""
print """<table class="HDR" cellpadding="0" cellspacing="0" border="0">"""
print """<tr>"""
print """<td class="LOGO"><a href="http://www.moosefs.org"><img src="/logomini.png" alt="logo" style="border:0;width:123px;height:47px" /></a></td>"""
print """<td class="MENU"><table class="MENU" cellspacing="0">"""
print """<tr>"""
last="U"
for k in sectionorder:
	if k==sectionorder[-1]:
		last = "L%s" % last
	if k in sectionset:
		if len(sectionset)<=1:
			print """<td class="%sS">%s &#8722;</td>""" % (last,sectiondef[k])
		else:
			print """<td class="%sS"><a href="%s">%s</a> <a href="%s">&#8722;</a></td>""" % (last,createlink({"sections":k}),sectiondef[k],createlink({"sections":"|".join(sectionset-set([k]))}))
		last="S"
	else:
		print """<td class="%sU"><a href="%s">%s</a> <a href="%s">+</a></td>""" % (last,createlink({"sections":k}),sectiondef[k],createlink({"sections":"|".join(sectionset|set([k]))}))
		last="U"
print """</tr>"""
print """</table></td>"""
print """<td class="FILLER" style="white-space:nowrap;">"""
print """<a href="http://jigsaw.w3.org/css-validator/check/referer"><img style="border:0;width:88px;height:31px" src="http://jigsaw.w3.org/css-validator/images/vcss-blue" alt="Valid CSS!" /></a>"""
print """<a href="http://validator.w3.org/check?uri=referer"><img style="border:0;width:88px;height:31px" src="http://www.w3.org/Icons/valid-xhtml10-blue" alt="Valid XHTML 1.0 Strict" /></a>"""
print """</td>"""
print """</tr>"""
print """</table>"""
print """</div>"""

#print """<div id="footer">
#Moose File System by Jakub Kruszona-Zawadzki
#</div>
#"""

print """<div id="container">"""

if "IN" in sectionset:
	try:
		INmatrix = int(fields.getvalue("INmatrix"))
	except Exception:
		INmatrix = 0
	try:
		out = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_INFO and length==52:
			data = myrecv(s,length)
			total,avail,trspace,trfiles,respace,refiles,nodes,chunks,tdcopies = struct.unpack(">QQQLQLLLL",data)
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="9">Info</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>total space</th>""")
			out.append("""		<th>avail space</th>""")
			out.append("""		<th>trash space</th>""")
			out.append("""		<th>trash files</th>""")
			out.append("""		<th>reserved space</th>""")
			out.append("""		<th>reserved files</th>""")
			out.append("""		<th>all fs objects</th>""")
			out.append("""		<th>chunks</th>""")
			out.append("""		<th>copies to delete</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""		<td align="right">%u</td>""" % nodes)
			out.append("""		<td align="right">%u</td>""" % chunks)
			out.append("""		<td align="right">%u</td>""" % tdcopies)
			out.append("""	</tr>""")
			out.append("""</table>""")
		elif cmd==MATOCL_INFO and length==60:
			data = myrecv(s,length)
			total,avail,trspace,trfiles,respace,refiles,nodes,dirs,files,chunks,tdcopies = struct.unpack(">QQQLQLLLLLL",data)
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="11">Info</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>total space</th>""")
			out.append("""		<th>avail space</th>""")
			out.append("""		<th>trash space</th>""")
			out.append("""		<th>trash files</th>""")
			out.append("""		<th>reserved space</th>""")
			out.append("""		<th>reserved files</th>""")
			out.append("""		<th>all fs objects</th>""")
			out.append("""		<th>directories</th>""")
			out.append("""		<th>files</th>""")
			out.append("""		<th>chunks</th>""")
			out.append("""		<th>copies to delete</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""		<td align="right">%u</td>""" % nodes)
			out.append("""		<td align="right">%u</td>""" % dirs)
			out.append("""		<td align="right">%u</td>""" % files)
			out.append("""		<td align="right">%u</td>""" % chunks)
			out.append("""		<td align="right">%u</td>""" % tdcopies)
			out.append("""	</tr>""")
			out.append("""</table>""")
		elif cmd==MATOCL_INFO and length==68:
			data = myrecv(s,length)
			v1,v2,v3,total,avail,trspace,trfiles,respace,refiles,nodes,dirs,files,chunks,allcopies,tdcopies = struct.unpack(">HBBQQQLQLLLLLLL",data)
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="13">Info</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>version</th>""")
			out.append("""		<th>total space</th>""")
			out.append("""		<th>avail space</th>""")
			out.append("""		<th>trash space</th>""")
			out.append("""		<th>trash files</th>""")
			out.append("""		<th>reserved space</th>""")
			out.append("""		<th>reserved files</th>""")
			out.append("""		<th>all fs objects</th>""")
			out.append("""		<th>directories</th>""")
			out.append("""		<th>files</th>""")
			out.append("""		<th>chunks</th>""")
			if masterversion>=(1,6,10):
				out.append("""		<th><a style="cursor:default" title="chunks from 'regular' hdd space and 'marked for removal' hdd space">all chunk copies</a></th>""")
				out.append("""		<th><a style="cursor:default" title="only chunks from 'regular' hdd space">regular chunk copies</a></th>""")
			else:
				out.append("""		<th>chunk copies</th>""")
				out.append("""		<th>copies to delete</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<td align="center">%u.%u.%u</td>""" % (v1,v2,v3))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""		<td align="right">%u</td>""" % nodes)
			out.append("""		<td align="right">%u</td>""" % dirs)
			out.append("""		<td align="right">%u</td>""" % files)
			out.append("""		<td align="right">%u</td>""" % chunks)
			out.append("""		<td align="right">%u</td>""" % allcopies)
			out.append("""		<td align="right">%u</td>""" % tdcopies)
			out.append("""	</tr>""")
			out.append("""</table>""")
		elif cmd==MATOCL_INFO and length==76:
			data = myrecv(s,length)
			v1,v2,v3,memusage,total,avail,trspace,trfiles,respace,refiles,nodes,dirs,files,chunks,allcopies,tdcopies = struct.unpack(">HBBQQQQLQLLLLLLL",data)
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="14">Info</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>version</th>""")
			out.append("""		<th>RAM used</th>""")
			out.append("""		<th>total space</th>""")
			out.append("""		<th>avail space</th>""")
			out.append("""		<th>trash space</th>""")
			out.append("""		<th>trash files</th>""")
			out.append("""		<th>reserved space</th>""")
			out.append("""		<th>reserved files</th>""")
			out.append("""		<th>all fs objects</th>""")
			out.append("""		<th>directories</th>""")
			out.append("""		<th>files</th>""")
			out.append("""		<th>chunks</th>""")
			out.append("""		<th><a style="cursor:default" title="chunks from 'regular' hdd space and 'marked for removal' hdd space">all chunk copies</a></th>""")
			out.append("""		<th><a style="cursor:default" title="only chunks from 'regular' hdd space">regular chunk copies</a></th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<td align="center">%u.%u.%u</td>""" % (v1,v2,v3))
			if memusage>0:
				out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(memusage),humanize_number(memusage,"&nbsp;")))
			else:
				out.append("""		<td align="center"><a style="cursor:default" title="obtaining memory usage is not supported by your OS">not available</td>""")
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(total),humanize_number(total,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(avail),humanize_number(avail,"&nbsp;")))
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(trspace),humanize_number(trspace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % trfiles)
			out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(respace),humanize_number(respace,"&nbsp;")))
			out.append("""		<td align="right">%u</td>""" % refiles)
			out.append("""		<td align="right">%u</td>""" % nodes)
			out.append("""		<td align="right">%u</td>""" % dirs)
			out.append("""		<td align="right">%u</td>""" % files)
			out.append("""		<td align="right">%u</td>""" % chunks)
			out.append("""		<td align="right">%u</td>""" % allcopies)
			out.append("""		<td align="right">%u</td>""" % tdcopies)
			out.append("""	</tr>""")
			out.append("""</table>""")
		else:
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><td align="left">unrecognized answer from MFSmaster</td></tr>""")
			out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

	if masterversion>=(1,5,13):
		try:
			out = []
			s = socket.socket()
			s.connect((masterhost,masterport))
			if masterversion>=(1,6,10):
				mysend(s,struct.pack(">LLB",CLTOMA_CHUNKS_MATRIX,1,INmatrix))
			else:
				mysend(s,struct.pack(">LL",CLTOMA_CHUNKS_MATRIX,0))
			header = myrecv(s,8)
			cmd,length = struct.unpack(">LL",header)
			if cmd==MATOCL_CHUNKS_MATRIX and length==484:
				matrix = []
				for i in xrange(11):
					data = myrecv(s,44)
					matrix.append(list(struct.unpack(">LLLLLLLLLLL",data)))
				out.append("""<table class="FR" cellspacing="0">""")
				if masterversion>=(1,6,10):
					if INmatrix==0:
						out.append("""	<tr><th colspan="13">All chunks state matrix (counts 'regular' hdd space and 'marked for removal' hdd space : <a href="%s" class="VISIBLELINK">switch to 'regular'</a>)</th></tr>""" % (createlink({"INmatrix":"1"})))
					else:
						out.append("""	<tr><th colspan="13">Regular chunks state matrix (counts only 'regular' hdd space : <a href="%s" class="VISIBLELINK">switch to 'all'</a>)</th></tr>""" % (createlink({"INmatrix":"0"})))
				else:
					out.append("""	<tr><th colspan="13">Chunk state matrix</th></tr>""")
				out.append("""	<tr>""")
				out.append("""		<th rowspan="2" class="PERC4">goal</th>""")
				out.append("""		<th colspan="12" class="PERC96">valid copies</th>""")
				out.append("""	</tr>""")
				out.append("""	<tr>""")
				out.append("""		<th class="PERC8">0</th>""")
				out.append("""		<th class="PERC8">1</th>""")
				out.append("""		<th class="PERC8">2</th>""")
				out.append("""		<th class="PERC8">3</th>""")
				out.append("""		<th class="PERC8">4</th>""")
				out.append("""		<th class="PERC8">5</th>""")
				out.append("""		<th class="PERC8">6</th>""")
				out.append("""		<th class="PERC8">7</th>""")
				out.append("""		<th class="PERC8">8</th>""")
				out.append("""		<th class="PERC8">9</th>""")
				out.append("""		<th class="PERC8">10+</th>""")
				out.append("""		<th class="PERC8">all</th>""")
				out.append("""	</tr>""")
				classsum = 7*[0]
				sumlist = 11*[0]
				for goal in xrange(11):
					out.append("""	<tr>""")
					if goal==10:
						out.append("""		<td align="center">10+</td>""")
					else:
						out.append("""		<td align="center">%u</td>""" % goal)
					for vc in xrange(11):
						if goal==0:
							if vc==0:
								cl = "DELETEREADY"
								clidx = 6
							else:
								cl = "DELETEPENDING"
								clidx = 5
						elif vc==0:
							cl = "MISSING"
							clidx = 0
						elif vc>goal:
							cl = "OVERGOAL"
							clidx = 4
						elif vc<goal:
							if vc==1:
								cl = "ENDANGERED"
								clidx = 1
							else:
								cl = "UNDERGOAL"
								clidx = 2
						else:
							cl = "NORMAL"
							clidx = 3
						if matrix[goal][vc]>0:
							out.append("""		<td align="right"><span class="%s">%u</span></td>""" % (cl,matrix[goal][vc]))
							classsum[clidx]+=matrix[goal][vc]
						else:
							out.append("""		<td align="center">-</td>""")
					if goal==0:
						out.append("""		<td align="right"><span class="IGNORE">%u</span></td>""" % sum(matrix[goal]))
					else:
						out.append("""		<td align="right">%u</td>""" % sum(matrix[goal]))
					out.append("""	</tr>""")
					if goal>0:
						sumlist = [ a + b for (a,b) in zip(sumlist,matrix[goal])]
				out.append("""	<tr>""")
				out.append("""		<td align="center">all 1+</td>""")
				for vc in xrange(11):
					out.append("""		<td align="right">%u</td>""" % sumlist[vc])
				out.append("""		<td align="right">%u</td>""" % sum(sumlist))
				out.append("""	</tr>""")
				out.append("""	<tr><td colspan="13">""" + " / ".join(["""<span class="%sBOX"></span>&nbsp;-&nbsp;%s (<span class="%s">%u</span>)""" % (cl,desc,cl,classsum[clidx]) for clidx,cl,desc in [(0,"MISSING","missing"),(1,"ENDANGERED","endangered"),(2,"UNDERGOAL","undergoal"),(3,"NORMAL","stable"),(4,"OVERGOAL","overgoal"),(5,"DELETEPENDING","pending&nbsp;deletion"),(6,"DELETEREADY","ready&nbsp;to&nbsp;be&nbsp;removed")]]) + """</td></tr>""")
				out.append("""</table>""")
			s.close()
			print "\n".join(out)
		except Exception:
			print """<table class="FR" cellspacing="0">"""
			print """<tr><td align="left"><pre>"""
			traceback.print_exc(file=sys.stdout)
			print """</pre></td></tr>"""
			print """</table>"""

		print """<br/>"""

	try:
		out = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_CHUNKSTEST_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_CHUNKSTEST_INFO and length==52:
			data = myrecv(s,length)
			loopstart,loopend,del_invalid,ndel_invalid,del_unused,ndel_unused,del_dclean,ndel_dclean,del_ogoal,ndel_ogoal,rep_ugoal,nrep_ugoal,rebalnce = struct.unpack(">LLLLLLLLLLLLL",data[:52])
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="8">Chunk operations info</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th colspan="2">loop time</th>""")
			out.append("""		<th colspan="4">deletions</th>""")
			out.append("""		<th colspan="2">replications</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>start</th>""")
			out.append("""		<th>end</th>""")
			out.append("""		<th>invalid</th>""")
			out.append("""		<th>unused</th>""")
			out.append("""		<th>disk clean</th>""")
			out.append("""		<th>over goal</th>""")
			out.append("""		<th>under goal</th>""")
			out.append("""		<th>rebalance</th>""")
			out.append("""	</tr>""")
			if loopstart>0:
				out.append("""	<tr>""")
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopstart)),))
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopend)),))
				out.append("""		<td align="right">%u/%u</td>""" % (del_invalid,del_invalid+ndel_invalid))
				out.append("""		<td align="right">%u/%u</td>""" % (del_unused,del_unused+ndel_unused))
				out.append("""		<td align="right">%u/%u</td>""" % (del_dclean,del_dclean+ndel_dclean))
				out.append("""		<td align="right">%u/%u</td>""" % (del_ogoal,del_ogoal+ndel_ogoal))
				out.append("""		<td align="right">%u/%u</td>""" % (rep_ugoal,rep_ugoal+nrep_ugoal))
				out.append("""		<td align="right">%u</td>""" % rebalnce)
				out.append("""	</tr>""")
			else:
				out.append("""	<tr>""")
				out.append("""		<td colspan="8" align="center">no data</td>""")
				out.append("""	</tr>""")
			out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

	try:
		out = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_FSTEST_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_FSTEST_INFO and length>=36:
			data = myrecv(s,length)
			loopstart,loopend,files,ugfiles,mfiles,chunks,ugchunks,mchunks,msgbuffleng = struct.unpack(">LLLLLLLLL",data[:36])
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="8">Filesystem check info</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>check loop start time</th>""")
			out.append("""		<th>check loop end time</th>""")
			out.append("""		<th>files</th>""")
			out.append("""		<th>under-goal files</th>""")
			out.append("""		<th>missing files</th>""")
			out.append("""		<th>chunks</th>""")
			out.append("""		<th>under-goal chunks</th>""")
			out.append("""		<th>missing chunks</th>""")
			out.append("""	</tr>""")
			if loopstart>0:
				out.append("""	<tr>""")
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopstart)),))
				out.append("""		<td align="center">%s</td>""" % (time.asctime(time.localtime(loopend)),))
				out.append("""		<td align="right">%u</td>""" % files)
				out.append("""		<td align="right">%u</td>""" % ugfiles)
				out.append("""		<td align="right">%u</td>""" % mfiles)
				out.append("""		<td align="right">%u</td>""" % chunks)
				out.append("""		<td align="right">%u</td>""" % ugchunks)
				out.append("""		<td align="right">%u</td>""" % mchunks)
				out.append("""	</tr>""")
				if msgbuffleng>0:
					if msgbuffleng==100000:
						out.append("""	<tr><th colspan="8">Important messages (first 100k):</th></tr>""")
					else:
						out.append("""	<tr><th colspan="8">Important messages:</th></tr>""")
					out.append("""	<tr>""")
					out.append("""		<td colspan="8" align="left"><pre>%s</pre></td>""" % (data[36:].replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")))
					out.append("""	</tr>""")
			else:
				out.append("""	<tr>""")
				out.append("""		<td colspan="8" align="center">no data</td>""")
				out.append("""	</tr>""")
			out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "CS" in sectionset:
	out = []

	try:
		CSorder = int(fields.getvalue("CSorder"))
	except Exception:
		CSorder = 0
	try:
		CSrev = int(fields.getvalue("CSrev"))
	except Exception:
		CSrev = 0

	try:
		out.append("""<table class="FR" cellspacing="0">""")
		out.append("""	<tr><th colspan="14">Chunk Servers</th></tr>""")
		out.append("""	<tr>""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">host</a></th>""" % (createorderlink("CS",1)))
		out.append("""		<th rowspan="2"><a href="%s">ip</a></th>""" % (createorderlink("CS",2)))
		out.append("""		<th rowspan="2"><a href="%s">port</a></th>""" % (createorderlink("CS",3)))
		out.append("""		<th rowspan="2"><a href="%s">version</a></th>""" % (createorderlink("CS",4)))
		out.append("""		<th colspan="4">'regular' hdd space</th>""")
		if masterversion>=(1,6,10):
			out.append("""		<th colspan="4">'marked for removal' hdd space</th>""")
		else:
			out.append("""		<th colspan="4">'to be empty' hdd space</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="%s">chunks</a></th>""" % (createorderlink("CS",10)))
		out.append("""		<th><a href="%s">used</a></th>""" % (createorderlink("CS",11)))
		out.append("""		<th><a href="%s">total</a></th>""" % (createorderlink("CS",12)))
		out.append("""		<th class="PROGBAR"><a href="%s">%% used</a></th>""" % (createorderlink("CS",13)))
		out.append("""		<th><a href="%s">chunks</a></th>""" % (createorderlink("CS",20)))
		out.append("""		<th><a href="%s">used</a></th>""" % (createorderlink("CS",21)))
		out.append("""		<th><a href="%s">total</a></th>""" % (createorderlink("CS",22)))
		out.append("""		<th class="PROGBAR"><a href="%s">%% used</a></th>""" % (createorderlink("CS",23)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_CSERV_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_CSERV_LIST and masterversion>=(1,5,13) and (length%54)==0:
			data = myrecv(s,length)
			n = length/54
			servers = []
			for i in xrange(n):
				d = data[i*54:(i+1)*54]
				v1,v2,v3,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">HBBBBBBHQQLQQLL",d)
				try:
					host = (socket.gethostbyaddr("%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)))[0]
				except Exception:
					host = "(unresolved)"
				if CSorder==1:
					sf = host
				elif CSorder==2 or CSorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif CSorder==3:
					sf = port
				elif CSorder==4:
					sf = (v1,v2,v3)
				elif CSorder==10:
					sf = chunks
				elif CSorder==11:
					sf = used
				elif CSorder==12:
					sf = total
				elif CSorder==13:
					if total>0:
						sf = (1.0*used)/total
					else:
						sf = 0
				elif CSorder==20:
					sf = tdchunks
				elif CSorder==21:
					sf = tdused
				elif CSorder==22:
					sf = tdtotal
				elif CSorder==23:
					if tdtotal>0:
						sf = (1.0*tdused)/tdtotal
					else:
						sf = 0
				else:
					sf = 0
				servers.append((sf,host,ip1,ip2,ip3,ip4,port,v1,v2,v3,used,total,chunks,tdused,tdtotal,tdchunks,errcnt))
			servers.sort()
			if CSrev:
				servers.reverse()
			i = 1
			for sf,host,ip1,ip2,ip3,ip4,port,v1,v2,v3,used,total,chunks,tdused,tdtotal,tdchunks,errcnt in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td><td align="left">%s</td><td align="center">%u.%u.%u.%u</td><td align="center">%u</td><td align="center">%u.%u.%u</td>""" % (i,host,ip1,ip2,ip3,ip4,port,v1,v2,v3))
				out.append("""		<td align="right">%u</td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (chunks,decimal_number(used),humanize_number(used,"&nbsp;"),decimal_number(total),humanize_number(total,"&nbsp;")))
				if (total>0):
					out.append("""		<td><div class="box"><div class="progress" style="width:%upx;"></div><div class="value">%.2f</div></div></td>""" % (int((used*200.0)/total),(used*100.0)/total))
				else:
					out.append("""		<td><div class="box"><div class="progress" style="width:0px;"></div><div class="value">-</div></div></td>""")
				out.append("""		<td align="right">%u</td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (tdchunks,decimal_number(tdused),humanize_number(tdused,"&nbsp;"),decimal_number(tdtotal),humanize_number(tdtotal,"&nbsp;")))
				if (tdtotal>0):
					out.append("""		<td><div class="box"><div class="progress" style="width:%upx;"></div><div class="value">%.2f</div></div></td>""" % (int((tdused*200.0)/tdtotal),(tdused*100.0)/tdtotal))
				else:
					out.append("""		<td><div class="box"><div class="progress" style="width:0px;"></div><div class="value">-</div></div></td>""")
				out.append("""	</tr>""")
				i+=1
		elif cmd==MATOCL_CSERV_LIST and masterversion<(1,5,13) and (length%50)==0:
			data = myrecv(s,length)
			n = length/50
			servers = []
			for i in xrange(n):
				d = data[i*50:(i+1)*50]
				ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBHQQLQQLL",d)
				try:
					host = (socket.gethostbyaddr("%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)))[0]
				except Exception:
					host = "(unresolved)"
				if CSorder==1:
					sf = host
				elif CSorder==2 or CSorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif CSorder==3:
					sf = port
				elif CSorder==4:
					sf = 0
				elif CSorder==10:
					sf = chunks
				elif CSorder==11:
					sf = used
				elif CSorder==12:
					sf = total
				elif CSorder==13:
					if total>0:
						sf = (1.0*used)/total
					else:
						sf = 0
				elif CSorder==20:
					sf = tdchunks
				elif CSorder==21:
					sf = tdused
				elif CSorder==22:
					sf = tdtotal
				elif CSorder==23:
					if tdtotal>0:
						sf = (1.0*tdused)/tdtotal
					else:
						sf = 0
				else:
					sf = 0
				servers.append((sf,host,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt))
			servers.sort()
			i = 1
			for sf,host,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td><td align="left">%s</td><td align="center">%u.%u.%u.%u</td><td align="center">%u</td><td align="center">???</td>""" % (i,host,ip1,ip2,ip3,ip4,port))
				out.append("""		<td align="right">%u</td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (chunks,decimal_number(used),humanize_number(used,"&nbsp;"),decimal_number(total),humanize_number(total,"&nbsp;")))
				if (total>0):
					out.append("""		<td><div class="box"><div class="progress" style="width:%upx;"></div><div class="value">%.2f</div></div></td>""" % (int((used*200.0)/total),(used*100.0)/total))
				else:
					out.append("""		<td><div class="box"><div class="progress" style="width:0px;"></div><div class="value">-</div></div></td>""")
				out.append("""		<td align="right">%u</td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (tdchunks,decimal_number(tdused),humanize_number(tdused,"&nbsp;"),decimal_number(tdtotal),humanize_number(tdtotal,"&nbsp;")))
				if (tdtotal>0):
					out.append("""		<td><div class="box"><div class="progress" style="width:%upx;"></div><div class="value">%.2f</div></div></td>""" % (int((tdused*200.0)/tdtotal),(tdused*100.0)/tdtotal))
				else:
					out.append("""		<td><div class="box"><div class="progress" style="width:0px;"></div><div class="value">-</div></div></td>""")
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

	if masterversion>=(1,6,5):
		out = []

		try:
			MBorder = int(fields.getvalue("MBorder"))
		except Exception:
			MBorder = 0
		try:
			MBrev = int(fields.getvalue("MBrev"))
		except Exception:
			MBrev = 0

		try:
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="4">Metadata Backup Loggers</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th>#</th>""")
			out.append("""		<th><a href="%s">host</a></th>""" % (createorderlink("MB",1)))
			out.append("""		<th><a href="%s">ip</a></th>""" % (createorderlink("MB",2)))
			out.append("""		<th><a href="%s">version</a></th>""" % (createorderlink("MB",3)))
			out.append("""	</tr>""")

			s = socket.socket()
			s.connect((masterhost,masterport))
			mysend(s,struct.pack(">LL",CLTOMA_MLOG_LIST,0))
			header = myrecv(s,8)
			cmd,length = struct.unpack(">LL",header)
			if cmd==MATOCL_MLOG_LIST and (length%8)==0:
				data = myrecv(s,length)
				n = length/8
				servers = []
				for i in xrange(n):
					d = data[i*8:(i+1)*8]
					v1,v2,v3,ip1,ip2,ip3,ip4 = struct.unpack(">HBBBBBB",d)
					try:
						host = (socket.gethostbyaddr("%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)))[0]
					except Exception:
						host = "(unresolved)"
					if MBorder==1:
						sf = host
					elif MBorder==2 or MBorder==0:
						sf = (ip1,ip2,ip3,ip4)
					elif MBorder==3:
						sf = (v1,v2,v3)
					servers.append((sf,host,ip1,ip2,ip3,ip4,v1,v2,v3))
				servers.sort()
				if MBrev:
					servers.reverse()
				i = 1
				for sf,host,ip1,ip2,ip3,ip4,v1,v2,v3 in servers:
					out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
					out.append("""		<td align="right">%u</td><td align="left">%s</td><td align="center">%u.%u.%u.%u</td><td align="center">%u.%u.%u</td>""" % (i,host,ip1,ip2,ip3,ip4,v1,v2,v3))
					out.append("""	</tr>""")
					i+=1
			out.append("""</table>""")
			s.close()
			print "\n".join(out)
		except Exception:
			print """<table class="FR" cellspacing="0">"""
			print """<tr><td align="left"><pre>"""
			traceback.print_exc(file=sys.stdout)
			print """</pre></td></tr>"""
			print """</table>"""

		print """<br/>"""

if "HD" in sectionset:
	out = []

	try:
		HDorder = int(fields.getvalue("HDorder"))
	except Exception:
		HDorder = 0
	try:
		HDrev = int(fields.getvalue("HDrev"))
	except Exception:
		HDrev = 0
	try:
		HDperiod = int(fields.getvalue("HDperiod"))
	except Exception:
		HDperiod = 0
	try:
		HDtime = int(fields.getvalue("HDtime"))
	except Exception:
		HDtime = 0
	try:
		HDaddrname = int(fields.getvalue("HDaddrname"))
	except Exception:
		HDaddrname = 0

	try:
		# get cs list
		hostlist = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_CSERV_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_CSERV_LIST and masterversion>=(1,5,13) and (length%54)==0:
			data = myrecv(s,length)
			n = length/54
			servers = []
			for i in xrange(n):
				d = data[i*54:(i+1)*54]
				v1,v2,v3,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">HBBBBBBHQQLQQLL",d)
				hostlist.append((v1,v2,v3,ip1,ip2,ip3,ip4,port))
		elif cmd==MATOCL_CSERV_LIST and masterversion<(1,5,13) and (length%50)==0:
			data = myrecv(s,length)
			n = length/50
			servers = []
			for i in xrange(n):
				d = data[i*50:(i+1)*50]
				ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBHQQLQQLL",d)
				hostlist.append((1,5,0,ip1,ip2,ip3,ip4,port))
		s.close()

		# get hdd lists one by one
		hdd = []
		for v1,v2,v3,ip1,ip2,ip3,ip4,port in hostlist:
			hostip = "%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)
			try:
				hoststr = (socket.gethostbyaddr(hostip))[0]
			except Exception:
				hoststr = "(unresolved)"
			if port>0:
				if (v1,v2,v3)<=(1,6,8):
					s = socket.socket()
					s.connect((hostip,port))
					mysend(s,struct.pack(">LL",CLTOCS_HDD_LIST_V1,0))
					header = myrecv(s,8)
					cmd,length = struct.unpack(">LL",header)
					if cmd==CSTOCL_HDD_LIST_V1:
						data = myrecv(s,length)
						while length>0:
							plen = ord(data[0])
							if HDaddrname==1:
								path = "%s:%u:%s" % (hoststr,port,data[1:plen+1])
							else:
								path = "%s:%u:%s" % (hostip,port,data[1:plen+1])
							flags,errchunkid,errtime,used,total,chunkscnt = struct.unpack(">BQLQQL",data[plen+1:plen+34])
							length -= plen+34
							data = data[plen+34:]
							if HDorder==1 or HDorder==0:
								sf = (ip1,ip2,ip3,ip4,port,data[1:plen+1])
							elif HDorder==2:
								sf = chunkscnt
							elif HDorder==3:
								sf = errtime
							elif HDorder==4:
								sf = -flags
							elif HDorder==20:
								sf = used
							elif HDorder==21:
								sf = total
							elif HDorder==22:
								if total>0:
									sf = (1.0*used)/total
								else:
									sf = 0
							else:
								sf = 0
							hdd.append((sf,path,flags,errchunkid,errtime,used,total,chunkscnt,0,0,0,0,0,0,0,0,0,0,0,0))
					s.close()
				else:
					s = socket.socket()
					s.connect((hostip,port))
					mysend(s,struct.pack(">LL",CLTOCS_HDD_LIST_V2,0))
					header = myrecv(s,8)
					cmd,length = struct.unpack(">LL",header)
					if cmd==CSTOCL_HDD_LIST_V2:
						data = myrecv(s,length)
						while length>0:
							entrysize = struct.unpack(">H",data[:2])[0]
							entry = data[2:2+entrysize]
							data = data[2+entrysize:]
							length -= 2+entrysize;

							plen = ord(entry[0])
							if HDaddrname==1:
								path = "%s:%u:%s" % (hoststr,port,entry[1:plen+1])
							else:
								path = "%s:%u:%s" % (hostip,port,entry[1:plen+1])
							flags,errchunkid,errtime,used,total,chunkscnt = struct.unpack(">BQLQQL",entry[plen+1:plen+34])
							rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = (0,0,0,0,0,0,0,0,0,0,0)
							if entrysize==plen+34+144:
								if HDperiod==0:
									rbytes,wbytes,usecreadsum,usecwritesum,rops,wops,usecreadmax,usecwritemax = struct.unpack(">QQQQLLLL",entry[plen+34:plen+34+48])
								elif HDperiod==1:
									rbytes,wbytes,usecreadsum,usecwritesum,rops,wops,usecreadmax,usecwritemax = struct.unpack(">QQQQLLLL",entry[plen+34+48:plen+34+96])
								elif HDperiod==2:
									rbytes,wbytes,usecreadsum,usecwritesum,rops,wops,usecreadmax,usecwritemax = struct.unpack(">QQQQLLLL",entry[plen+34+96:plen+34+144])
							elif entrysize==plen+34+192:
								if HDperiod==0:
									rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = struct.unpack(">QQQQQLLLLLL",entry[plen+34:plen+34+64])
								elif HDperiod==1:
									rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = struct.unpack(">QQQQQLLLLLL",entry[plen+34+64:plen+34+128])
								elif HDperiod==2:
									rbytes,wbytes,usecreadsum,usecwritesum,usecfsyncsum,rops,wops,fsyncops,usecreadmax,usecwritemax,usecfsyncmax = struct.unpack(">QQQQQLLLLLL",entry[plen+34+128:plen+34+192])
							if usecreadsum>0:
								rbw = rbytes*1000000/usecreadsum
							else:
								rbw = 0
							if usecwritesum+usecfsyncsum>0:
								wbw = wbytes*1000000/(usecwritesum+usecfsyncsum)
							else:
								wbw = 0
							if HDtime==1:
								if rops>0:
									rtime = usecreadsum/rops
								else:
									rtime = 0
								if wops>0:
									wtime = usecwritesum/wops
								else:
									wtime = 0
								if fsyncops>0:
									fsynctime = usecfsyncsum/fsyncops
								else:
									fsynctime = 0
							else:
								rtime = usecreadmax
								wtime = usecwritemax
								fsynctime = usecfsyncmax
							if HDorder==1 or HDorder==0:
								sf = (ip1,ip2,ip3,ip4,port,data[1:plen+1])
							elif HDorder==2:
								sf = chunkscnt
							elif HDorder==3:
								sf = errtime
							elif HDorder==4:
								sf = -flags
							elif HDorder==5:
								sf = rbw
							elif HDorder==6:
								sf = wbw
							elif HDorder==7:
								sf = -rtime
							elif HDorder==8:
								sf = -wtime
							elif HDorder==9:
								sf = -fsynctime
							elif HDorder==10:
								sf = rops
							elif HDorder==11:
								sf = wops
							elif HDorder==12:
								sf = fsyncops
							elif HDorder==20:
								if flags&4:
									sf = used
								else:
									sf = 0
							elif HDorder==21:
								if flags&4:
									sf = total
								else:
									sf = 0
							elif HDorder==22:
								if flags&4 and total>0:
									sf = (1.0*used)/total
								else:
									sf = 0
							else:
								sf = 0
							hdd.append((sf,path,flags,errchunkid,errtime,used,total,chunkscnt,rbw,wbw,rtime,wtime,fsynctime,rops,wops,fsyncops,rbytes,wbytes,usecreadsum,usecwritesum))
					s.close()

		if len(hdd)>0:
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr><th colspan="16">Disks</th></tr>""")
			out.append("""	<tr>""")
			out.append("""		<th rowspan="3">#</th>""")
			out.append("""		<th colspan="4" rowspan="2">info</th>""")
			if HDperiod==2:
				out.append("""		<th colspan="8">I/O stats last day (switch to <a href="%s" class="VISIBLELINK">min</a>,<a href="%s" class="VISIBLELINK">hour</a>)</th>""" % (createlink({"HDperiod":"0"}),createlink({"HDperiod":"1"})))
			elif HDperiod==1:
				out.append("""		<th colspan="8">I/O stats last hour (switch to <a href="%s" class="VISIBLELINK">min</a>,<a href="%s" class="VISIBLELINK">day</a>)</th>""" % (createlink({"HDperiod":"0"}),createlink({"HDperiod":"2"})))
			else:
				out.append("""		<th colspan="8">I/O stats last min (switch to <a href="%s" class="VISIBLELINK">hour</a>,<a href="%s" class="VISIBLELINK">day</a>)</th>""" % (createlink({"HDperiod":"1"}),createlink({"HDperiod":"2"})))
			out.append("""		<th colspan="3" rowspan="2">space</th>""")
			out.append("""	</tr>""")
			out.append("""	<tr>""")
			out.append("""		<th colspan="2"><a style="cursor:default" title="average data transfer speed">transfer</a></th>""")
			if HDtime==1:
				out.append("""		<th colspan="3"><a style="cursor:default" title="average time of read or write chunk block (up to 64kB)">avg time</a> (<a href="%s" class="VISIBLELINK">switch to max</a>)</th>""" % (createlink({"HDtime":"0"})))
			else:
				out.append("""		<th colspan="3"><a style="cursor:default" title="max time of read or write one chunk block (up to 64kB)">max time</a> (<a href="%s" class="VISIBLELINK">switch to avg</a>)</th>""" % (createlink({"HDtime":"1"})))
			out.append("""		<th colspan="3"><a style="cursor:default" title="number of chunk block operations / chunk fsyncs"># of ops</a></th></tr>""")
			out.append("""	<tr>""")
			if HDaddrname==1:
				out.append("""		<th><a href="%s">name path</a> (<a href="%s" class="VISIBLELINK">switch to IP</a>)</th>""" % (createorderlink("HD",1),createlink({"HDaddrname":"0"})))
			else:
				out.append("""		<th><a href="%s">IP path</a> (<a href="%s" class="VISIBLELINK">switch to name</a>)</th>""" % (createorderlink("HD",1),createlink({"HDaddrname":"1"})))
			out.append("""		<th><a href="%s">chunks</a></th>""" % (createorderlink("HD",2)))
			out.append("""		<th><a href="%s">last error</a></th>""" % (createorderlink("HD",3)))
			out.append("""		<th><a href="%s">status</a></th>""" % (createorderlink("HD",4)))
			out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("HD",5)))
			out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("HD",6)))
			out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("HD",7)))
			out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("HD",8)))
			out.append("""		<th><a href="%s">fsync</a></th>""" % (createorderlink("HD",9)))
			out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("HD",10)))
			out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("HD",11)))
			out.append("""		<th><a href="%s">fsync</a></th>""" % (createorderlink("HD",12)))
			out.append("""		<th><a href="%s">used</a></th>""" % (createorderlink("HD",20)))
			out.append("""		<th><a href="%s">total</a></th>""" % (createorderlink("HD",21)))
			out.append("""		<th class="SMPROGBAR"><a href="%s">used (%%)</a></th>""" % (createorderlink("HD",22)))
			out.append("""	</tr>""")
			hdd.sort()
			if HDrev:
				hdd.reverse()
			i = 1
			for sf,path,flags,errchunkid,errtime,used,total,chunkscnt,rbw,wbw,rtime,wtime,fsynctime,rops,wops,fsyncops,rbytes,wbytes,rsum,wsum in hdd:
				if flags==1:
					if masterversion>=(1,6,10):
						status = 'marked for removal'
					else:
						status = 'to be empty'
				elif flags==2:
					status = 'damaged'
				elif flags==3:
					if masterversion>=(1,6,10):
						status = 'damaged, marked for removal'
					else:
						status = 'damaged, to be empty'
				elif flags==4 or flags==6:
					status = 'scanning'
				elif flags==5 or flags==7:
					status = 'marked for removal, scanning'
				else:
					status = 'ok'
				if errtime==0 and errchunkid==0:
					lerror = 'no errors'
				else:
					errtimetuple = time.localtime(errtime)
					lerror = '<a style="cursor:default" title="%s on chunk: %u">%s</a>' % (time.strftime("%Y-%m-%d %H:%M:%S",errtimetuple),errchunkid,time.strftime("%Y-%m-%d %H:%M",errtimetuple))
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td><td align="left">%s</td><td align="right">%u</td><td align="right">%s</td><td align="right">%s</td>""" % (i,path,chunkscnt,lerror,status))
				if rbw==0 and wbw==0 and rtime==0 and wtime==0 and rops==0 and wops==0:
					out.append("""		<td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>""")
				else:
					if rops>0:
						rbsize = rbytes/rops
					else:
						rbsize = 0
					if wops>0:
						wbsize = wbytes/wops
					else:
						wbsize = 0
					out.append("""		<td align="right"><a style="cursor:default" title="%s B/s">%sB/s</a></td><td align="right"><a style="cursor:default" title="%s B">%sB/s</a></td>""" % (decimal_number(rbw),humanize_number(rbw,"&nbsp;"),decimal_number(wbw),humanize_number(wbw,"&nbsp;")))
					out.append("""		<td align="right">%u us</td><td align="right">%u us</td><td align="right">%u us</td><td align="right"><a style="cursor:default" title="average block size: %u B">%u</a></td><td align="right"><a style="cursor:default" title="average block size: %u B">%u</a></td><td align="right">%u</td>""" % (rtime,wtime,fsynctime,rbsize,rops,wbsize,wops,fsyncops))
				if flags&4:
					out.append("""		<td colspan="3" align="right"><div class="box"><div class="progress" style="width:%upx;"></div><div class="value">%.0f%% scanned</div></div></td>""" % (int(used)*2,used))
				else:
					out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td><td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(used),humanize_number(used,"&nbsp;"),decimal_number(total),humanize_number(total,"&nbsp;")))
					if (total>0):
						out.append("""		<td><div class="smbox"><div class="progress" style="width:%upx;"></div><div class="value">%.2f</div></div></td>""" % (int((used*100.0)/total),(used*100.0)/total))
					else:
						out.append("""		<td><div class="smbox"><div class="progress" style="width:%upx;"></div><div class="value">-</div></div></td>""" % (0))
				out.append("""	</tr>""")
				i+=1
			out.append("""</table>""")

		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "EX" in sectionset:
	out = []

	try:
		EXorder = int(fields.getvalue("EXorder"))
	except Exception:
		EXorder = 0
	try:
		EXrev = int(fields.getvalue("EXrev"))
	except Exception:
		EXrev = 0

	try:
		out.append("""<table class="FR" cellspacing="0">""")
		out.append("""	<tr><th colspan="%u">Exports</th></tr>""" % (19 if masterversion>=(1,7,0) else 18 if masterversion>=(1,6,26) else 14))
		out.append("""	<tr>""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th colspan="2">ip&nbsp;range</th>""")
		out.append("""		<th rowspan="2"><a href="%s">path</a></th>""" % (createorderlink("EX",3)))
		out.append("""		<th rowspan="2"><a href="%s">minversion</a></th>""" % (createorderlink("EX",4)))
		out.append("""		<th rowspan="2"><a href="%s">alldirs</a></th>""" % (createorderlink("EX",5)))
		out.append("""		<th rowspan="2"><a href="%s">password</a></th>""" % (createorderlink("EX",6)))
		out.append("""		<th rowspan="2"><a href="%s">ro/rw</a></th>""" % (createorderlink("EX",7)))
		out.append("""		<th rowspan="2"><a href="%s">restricted&nbsp;ip</a></th>""" % (createorderlink("EX",8)))
		out.append("""		<th rowspan="2"><a href="%s">ignore&nbsp;gid</a></th>""" % (createorderlink("EX",9)))
		if masterversion>=(1,7,0):
			out.append("""		<th rowspan="2"><a href="%s">can&nbsp;change&nbsp;quota</a></th>""" % (createorderlink("EX",10)))
		out.append("""		<th colspan="2">map&nbsp;root</th>""")
		out.append("""		<th colspan="2">map&nbsp;users</th>""")
		if masterversion>=(1,6,26):
			out.append("""		<th colspan="2">goal&nbsp;limit</th>""")
			out.append("""		<th colspan="2">trashtime&nbsp;limit</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="%s">from</a></th>""" % (createorderlink("EX",1)))
		out.append("""		<th><a href="%s">to</a></th>""" % (createorderlink("EX",2)))
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("EX",11)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("EX",12)))
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("EX",13)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("EX",14)))
		if masterversion>=(1,6,26):
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("EX",15)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("EX",16)))
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("EX",17)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("EX",18)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		if masterversion>=(1,6,26):
			mysend(s,struct.pack(">LLB",CLTOMA_EXPORTS_INFO,1,1))
		else:
			mysend(s,struct.pack(">LL",CLTOMA_EXPORTS_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_EXPORTS_INFO and masterversion>=(1,5,14):
			data = myrecv(s,length)
			servers = []
			pos = 0
			while pos<length:
				fip1,fip2,fip3,fip4,tip1,tip2,tip3,tip4,pleng = struct.unpack(">BBBBBBBBL",data[pos:pos+12])
				ipfrom = "%d.%d.%d.%d" % (fip1,fip2,fip3,fip4)
				ipto = "%d.%d.%d.%d" % (tip1,tip2,tip3,tip4)
				pos+=12
				path = data[pos:pos+pleng]
				pos+=pleng
				if masterversion>=(1,6,26):
					v1,v2,v3,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime = struct.unpack(">HBBBBLLLLBBLL",data[pos:pos+32])
					pos+=32
					if mingoal<=1 and maxgoal>=9:
						mingoal = None
						maxgoal = None
					if mintrashtime==0 and maxtrashtime==0xFFFFFFFF:
						mintrashtime = None
						maxtrashtime = None
				elif masterversion>=(1,6,1):
					v1,v2,v3,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid = struct.unpack(">HBBBBLLLL",data[pos:pos+22])
					mingoal = None;
					maxgoal = None;
					mintrashtime = None;
					maxtrashtime = None;
					pos+=22
				else:
					v1,v2,v3,exportflags,sesflags,rootuid,rootgid = struct.unpack(">HBBBBLL",data[pos:pos+14])
					mapalluid = 0
					mapallgid = 0
					mingoal = None;
					maxgoal = None;
					mintrashtime = None;
					maxtrashtime = None;
					pos+=14
				ver = "%d.%d.%d" % (v1,v2,v3)
				if path=='.':
					meta=1
				else:
					meta=0
				if EXorder==1 or EXorder==0:
					sf = (fip1,fip2,fip3,fip4)
				elif EXorder==2:
					sf = (tip1,tip2,tip3,tip4)
				elif EXorder==3:
					sf = path
				elif EXorder==4:
					sf = (v1,v2,v3)
				elif EXorder==5:
					if meta:
						sf = None
					else:
						sf = exportflags&1
				elif EXorder==6:
					sf = exportflags&2
				elif EXorder==7:
					sf = sesflags&1
				elif EXorder==8:
					sf = 2-(sesflags&2)
				elif EXorder==9:
					if meta:
						sf = None
					else:
						sf = sesflags&4
				elif EXorder==10:
					if meta:
						sf = None
					else:
						sf = sesflags&8
				elif EXorder==11:
					if meta:
						sf = None
					else:
						sf = rootuid
				elif EXorder==12:
					if meta:
						sf = None
					else:
						sf = rootgid
				elif EXorder==13:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapalluid
				elif EXorder==14:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapalguid
				elif EXorder==15:
					sf = mingoal
				elif EXorder==16:
					sf = maxgoal
				elif EXorder==17:
					sf = mintrashtime
				elif EXorder==18:
					sf = maxtrashtime
				else:
					sf = 0
				servers.append((sf,ipfrom,ipto,path,meta,ver,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime))
			servers.sort()
			if EXrev:
				servers.reverse()
			i = 1
			for sf,ipfrom,ipto,path,meta,ver,exportflags,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td>""" % i)
				out.append("""		<td align="center">%s</td>""" % ipfrom)
				out.append("""		<td align="center">%s</td>""" % ipto)
				out.append("""		<td align="left">%s</td>""" % (".&nbsp;(META)" if meta else path))
				out.append("""		<td align="center">%s</td>""" % ver)
				out.append("""		<td align="center">%s</td>""" % ("-" if meta else "yes" if exportflags&1 else "no"))
				out.append("""		<td align="center">%s</td>""" % ("yes" if exportflags&2 else "no"))
				out.append("""		<td align="center">%s</td>""" % ("ro" if sesflags&1 else "rw"))
				out.append("""		<td align="center">%s</td>""" % ("no" if sesflags&2 else "yes"))
				out.append("""		<td align="center">%s</td>""" % ("-" if meta else "yes" if sesflags&4 else "no"))
				if masterversion>=(1,7,0):
					out.append("""		<td align="center">%s</td>""" % ("-" if meta else "yes" if sesflags&8 else "no"))
				if meta:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % rootuid)
					out.append("""		<td align="right">%u</td>""" % rootgid)
				if meta or (sesflags&16)==0:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % mapalluid)
					out.append("""		<td align="right">%u</td>""" % mapallgid)
				if masterversion>=(1,6,26):
					if mingoal!=None and maxgoal!=None:
						out.append("""		<td align="right">%u</td>""" % mingoal)
						out.append("""		<td align="right">%u</td>""" % maxgoal)
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
					if mintrashtime!=None and maxtrashtime!=None:
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(mintrashtime),timeduration_to_shortstr(mintrashtime)))
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(maxtrashtime),timeduration_to_shortstr(maxtrashtime)))
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "ML" in sectionset:
	out = []

	try:
		MLorder = int(fields.getvalue("MLorder"))
	except Exception:
		MLorder = 0
	try:
		MLrev = int(fields.getvalue("MLrev"))
	except Exception:
		MLrev = 0

	try:
		out.append("""<table class="CR" cellspacing="0">""")
		out.append("""	<tr><th colspan="20">Active mounts</th></tr>""")
		out.append("""	<tr>""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">host</a></th>""" % (createorderlink("ML",1)))
		out.append("""		<th rowspan="2"><a href="%s">ip</a></th>""" % (createorderlink("ML",2)))
		out.append("""		<th rowspan="2"><a href="%s">version</a></th>""" % (createorderlink("ML",3)))
		out.append("""		<th colspan="16">operations current hour/last hour</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="%s">statfs</a></th>""" % (createorderlink("ML",100)))
		out.append("""		<th><a href="%s">getattr</a></th>""" % (createorderlink("ML",101)))
		out.append("""		<th><a href="%s">setattr</a></th>""" % (createorderlink("ML",102)))
		out.append("""		<th><a href="%s">lookup</a></th>""" % (createorderlink("ML",103)))
		out.append("""		<th><a href="%s">mkdir</a></th>""" % (createorderlink("ML",104)))
		out.append("""		<th><a href="%s">rmdir</a></th>""" % (createorderlink("ML",105)))
		out.append("""		<th><a href="%s">symlink</a></th>""" % (createorderlink("ML",106)))
		out.append("""		<th><a href="%s">readlink</a></th>""" % (createorderlink("ML",107)))
		out.append("""		<th><a href="%s">mknod</a></th>""" % (createorderlink("ML",108)))
		out.append("""		<th><a href="%s">unlink</a></th>""" % (createorderlink("ML",109)))
		out.append("""		<th><a href="%s">rename</a></th>""" % (createorderlink("ML",110)))
		out.append("""		<th><a href="%s">link</a></th>""" % (createorderlink("ML",111)))
		out.append("""		<th><a href="%s">readdir</a></th>""" % (createorderlink("ML",112)))
		out.append("""		<th><a href="%s">open</a></th>""" % (createorderlink("ML",113)))
		out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("ML",114)))
		out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("ML",115)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_SESSION_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_SESSION_LIST and masterversion<=(1,5,13) and (length%136)==0:
			data = myrecv(s,length)
			n = length/136
			servers = []
			for i in xrange(n):
				d = data[i*136:(i+1)*136]
				addrdata = d[0:8]
				stats_c = []
				stats_l = []
				ip1,ip2,ip3,ip4,spare,v1,v2,v3 = struct.unpack(">BBBBBBBB",addrdata)
				ipnum = "%d.%d.%d.%d" % (ip1,ip2,ip3,ip4)
				if v1==0 and v2==0:
					if v3==2:
						ver = "1.3.x"
					elif v3==3:
						ver = "1.4.x"
					else:
						ver = "unknown"
				else:
					ver = "%d.%d.%d" % (v1,v2,v3)
				for i in xrange(16):
					stats_c.append(struct.unpack(">L",d[i*4+8:i*4+12]))
					stats_l.append(struct.unpack(">L",d[i*4+72:i*4+76]))
				try:
					host = (socket.gethostbyaddr(ipnum))[0]
				except Exception:
					host = "(unresolved)"
				if MLorder==1:
					sf = host
				elif MLorder==2 or MLorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif MLorder==3:
					sf = (v1,v2,v3)
				elif MLorder>=100 and MLorder<=115:
					sf = stats_c[MLorder-100][0]+stats_l[MLorder-100][0]
				else:
					sf = 0
				servers.append((sf,host,ipnum,ver,stats_c,stats_l))
			servers.sort()
			if MLrev:
				servers.reverse()
			i = 1
			for sf,host,ipnum,ver,stats_c,stats_l in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+1))
				out.append("""		<td align="right" rowspan="2">%u</td>""" % i)
				out.append("""		<td align="left" rowspan="2">%s</td>""" % host)
				out.append("""		<td align="center" rowspan="2">%s</td>""" % ipnum)
				out.append("""		<td align="center" rowspan="2">%s</td>""" % ver)
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_c[st]))
				out.append("""	</tr>""")
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+2))
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_l[st]))
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "MS" in sectionset:
	out = []

	try:
		MSorder = int(fields.getvalue("MSorder"))
	except Exception:
		MSorder = 0
	try:
		MSrev = int(fields.getvalue("MSrev"))
	except Exception:
		MSrev = 0

	try:
		out.append("""<table class="FR" cellspacing="0">""")
		out.append("""	<tr><th colspan="%u">Active mounts (parameters)</th></tr>""" % (19 if masterversion>=(1,7,0) else 18 if masterversion>=(1,6,26) else 14))
		out.append("""	<tr>""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">session&nbsp;id</a></th>""" % (createorderlink("MS",1)))
		out.append("""		<th rowspan="2"><a href="%s">host</a></th>""" % (createorderlink("MS",2)))
		out.append("""		<th rowspan="2"><a href="%s">ip</a></th>""" % (createorderlink("MS",3)))
		out.append("""		<th rowspan="2"><a href="%s">mount&nbsp;point</a></th>""" % (createorderlink("MS",4)))
		out.append("""		<th rowspan="2"><a href="%s">version</a></th>""" % (createorderlink("MS",5)))
		out.append("""		<th rowspan="2"><a href="%s">root&nbsp;dir</a></th>""" % (createorderlink("MS",6)))
		out.append("""		<th rowspan="2"><a href="%s">ro/rw</a></th>""" % (createorderlink("MS",7)))
		out.append("""		<th rowspan="2"><a href="%s">restricted&nbsp;ip</a></th>""" % (createorderlink("MS",8)))
		out.append("""		<th rowspan="2"><a href="%s">ignore&nbsp;gid</a></th>""" % (createorderlink("MS",9)))
		if masterversion>=(1,7,0):
			out.append("""		<th rowspan="2"><a href="%s">can&nbsp;change&nbsp;quota</a></th>""" % (createorderlink("MS",10)))
		out.append("""		<th colspan="2">map&nbsp;root</th>""")
		out.append("""		<th colspan="2">map&nbsp;users</th>""")
		if masterversion>=(1,6,26):
			out.append("""		<th colspan="2">goal&nbsp;limits</th>""")
			out.append("""		<th colspan="2">trashtime&nbsp;limits</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("MS",11)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("MS",12)))
		out.append("""		<th><a href="%s">uid</a></th>""" % (createorderlink("MS",13)))
		out.append("""		<th><a href="%s">gid</a></th>""" % (createorderlink("MS",14)))
		if masterversion>=(1,6,26):
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("MS",15)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("MS",16)))
			out.append("""		<th><a href="%s">min</a></th>""" % (createorderlink("MS",17)))
			out.append("""		<th><a href="%s">max</a></th>""" % (createorderlink("MS",18)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		if masterversion>=(1,6,26):
			mysend(s,struct.pack(">LLB",CLTOMA_SESSION_LIST,1,1))
		else:
			mysend(s,struct.pack(">LL",CLTOMA_SESSION_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_SESSION_LIST and masterversion>=(1,5,14):
			data = myrecv(s,length)
			servers = []
			if masterversion<(1,6,21):
				statscnt = 16
				pos = 0
			elif masterversion==(1,6,21):
				statscnt = 21
				pos = 0
			else:
				statscnt = struct.unpack(">H",data[0:2])[0]
				pos = 2
			while pos<length:
				sessionid,ip1,ip2,ip3,ip4,v1,v2,v3,ileng = struct.unpack(">LBBBBHBBL",data[pos:pos+16])
				ipnum = "%d.%d.%d.%d" % (ip1,ip2,ip3,ip4)
				ver = "%d.%d.%d" % (v1,v2,v3)
				pos+=16
				info = data[pos:pos+ileng]
				pos+=ileng
				pleng = struct.unpack(">L",data[pos:pos+4])[0]
				pos+=4
				path = data[pos:pos+pleng]
				pos+=pleng
				if masterversion>=(1,6,26):
					sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime = struct.unpack(">BLLLLBBLL",data[pos:pos+27])
					pos+=27
					if mingoal<=1 and maxgoal>=9:
						mingoal = None
						maxgoal = None
					if mintrashtime==0 and maxtrashtime==0xFFFFFFFF:
						mintrashtime = None
						maxtrashtime = None
				elif masterversion>=(1,6,1):
					sesflags,rootuid,rootgid,mapalluid,mapallgid = struct.unpack(">BLLLL",data[pos:pos+17])
					mingoal = None
					maxgoal = None
					mintrashtime = None
					maxtrashtime = None
					pos+=17
				else:
					sesflags,rootuid,rootgid = struct.unpack(">BLL",data[pos:pos+9])
					mapalluid = 0
					mapallgid = 0
					mingoal = None
					maxgoal = None
					mintrashtime = None
					maxtrashtime = None
					pos+=9
				pos+=8*statscnt		# skip stats
				if path=='.':
					meta=1
				else:
					meta=0
				try:
					host = (socket.gethostbyaddr(ipnum))[0]
				except Exception:
					host = "(unresolved)"
#				if path=="":
#					path="(empty)"
				if MSorder==1:
					sf = sessionid
				elif MSorder==2:
					sf = host
				elif MSorder==3 or MSorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif MSorder==4:
					sf = info
				elif MSorder==5:
					sf = (v1,v2,v3)
				elif MSorder==6:
					sf = path
				elif MSorder==7:
					sf = sesflags&1
				elif MSorder==8:
					sf = 2-(sesflags&2)
				elif MSorder==9:
					if meta:
						sf = None
					else:
						sf = sesflags&4
				elif MSorder==10:
					if meta:
						sf = None
					else:
						sf = sesflags&8
				elif MSorder==11:
					if meta:
						sf = None
					else:
						sf = rootuid
				elif MSorder==12:
					if meta:
						sf = None
					else:
						sf = rootgid
				elif MSorder==13:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapalluid
				elif MSorder==14:
					if meta or (sesflags&16)==0:
						sf = None
					else:
						sf = mapallgid
				elif MSorder==15:
					sf = mingoal
				elif MSorder==16:
					sf = maxgoal
				elif MSorder==17:
					sf = mintrashtime
				elif MSorder==18:
					sf = maxtrashtime
				else:
					sf = 0
				servers.append((sf,sessionid,host,ipnum,info,ver,meta,path,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime))
			servers.sort()
			if MSrev:
				servers.reverse()
			i = 1
			for sf,sessionid,host,ipnum,info,ver,meta,path,sesflags,rootuid,rootgid,mapalluid,mapallgid,mingoal,maxgoal,mintrashtime,maxtrashtime in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td>""" % i)
				out.append("""		<td align="center">%u</td>""" % sessionid)
				out.append("""		<td align="left">%s</td>""" % host)
				out.append("""		<td align="center">%s</td>""" % ipnum)
				out.append("""		<td align="left">%s</td>""" % info)
				out.append("""		<td align="center">%s</td>""" % ver)
				if meta:
					out.append("""		<td align="left">.&nbsp;(META)</td>""")
				else:
					out.append("""		<td align="left">%s</td>""" % path)
				if sesflags&1:
					out.append("""		<td align="center">ro</td>""")
				else:
					out.append("""		<td align="center">rw</td>""")
				if sesflags&2:
					out.append("""		<td align="center">no</td>""")
				else:
					out.append("""		<td align="center">yes</td>""")
				if meta:
					out.append("""		<td align="center">-</td>""")
				elif sesflags&4:
					out.append("""		<td align="center">yes</td>""")
				else:
					out.append("""		<td align="center">no</td>""")
				if masterversion>=(1,7,0):
					if meta:
						out.append("""		<td align="center">-</td>""")
					elif sesflags&8:
						out.append("""		<td align="center">yes</td>""")
					else:
						out.append("""		<td align="center">no</td>""")
				if meta:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % rootuid)
					out.append("""		<td align="right">%u</td>""" % rootgid)
				if meta or (sesflags&16)==0:
					out.append("""		<td align="center">-</td>""")
					out.append("""		<td align="center">-</td>""")
				else:
					out.append("""		<td align="right">%u</td>""" % mapalluid)
					out.append("""		<td align="right">%u</td>""" % mapallgid)
				if masterversion>=(1,6,26):
					if mingoal!=None and maxgoal!=None:
						out.append("""		<td align="right">%u</td>""" % mingoal)
						out.append("""		<td align="right">%u</td>""" % maxgoal)
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
					if mintrashtime!=None and maxtrashtime!=None:
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(mintrashtime),timeduration_to_shortstr(mintrashtime)))
						out.append("""		<td align="right"><a style="cursor:default" title="%s">%s</a></td>""" % (timeduration_to_fullstr(maxtrashtime),timeduration_to_shortstr(maxtrashtime)))
					else:
						out.append("""		<td align="center">-</td>""")
						out.append("""		<td align="center">-</td>""")
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "MO" in sectionset:
	out = []

	try:
		MOorder = int(fields.getvalue("MOorder"))
	except Exception:
		MOorder = 0
	try:
		MOrev = int(fields.getvalue("MOrev"))
	except Exception:
		MOrev = 0

	try:
		out.append("""<table class="CR" cellspacing="0">""")
		out.append("""	<tr><th colspan="21">Active mounts (operations)</th></tr>""")
		out.append("""	<tr>""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">host</a></th>""" % (createorderlink("MO",1)))
		out.append("""		<th rowspan="2"><a href="%s">ip</a></th>""" % (createorderlink("MO",2)))
		out.append("""		<th rowspan="2"><a href="%s">mount&nbsp;point</a></th>""" % (createorderlink("MO",3)))
		out.append("""		<th colspan="17">operations current hour/last hour</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="%s">statfs</a></th>""" % (createorderlink("MO",100)))
		out.append("""		<th><a href="%s">getattr</a></th>""" % (createorderlink("MO",101)))
		out.append("""		<th><a href="%s">setattr</a></th>""" % (createorderlink("MO",102)))
		out.append("""		<th><a href="%s">lookup</a></th>""" % (createorderlink("MO",103)))
		out.append("""		<th><a href="%s">mkdir</a></th>""" % (createorderlink("MO",104)))
		out.append("""		<th><a href="%s">rmdir</a></th>""" % (createorderlink("MO",105)))
		out.append("""		<th><a href="%s">symlink</a></th>""" % (createorderlink("MO",106)))
		out.append("""		<th><a href="%s">readlink</a></th>""" % (createorderlink("MO",107)))
		out.append("""		<th><a href="%s">mknod</a></th>""" % (createorderlink("MO",108)))
		out.append("""		<th><a href="%s">unlink</a></th>""" % (createorderlink("MO",109)))
		out.append("""		<th><a href="%s">rename</a></th>""" % (createorderlink("MO",110)))
		out.append("""		<th><a href="%s">link</a></th>""" % (createorderlink("MO",111)))
		out.append("""		<th><a href="%s">readdir</a></th>""" % (createorderlink("MO",112)))
		out.append("""		<th><a href="%s">open</a></th>""" % (createorderlink("MO",113)))
		out.append("""		<th><a href="%s">read</a></th>""" % (createorderlink("MO",114)))
		out.append("""		<th><a href="%s">write</a></th>""" % (createorderlink("MO",115)))
		out.append("""		<th><a href="%s">total</a></th>""" % (createorderlink("MO",150)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_SESSION_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_SESSION_LIST and masterversion>=(1,5,14):
			data = myrecv(s,length)
			servers = []
			if masterversion<(1,6,21):
				statscnt = 16
				pos = 0
			elif masterversion==(1,6,21):
				statscnt = 21
				pos = 0
			else:
				statscnt = struct.unpack(">H",data[0:2])[0]
				pos = 2
			while pos<length:
				sessionid,ip1,ip2,ip3,ip4,v1,v2,v3,ileng = struct.unpack(">LBBBBHBBL",data[pos:pos+16])
				ipnum = "%d.%d.%d.%d" % (ip1,ip2,ip3,ip4)
				ver = "%d.%d.%d" % (v1,v2,v3)
				pos+=16
				info = data[pos:pos+ileng]
				pos+=ileng
				pleng = struct.unpack(">L",data[pos:pos+4])[0]
				pos+=4
				path = data[pos:pos+pleng]
				pos+=pleng
				# sesflags,rootuid,rootgid,mapalluid,mapallgid = struct.unpack(">BLLLL",data[pos:pos+17])
				if masterversion>=(1,6,0):
					pos+=17
				else:
					pos+=9
				if statscnt<16:
					stats_c = struct.unpack(">"+"L"*statscnt,data[pos:pos+4*statscnt])+(0,)*(16-statscnt)
					pos+=statscnt*4
					stats_l = struct.unpack(">"+"L"*statscnt,data[pos:pos+4*statscnt])+(0,)*(16-statscnt)
					pos+=statscnt*4
				else:
					stats_c = struct.unpack(">LLLLLLLLLLLLLLLL",data[pos:pos+64])
					pos+=statscnt*4
					stats_l = struct.unpack(">LLLLLLLLLLLLLLLL",data[pos:pos+64])
					pos+=statscnt*4
				try:
					host = (socket.gethostbyaddr(ipnum))[0]
				except Exception:
					host = "(unresolved)"
				if MOorder==1:
					sf = host
				elif MOorder==2 or MOorder==0:
					sf = (ip1,ip2,ip3,ip4)
				elif MOorder==3:
					sf = info
				elif MOorder>=100 and MOorder<=115:
					sf = -(stats_c[MOorder-100]+stats_l[MOorder-100])
				elif MOorder==150:
					sf = -(sum(stats_c)+sum(stats_l))
				else:
					sf = 0
				if path!='.':
					servers.append((sf,host,ipnum,info,stats_c,stats_l))
			servers.sort()
			if MOrev:
				servers.reverse()
			i = 1
			for sf,host,ipnum,info,stats_c,stats_l in servers:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+1))
				out.append("""		<td align="right" rowspan="2">%u</td>""" % i)
				out.append("""		<td align="left" rowspan="2">%s</td>""" % host)
				out.append("""		<td align="center" rowspan="2">%s</td>""" % ipnum)
				out.append("""		<td align="left" rowspan="2">%s</td>""" % info)
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_c[st]))
				out.append("""		<td align="right">%u</td>""" % (sum(stats_c)))
				out.append("""	</tr>""")
				out.append("""	<tr class="C%u">""" % (((i-1)%2)*2+2))
				for st in xrange(16):
					out.append("""		<td align="right">%u</td>""" % (stats_l[st]))
				out.append("""		<td align="right">%u</td>""" % (sum(stats_l)))
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "QU" in sectionset:
	out = []

	try:
		QUorder = int(fields.getvalue("QUorder"))
	except Exception:
		QUorder = 0
	try:
		QUrev = int(fields.getvalue("QUrev"))
	except Exception:
		QUrev = 0

	try:
		out.append("""<table class="FR" cellspacing="0">""")
		out.append("""	<tr><th colspan="16">Active quotas</th></tr>""")
		out.append("""	<tr>""")
		out.append("""		<th rowspan="2">#</th>""")
		out.append("""		<th rowspan="2"><a href="%s">path</a></th>""" % (createorderlink("QU",11)))
		out.append("""		<th rowspan="2"><a href="%s">exceeded</a></th>""" % (createorderlink("QU",2)))
		out.append("""	<th colspan="5">soft&nbsp;quota</th>""")
		out.append("""	<th colspan="4">hard&nbsp;quota</th>""")
		out.append("""	<th colspan="4">current&nbsp;values</th>""")
		out.append("""	</tr>""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="%s">time&nbsp;to&nbsp;expire</a></th>""" % (createorderlink("QU",10)))
		out.append("""		<th><a href="%s">inodes</a></th>""" % (createorderlink("QU",11)))
		out.append("""		<th><a href="%s">length</a></th>""" % (createorderlink("QU",12)))
		out.append("""		<th><a href="%s">size</a></th>""" % (createorderlink("QU",13)))
		out.append("""		<th><a href="%s">real&nbsp;size</a></th>""" % (createorderlink("QU",14)))
		out.append("""		<th><a href="%s">inodes</a></th>""" % (createorderlink("QU",21)))
		out.append("""		<th><a href="%s">length</a></th>""" % (createorderlink("QU",22)))
		out.append("""		<th><a href="%s">size</a></th>""" % (createorderlink("QU",23)))
		out.append("""		<th><a href="%s">real&nbsp;size</a></th>""" % (createorderlink("QU",24)))
		out.append("""		<th><a href="%s">inodes</a></th>""" % (createorderlink("QU",31)))
		out.append("""		<th><a href="%s">length</a></th>""" % (createorderlink("QU",32)))
		out.append("""		<th><a href="%s">size</a></th>""" % (createorderlink("QU",33)))
		out.append("""		<th><a href="%s">real&nbsp;size</a></th>""" % (createorderlink("QU",34)))
		out.append("""	</tr>""")

		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_QUOTA_INFO,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_QUOTA_INFO and length>=4 and masterversion>=(1,7,0):
			data = myrecv(s,length)
			quotas = []
			pos = 0
			while pos<length:
				inode,pleng = struct.unpack(">LL",data[pos:pos+8])
				pos+=8
				path = data[pos:pos+pleng]
				pos+=pleng
				exceeded,qflags,timetoblock = struct.unpack(">BBL",data[pos:pos+6])
				pos+=6;
				sinodes,slength,ssize,srealsize = struct.unpack(">LQQQ",data[pos:pos+28])
				pos+=28
				hinodes,hlength,hsize,hrealsize = struct.unpack(">LQQQ",data[pos:pos+28])
				pos+=28
				cinodes,clength,csize,crealsize = struct.unpack(">LQQQ",data[pos:pos+28])
				pos+=28
				if QUorder==1 or QUorder==0:
					sf = path
				elif QUorder==2:
					sf = exceeded
				elif QUorder==10:
					sf = timetoblock
				elif QUorder==11:
					sf = sinodes
				elif QUorder==12:
					sf = slength
				elif QUorder==13:
					sf = ssize
				elif QUorder==14:
					sf = srealsize
				elif QUorder==21:
					sf = hinodes
				elif QUorder==22:
					sf = hlength
				elif QUorder==23:
					sf = hsize
				elif QUorder==24:
					sf = hrealsize
				elif QUorder==31:
					sf = cinodes
				elif QUorder==32:
					sf = clength
				elif QUorder==33:
					sf = csize
				elif QUorder==34:
					sf = crealsize
				else:
					sf = 0
				quotas.append((sf,path,exceeded,qflags,timetoblock,sinodes,slength,ssize,srealsize,hinodes,hlength,hsize,hrealsize,cinodes,clength,csize,crealsize))
			quotas.sort()
			if QUrev:
				quotas.reverse()
			i = 1
			for sf,path,exceeded,qflags,timetoblock,sinodes,slength,ssize,srealsize,hinodes,hlength,hsize,hrealsize,cinodes,clength,csize,crealsize in quotas:
				out.append("""	<tr class="C%u">""" % (((i-1)%2)+1))
				out.append("""		<td align="right">%u</td>""" % i)
				out.append("""		<td align="left">%s</td>""" % path)
				if exceeded:
					out.append("""		<td align="center">yes</td>""")
				else:
					out.append("""		<td align="center">no</td>""")
				if timetoblock<0xFFFFFFFF:
					if timetoblock>0:
#						days,rest = divmod(timetoblock,86400)
#						hours,rest = divmod(rest,3600)
#						min,sec = divmod(rest,60)
#						if days>0:
#							tbstr = "%ud,&nbsp;%uh&nbsp;%um&nbsp;%us" % (days,hours,min,sec)
#						elif hours>0:
#							tbstr = "%uh&nbsp;%um&nbsp;%us" % (hours,min,sec)
#						elif min>0:
#							tbstr = "%um&nbsp;%us" % (min,sec)
#						else:
#							tbstr = "%us" % sec
						out.append("""		<td align="center"><span class="SEXCEEDED"><a style="cursor:default" title="%s">%s</a></span></td>""" % (timeduration_to_fullstr(timetoblock),timeduration_to_shortstr(timetoblock)))
					else:
						out.append("""		<td align="center"><span class="EXCEEDED">expired</span></td>""")
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&1:
					if sinodes>=cinodes:
						cl="NOTEXCEEDED"
					elif timetoblock>0:
						cl="SEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><span class="%s">%u</span></td>""" % (cl,sinodes))
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&2:
					if slength>=clength:
						cl="NOTEXCEEDED"
					elif timetoblock>0:
						cl="SEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><a style="cursor:default" title="%s B"><span class="%s">%sB</span></a></td>""" % (decimal_number(slength),cl,humanize_number(slength,"&nbsp;")))
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&4:
					if ssize>=csize:
						cl="NOTEXCEEDED"
					elif timetoblock>0:
						cl="SEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><a style="cursor:default" title="%s B"><span class="%s">%sB</span></a></td>""" % (decimal_number(ssize),cl,humanize_number(ssize,"&nbsp;")))
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&8:
					if srealsize>=crealsize:
						cl="NOTEXCEEDED"
					elif timetoblock>0:
						cl="SEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><a style="cursor:default" title="%s B"><span class="%s">%sB</span></a></td>""" % (decimal_number(srealsize),cl,humanize_number(srealsize,"&nbsp;")))
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&16:
					if hinodes>=cinodes:
						cl="NOTEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><span class="%s">%u</span></td>""" % (cl,hinodes))
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&32:
					if hlength>=clength:
						cl="NOTEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><a style="cursor:default" title="%s B"><span class="%s">%sB</span></a></td>""" % (decimal_number(hlength),cl,humanize_number(hlength,"&nbsp;")))
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&64:
					if hsize>=csize:
						cl="NOTEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><a style="cursor:default" title="%s B"><span class="%s">%sB</span></a></td>""" % (decimal_number(hsize),cl,humanize_number(hsize,"&nbsp;")))
				else:
					out.append("""		<td align="center">-</td>""")
				if qflags&128:
					if hrealsize>=crealsize:
						cl="NOTEXCEEDED"
					else:
						cl="EXCEEDED"
					out.append("""		<td align="right"><a style="cursor:default" title="%s B"><span class="%s">%sB</span></a></td>""" % (decimal_number(hrealsize),cl,humanize_number(hrealsize,"&nbsp;")))
				else:
					out.append("""		<td align="center">-</td>""")
				out.append("""		<td align="right">%u</td>""" % cinodes)
				out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(clength),humanize_number(clength,"&nbsp;")))
				out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(csize),humanize_number(csize,"&nbsp;")))
				out.append("""		<td align="right"><a style="cursor:default" title="%s B">%sB</a></td>""" % (decimal_number(crealsize),humanize_number(crealsize,"&nbsp;")))
				out.append("""	</tr>""")
				i+=1
		out.append("""</table>""")
		s.close()
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "MC" in sectionset:
	out = []

	try:
		charts = (
			(100,'cpu','cpu usage (percent)'),
			(20,'memory','memory usage (if available)'),
			(2,'dels','chunk deletions (per minute)'),
			(3,'repl','chunk replications (per minute)'),
			(4,'stafs','statfs operations (per minute)'),
			(5,'getattr','getattr operations (per minute)'),
			(6,'setattr','setattr operations (per minute)'),
			(7,'lookup','lookup operations (per minute)'),
			(8,'mkdir','mkdir operations (per minute)'),
			(9,'rmdir','rmdir operations (per minute)'),
			(10,'symlink','symlink operations (per minute)'),
			(11,'readlink','readlink operations (per minute)'),
			(12,'mknod','mknod operations (per minute)'),
			(13,'unlink','unlink operations (per minute)'),
			(14,'rename','rename operations (per minute)'),
			(15,'link','link operations (per minute)'),
			(16,'readdir','readdir operations (per minute)'),
			(17,'open','open operations (per minute)'),
			(18,'read','read operations (per minute)'),
			(19,'write','write operations (per minute)'),
			(21,'prcvd','packets received (per second)'),
			(22,'psent','packets sent (per second)'),
			(23,'brcvd','bits received (per second)'),
			(24,'bsent','bits sent (per second)')
		)

		out.append("""<script type="text/javascript">""")
		out.append("""<!--//--><![CDATA[//><!--""")
		out.append("""	var i,j;""")
		out.append("""	var ma_chartid = new Array(0,0);""")
		out.append("""	var ma_range=0;""")
		out.append("""	var ma_imgs = new Array();""")
		out.append("""	var ma_vids = new Array%s;""" % str(tuple([ x[0] for x in charts ])))
		out.append("""	var ma_inames = new Array%s;""" % str(tuple([ x[1] for x in charts ])))
		out.append("""	var ma_idesc = new Array%s;""" % str(tuple([ x[2] for x in charts ])))
		out.append("""	for (i=0 ; i<ma_vids.length ; i++) {""")
		out.append("""		for (j=0 ; j<4 ; j++) {""")
		out.append("""			var vid = ma_vids[i];""")
		out.append("""			var id = vid*10+j;""")
		out.append("""			ma_imgs[id] = new Image();""")
		out.append("""			ma_imgs[id].src = "chart.cgi?host=%s&amp;port=%u&amp;id="+id;""" % (urlescape(masterhost),masterport))
		out.append("""		}""")
		out.append("""	}""")
		out.append("""	function ma_change(num) {""")
		out.append("""		for (i=0 ; i<ma_inames.length ; i++) {""")
		out.append("""			var name = "ma_"+ma_inames[i];""")
		out.append("""			var vid = ma_vids[i];""")
		out.append("""			var id = vid*10+num;""")
		out.append("""			document.images[name].src = ma_imgs[id].src;""")
		out.append("""		}""")
		out.append("""	}""")
		out.append("""	function ma_cmp_refresh() {""")
		out.append("""		var vid,id,iname;""")
		out.append("""		for (i=0 ; i<2 ; i++) {""")
		out.append("""			vid = ma_vids[ma_chartid[i]];""")
		out.append("""			id = vid*10+ma_range;""")
		out.append("""			iname = "ma_chart"+i;""")
		out.append("""			document.images[iname].src = ma_imgs[id].src;""")
		out.append("""		}""")
		out.append("""	}""")
		out.append("""	function ma_change_range(no) {""")
		out.append("""		ma_range = no;""")
		out.append("""		ma_cmp_refresh();""")
		out.append("""	}""")
		out.append("""	function ma_change_type(id,no) {""")
		out.append("""		var o;""")
		out.append("""		o = document.getElementById("ma_cell_"+id+"_"+ma_chartid[id]);""")
		out.append("""		o.className="REL";""")
		out.append("""		ma_chartid[id]=no;""")
		out.append("""		o = document.getElementById("ma_cell_"+id+"_"+ma_chartid[id]);""")
		out.append("""		o.className="PR";""")
		out.append("""		o = document.getElementById("ma_desc"+id);""")
		out.append("""		o.innerHTML = ma_idesc[no];""")
		out.append("""		ma_cmp_refresh();""")
		out.append("""	}""")
		out.append("""//--><!]]>""")
		out.append("""</script>""")
		out.append("""<table class="FR" cellspacing="0">""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="javascript:ma_change(0);">short range</a></th>""")
		out.append("""		<th><a href="javascript:ma_change(1);">medium range</a></th>""")
		out.append("""		<th><a href="javascript:ma_change(2);">long range</a></th>""")
		out.append("""		<th><a href="javascript:ma_change(3);">very long range</a></th>""")
		out.append("""	</tr>""")
		for id,name,desc in charts:
			out.append("""	<tr class="C2">""")
			out.append("""		<td align="center" colspan="4">""")
			out.append("""			%s:<br/>""" % (desc))
			out.append("""			<img src="chart.cgi?host=%s&amp;port=%u&amp;id=%u" width="1000" height="120" id="ma_%s" alt="%s" />""" % (urlescape(masterhost),masterport,id*10,name,name))
			out.append("""		</td>""")
			out.append("""	</tr>""")
		out.append("""</table>""")
		out.append("""<br/>""")

		out.append("""<table class="FR" cellspacing="0">""")
		out.append("""	<tr>""")
		out.append("""		<th><a href="javascript:ma_change_range(0);">short range</a></th>""")
		out.append("""		<th><a href="javascript:ma_change_range(1);">medium range</a></th>""")
		out.append("""		<th><a href="javascript:ma_change_range(2);">long range</a></th>""")
		out.append("""		<th><a href="javascript:ma_change_range(3);">very long range</a></th>""")
		out.append("""	</tr>""")
		out.append("""</table>""")
		out.append("""<table class="FR" cellspacing="0">""")
		for i in xrange(2):
			out.append("""	<tr>""")
			out.append("""		<td align="center" colspan="4">""")
			out.append("""			<div id="ma_desc%u">%s</div>""" % (i,charts[0][2]))
			out.append("""			<img src="chart.cgi?host=%s&amp;port=%u&amp;id=%u" width="1000" height="120" id="ma_chart%u" alt="chart" />""" % (urlescape(masterhost),masterport,10*charts[0][0],i))
			out.append("""			<table class="BOTMENU" cellspacing="0">""")
			out.append("""				<tr>""")
			no=0
			cl="PR"
			for id,name,desc in charts:
				out.append("""					<td align="center" id="ma_cell_%u_%u" class="%s"><a href="javascript:ma_change_type(%u,%u);" title="%s">%s</a></td>""" % (i,no,cl,i,no,desc,name))
				cl="REL"
				no+=1
			out.append("""				</tr>""")
			out.append("""			</table>""")
			out.append("""		</td>""")
			out.append("""	</tr>""")
		out.append("""</table>""")
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

if "CC" in sectionset:
	out = []

	try:
		if fields.has_key("CCdata"):
			CCdata = fields.getvalue("CCdata")
		else:
			CCdata = ""
	except Exception:
		CCdata = ""

	try:
		# get cs list
		hostlist = []
		s = socket.socket()
		s.connect((masterhost,masterport))
		mysend(s,struct.pack(">LL",CLTOMA_CSERV_LIST,0))
		header = myrecv(s,8)
		cmd,length = struct.unpack(">LL",header)
		if cmd==MATOCL_CSERV_LIST and (length%54)==0:
			data = myrecv(s,length)
			n = length/54
			for i in xrange(n):
				d = data[i*54:(i+1)*54]
				v1,v2,v3,ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">HBBBBBBHQQLQQLL",d)
				hostlist.append((ip1,ip2,ip3,ip4,port))
		elif cmd==MATOCL_CSERV_LIST and (length%50)==0:
			data = myrecv(s,length)
			n = length/50
			for i in xrange(n):
				d = data[i*50:(i+1)*50]
				ip1,ip2,ip3,ip4,port,used,total,chunks,tdused,tdtotal,tdchunks,errcnt = struct.unpack(">BBBBHQQLQQLL",d)
				hostlist.append((ip1,ip2,ip3,ip4,port))
		s.close()

		charts = (
			(100,'cpu','cpu usage (percent)'),
			(101,'datain','traffic from clients and other chunkservers (bits/s)'),
			(102,'dataout','traffic to clients and other chunkservers (bits/s)'),
			(103,'bytesr','bytes read - data/other (bytes/s)'),
			(104,'bytesw','bytes written - data/other (bytes/s)'),
			(2,'masterin','traffic from master (bits/s)'),
			(3,'masterout','traffic to master (bits/s)'),
			(105,'hddopr','number of low-level read operations per minute'),
			(106,'hddopw','number of low-level write operations per minute'),
			(16,'hlopr','number of high-level read operations per minute'),
			(17,'hlopw','number of high-level write operations per minute'),
			(18,'rtime','time of data read operations'),
			(19,'wtime','time of data write operations'),
			(20,'repl','number of chunk replications per minute'),
			(21,'create','number of chunk creations per minute'),
			(22,'delete','number of chunk deletions per minute'),
		)
		servers = []

		if len(hostlist)>0:
			hostlist.sort()
			out.append("""<form action=""><table class="FR" cellspacing="0"><tr><th>Select: <select name="server" size="1" onchange="document.location.href='%s&amp;CCdata='+this.options[this.selectedIndex].value">""" % createlink({"CCdata":""}))
			entrystr = []
			entrydesc = {}
			for id,oname,desc in charts:
				name = oname.replace(":","")
				entrystr.append(name)
				entrydesc[name] = desc
			for ip1,ip2,ip3,ip4,port in hostlist:
				strip = "%u.%u.%u.%u" % (ip1,ip2,ip3,ip4)
				name = "%s:%u" % (strip,port)
				try:
					host = " / "+(socket.gethostbyaddr(strip))[0]
				except Exception:
					host = ""
				entrystr.append(name)
				entrydesc[name] = "Server: %s%s" % (name,host)
				servers.append((strip,port,name.replace(".","_").replace(":","_"),entrydesc[name]))
			if CCdata not in entrystr:
				out.append("""<option value="" selected="selected"> data type or server</option>""")
			for estr in entrystr:
				if estr==CCdata:
					out.append("""<option value="%s" selected="selected">%s</option>""" % (estr,entrydesc[estr]))
				else:
					out.append("""<option value="%s">%s</option>""" % (estr,entrydesc[estr]))
			out.append("""</select></th></tr></table></form><br/>""")

		cchtmp = CCdata.split(":")
		if len(cchtmp)==2:
			cshost = cchtmp[0]
			csport = cchtmp[1]

			out.append("""<script type="text/javascript">""")
			out.append("""<!--//--><![CDATA[//><!--""")
			out.append("""	var i,j;""")
			out.append("""	var cs_chartid = new Array(0,0);""")
			out.append("""	var cs_range=0;""")
			out.append("""	var cs_imgs = new Array();""")
			out.append("""	var cs_vids = new Array%s;""" % str(tuple([ x[0] for x in charts ])))
			out.append("""	var cs_inames = new Array%s;""" % str(tuple([ x[1] for x in charts ])))
			out.append("""	var cs_idesc = new Array%s;""" % str(tuple([ x[2] for x in charts ])))
			out.append("""	for (i=0 ; i<cs_vids.length ; i++) {""")
			out.append("""		for (j=0 ; j<4 ; j++) {""")
			out.append("""			var vid = cs_vids[i];""")
			out.append("""			var id = vid*10+j;""")
			out.append("""			cs_imgs[id] = new Image();""")
			out.append("""			cs_imgs[id].src = "chart.cgi?host=%s&amp;port=%s&amp;id="+id;""" % (cshost,csport))
			out.append("""		}""")
			out.append("""	}""")
			out.append("""	function cs_change(num) {""")
			out.append("""		for (i=0 ; i<cs_inames.length ; i++) {""")
			out.append("""			var name = "cs_"+cs_inames[i];""")
			out.append("""			var vid = cs_vids[i];""")
			out.append("""			var id = vid*10+num;""")
			out.append("""			document.images[name].src = cs_imgs[id].src;""")
			out.append("""		}""")
			out.append("""	}""")
			out.append("""	function cs_cmp_refresh() {""")
			out.append("""		var vid,id,iname;""")
			out.append("""		for (i=0 ; i<2 ; i++) {""")
			out.append("""			vid = cs_vids[cs_chartid[i]];""")
			out.append("""			id = vid*10+cs_range;""")
			out.append("""			iname = "cs_chart"+i;""")
			out.append("""			document.images[iname].src = cs_imgs[id].src;""")
			out.append("""		}""")
			out.append("""	}""")
			out.append("""	function cs_change_range(no) {""")
			out.append("""		cs_range = no;""")
			out.append("""		cs_cmp_refresh();""")
			out.append("""	}""")
			out.append("""	function cs_change_type(id,no) {""")
			out.append("""		var o;""")
			out.append("""		o = document.getElementById("cs_cell_"+id+"_"+cs_chartid[id]);""")
			out.append("""		o.className="REL";""")
			out.append("""		cs_chartid[id]=no;""")
			out.append("""		o = document.getElementById("cs_cell_"+id+"_"+cs_chartid[id]);""")
			out.append("""		o.className="PR";""")
			out.append("""		o = document.getElementById("cs_desc"+id);""")
			out.append("""		o.innerHTML = cs_idesc[no];""")
			out.append("""		cs_cmp_refresh();""")
			out.append("""	}""")
			out.append("""//--><!]]>""")
			out.append("""</script>""")
			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr>""")
			out.append("""		<th><a href="javascript:cs_change(0);">short range</a></th>""")
			out.append("""		<th><a href="javascript:cs_change(1);">medium range</a></th>""")
			out.append("""		<th><a href="javascript:cs_change(2);">long range</a></th>""")
			out.append("""		<th><a href="javascript:cs_change(3);">very long range</a></th>""")
			out.append("""	</tr>""")
			for id,name,desc in charts:
				out.append("""	<tr class="C2">""")
				out.append("""		<td align="center" colspan="4">""")
				out.append("""			%s:<br/>""" % (desc))
				out.append("""			<img src="chart.cgi?host=%s&amp;port=%s&amp;id=%u" width="1000" height="120" id="cs_%s" alt="%s" />""" % (cshost,csport,id*10,name,name))
				out.append("""		</td>""")
				out.append("""	</tr>""")
			out.append("""</table>""")
			out.append("""<br/>""")

			out.append("""<table class="FR" cellspacing="0">""")
			out.append("""	<tr>""")
			out.append("""		<th><a href="javascript:cs_change_range(0);">short range</a></th>""")
			out.append("""		<th><a href="javascript:cs_change_range(1);">medium range</a></th>""")
			out.append("""		<th><a href="javascript:cs_change_range(2);">long range</a></th>""")
			out.append("""		<th><a href="javascript:cs_change_range(3);">very long range</a></th>""")
			out.append("""	</tr>""")
			out.append("""</table>""")
			out.append("""<table class="FR" cellspacing="0">""")
			for i in xrange(2):
				out.append("""	<tr>""")
				out.append("""		<td align="center" colspan="4">""")
				out.append("""			<div id="cs_desc%u">%s</div>""" % (i,charts[0][2]))
				out.append("""			<img src="chart.cgi?host=%s&amp;port=%s&amp;id=%u" width="1000" height="120" id="cs_chart%u" alt="chart" />""" % (cshost,csport,10*charts[0][0],i))
				out.append("""			<table class="BOTMENU" cellspacing="0">""")
				out.append("""				<tr>""")
				no=0
				cl="PR"
				for id,name,desc in charts:
					out.append("""					<td align="center" id="cs_cell_%u_%u" class="%s"><a href="javascript:cs_change_type(%u,%u);" title="%s">%s</a></td>""" % (i,no,cl,i,no,desc,name))
					cl="REL"
					no+=1
				out.append("""				</tr>""")
				out.append("""			</table>""")
				out.append("""		</td>""")
				out.append("""	</tr>""")
			out.append("""</table>""")
		elif len(cchtmp)==1 and len(CCdata)>0:
			chid = 0
			for id,name,desc in charts:
				if name==CCdata:
					chid = id
			if chid==0:
				try:
					chid = int(CCdata)
				except Exception:
					pass
			if chid>0 and chid<1000:
				out.append("""<script type="text/javascript">""")
				out.append("""<!--//--><![CDATA[//><!--""")
				out.append("""	var i,j;""")
				out.append("""	var cs_chartid = new Array(0,0);""")
				out.append("""	var cs_range=0;""")
				out.append("""	var cs_imgs = new Array();""")
				out.append("""	var cs_vhosts = new Array%s;""" % str(tuple([ x[0] for x in servers ])))
				out.append("""	var cs_vports = new Array%s;""" % str(tuple([ x[1] for x in servers ])))
				out.append("""	var cs_inames = new Array%s;""" % str(tuple([ x[2] for x in servers ])))
				out.append("""	for (i=0 ; i<cs_inames.length ; i++) {""")
				out.append("""		for (j=0 ; j<4 ; j++) {""")
				out.append("""			var vhost = cs_vhosts[i];""")
				out.append("""			var vport = cs_vports[i];""")
				out.append("""			var id = %d*10+j;""" % chid)
				out.append("""			cs_imgs[i*10+j] = new Image();""")
				out.append("""			cs_imgs[i*10+j].src = "chart.cgi?host="+vhost+"&amp;port="+vport+"&amp;id="+id;""")
				out.append("""		}""")
				out.append("""	}""")
				out.append("""	function cs_change(num) {""")
				out.append("""		for (i=0 ; i<cs_inames.length ; i++) {""")
				out.append("""			var name = "cs_"+cs_inames[i];""")
				out.append("""			document.images[name].src = cs_imgs[i*10+num].src;""")
				out.append("""		}""")
				out.append("""	}""")
				out.append("""//--><!]]>""")
				out.append("""</script>""")
				out.append("""<table class="FR" cellspacing="0">""")
				out.append("""	<tr>""")
				out.append("""		<th><a href="javascript:cs_change(0);">short range</a></th>""")
				out.append("""		<th><a href="javascript:cs_change(1);">medium range</a></th>""")
				out.append("""		<th><a href="javascript:cs_change(2);">long range</a></th>""")
				out.append("""		<th><a href="javascript:cs_change(3);">very long range</a></th>""")
				out.append("""	</tr>""")
				for cshost,csport,name,desc in servers:
					out.append("""	<tr class="C2">""")
					out.append("""		<td align="center" colspan="4">""")
					out.append("""			%s:<br/>""" % (desc))
					out.append("""			<img src="chart.cgi?host=%s&amp;port=%s&amp;id=%u" width="1000" height="120" id="cs_%s" alt="%s" />""" % (cshost,csport,chid*10,name,name))
					out.append("""		</td>""")
					out.append("""	</tr>""")
				out.append("""</table>""")
		print "\n".join(out)
	except Exception:
		print """<table class="FR" cellspacing="0">"""
		print """<tr><td align="left"><pre>"""
		traceback.print_exc(file=sys.stdout)
		print """</pre></td></tr>"""
		print """</table>"""

	print """<br/>"""

print """</div> <!-- end of container -->"""

print """</body>"""
print """</html>"""
