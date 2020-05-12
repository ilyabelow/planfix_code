#!/usr/bin/python3

import io, cgi, cgitb, sys,html

cgitb.enable()

if hasattr(sys.stdout, "buffer"):
  def bwrite(s):
    sys.stdout.flush()
    sys.stdout.buffer.write(s)
  write = sys.stdout.write
else:
  wrapper = io.TextIOWrapper(sys.stdout)
  def bwrite(s):
    wrapper.flush()
    sys.stdout.write(s)
  write = wrapper.write

write("Content-type: text/html;charset=utf-8\r\n\r\n")

bwrite("""<!DOCTYPE html>

<html>
<head>

  <title>Logs</title>
</head>
<body>

<a href=#end>Вниз</a>
""".encode())

f = open('log','rt',encoding='utf-8')
for line in f:
  line = html.escape(line)
  if len(line) == 31:
    bwrite('<hr/>'.encode())
    line = line[:22] + '<u>' + line[22:] + '</u>'

  if line.find('==========') != -1:
    line = line[:33] + '<b>' + line[33:] + '</b>'
  l = line + '<br/>'
  bwrite(l.encode())

bwrite("""
<a id=end></a>
</body>
</html>""".encode())