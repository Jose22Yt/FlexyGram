"""Explicit runtime suite: not discovered by the static gate and never skipped.
Host run checks host source libraries/fixtures ONLY. Android lab must run this
inside the experimental Chaquopy interpreter; record actual library paths.
No account, network input, untrusted XML or plugin is used.
"""
from pathlib import Path
import argparse,ctypes,gzip,io,json,lzma,os,sys,tempfile,unittest

def deny_network(event,args):
 if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo','socket.bind'):
  raise RuntimeError('OFFLINE_NATIVE_LAB_NETWORK_DENIED')
sys.addaudithook(deny_network)
LIBDIR=None;FTLIB=None;FONT=None
class NativeRuntimeCases(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from lxml import etree
  from PIL import Image,ImageFont
  cls.etree=etree;cls.Image=Image;cls.ImageFont=ImageFont
  cls.xml=ctypes.CDLL(str(LIBDIR/'libxml2.so'),mode=ctypes.RTLD_GLOBAL)
  cls.xslt=ctypes.CDLL(str(LIBDIR/'libxslt.so'),mode=ctypes.RTLD_GLOBAL)
  cls.exslt=ctypes.CDLL(str(LIBDIR/'libexslt.so'),mode=ctypes.RTLD_GLOBAL)
  cls.ft=ctypes.CDLL(str(FTLIB))
  def bind(lib,name,args,result):
   f=getattr(lib,name);f.argtypes=args;f.restype=result;return f
  P=ctypes.c_void_p;S=ctypes.c_char_p;I=ctypes.c_int
  bind(cls.xml,'xmlReadMemory',[S,I,S,S,I],P);bind(cls.xml,'xmlReadFile',[S,S,I],P)
  bind(cls.xml,'xmlFreeDoc',[P],None);bind(cls.xml,'xmlDocDumpMemory',[P,ctypes.POINTER(P),ctypes.POINTER(I)],None)
  bind(cls.xml,'xmlHasFeature',[I],I)
  bind(cls.xslt,'xsltParseStylesheetDoc',[P],P);bind(cls.xslt,'xsltApplyStylesheet',[P,P,P],P)
  bind(cls.xslt,'xsltSaveResultToString',[ctypes.POINTER(P),ctypes.POINTER(I),P,P],I)
  bind(cls.xslt,'xsltFreeStylesheet',[P],None);bind(cls.exslt,'exsltRegisterAll',[],None)
  cls.free=ctypes.CFUNCTYPE(None,P)(P.in_dll(cls.xml,'xmlFree').value)
  bind(cls.ft,'FT_Init_FreeType',[ctypes.POINTER(P)],I);bind(cls.ft,'FT_Done_FreeType',[P],I)
  bind(cls.ft,'FT_New_Face',[P,S,ctypes.c_long,ctypes.POINTER(P)],I)
  bind(cls.ft,'FT_Done_Face',[P],I);bind(cls.ft,'FT_Set_Pixel_Sizes',[P,ctypes.c_uint,ctypes.c_uint],I)
  bind(cls.ft,'FT_Load_Char',[P,ctypes.c_ulong,ctypes.c_int],I)
 def xml_parse(self,data):
  p=self.xml.xmlReadMemory(data,len(data),b'offline-synthetic.xml',b'UTF-8',2048)
  self.assertTrue(p);return p
 def xml_dump(self,p):
  out=ctypes.c_void_p();n=ctypes.c_int();self.xml.xmlDocDumpMemory(p,ctypes.byref(out),ctypes.byref(n))
  try:return ctypes.string_at(out,n.value)
  finally:self.free(out)
 def test_xml_unicode_and_entities_native(self):
  p=self.xml_parse('<root>Español 日本語 😀 &amp; &#233;</root>'.encode())
  try:self.assertIn('日本語'.encode(),self.xml_dump(p))
  finally:self.xml.xmlFreeDoc(p)
 def test_xml_malformed_is_rejected_native(self):
  # Suppress parser diagnostics with XML_PARSE_NOERROR|NOWARNING, never text logs.
  self.assertFalse(self.xml.xmlReadMemory(b'<root>',6,b'offline.xml',None,2048|32|64))
 def test_xml_zlib_and_lzma_features_native(self):
  # xmlFeature enum from the pinned public parser.h: ZLIB=31,LZMA=33.
  self.assertEqual(self.xml.xmlHasFeature(31),1);self.assertEqual(self.xml.xmlHasFeature(33),1)
 def test_xml_gzip_file_native(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'synthetic.xml.gz';p.write_bytes(gzip.compress(b'<root>LOCAL</root>'))
   doc=self.xml.xmlReadFile(os.fsencode(p),None,2048);self.assertTrue(doc)
   try:self.assertIn(b'LOCAL',self.xml_dump(doc))
   finally:self.xml.xmlFreeDoc(doc)
 def test_xml_xz_file_native(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'synthetic.xml.xz';p.write_bytes(lzma.compress(b'<root>LOCAL_XZ</root>'))
   doc=self.xml.xmlReadFile(os.fsencode(p),None,2048);self.assertTrue(doc)
   try:self.assertIn(b'LOCAL_XZ',self.xml_dump(doc))
   finally:self.xml.xmlFreeDoc(doc)
 def transform(self,template):
  style=self.xml_parse(template);sheet=self.xslt.xsltParseStylesheetDoc(style);self.assertTrue(sheet)
  doc=self.xml_parse(b'<root><value>3</value></root>');result=None;out=ctypes.c_void_p();n=ctypes.c_int()
  try:
   result=self.xslt.xsltApplyStylesheet(sheet,doc,None);self.assertTrue(result)
   self.assertEqual(self.xslt.xsltSaveResultToString(ctypes.byref(out),ctypes.byref(n),result,sheet),0)
   return ctypes.string_at(out,n.value)
  finally:
   if out:self.free(out)
   if result:self.xml.xmlFreeDoc(result)
   self.xml.xmlFreeDoc(doc);self.xslt.xsltFreeStylesheet(sheet)
 def test_xslt_native_transform(self):
  text=b'<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"><xsl:template match="/"><out><xsl:value-of select="root/value * 2"/></out></xsl:template></xsl:stylesheet>'
  self.assertIn(b'<out>6</out>',self.transform(text))
 def test_exslt_native_math(self):
  self.exslt.exsltRegisterAll()
  text=b'<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:math="http://exslt.org/math"><xsl:template match="/"><out><xsl:value-of select="math:sqrt(9)"/></out></xsl:template></xsl:stylesheet>'
  self.assertIn(b'>3</out>',self.transform(text))
 def test_freetype_native_font_load_and_render(self):
  lib=ctypes.c_void_p();face=ctypes.c_void_p();self.assertEqual(self.ft.FT_Init_FreeType(ctypes.byref(lib)),0)
  try:
   self.assertEqual(self.ft.FT_New_Face(lib,os.fsencode(FONT),0,ctypes.byref(face)),0)
   self.assertEqual(self.ft.FT_Set_Pixel_Sizes(face,0,24),0)
   for c in 'Agé':self.assertEqual(self.ft.FT_Load_Char(face,ord(c),4),0)
  finally:
   if face:self.ft.FT_Done_Face(face)
   self.ft.FT_Done_FreeType(lib)
 def test_pillow_png_rgba_roundtrip(self):
  image=self.Image.new('RGBA',(17,19),(3,45,67,128));buffer=io.BytesIO();image.save(buffer,format='PNG');buffer.seek(0)
  with self.Image.open(buffer) as decoded:self.assertEqual(decoded.getpixel((0,0)),(3,45,67,128));self.assertEqual(decoded.size,(17,19))
 def test_pillow_jpeg_roundtrip(self):
  buffer=io.BytesIO();self.Image.new('RGB',(16,16),(120,130,140)).save(buffer,format='JPEG');buffer.seek(0)
  with self.Image.open(buffer) as image:image.load();self.assertEqual(image.size,(16,16))
 def test_pillow_font_unicode(self):
  font=self.ImageFont.truetype(str(FONT),24);self.assertGreater(font.getlength('FlexyGram é 😀'),0)
 def test_lxml_xpath_xslt_and_html(self):
  e=self.etree;parser=e.XMLParser(no_network=True,resolve_entities=False);root=e.fromstring(b'<r><v>2</v></r>',parser)
  self.assertEqual(root.xpath('sum(v)'),2.0)
  style=e.XML(b'<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"><xsl:template match="/"><ok/></xsl:template></xsl:stylesheet>')
  transform=e.XSLT(style,access_control=e.XSLTAccessControl.DENY_ALL);self.assertIn('<ok/>',str(transform(root)))
  self.assertIsNotNone(e.HTML('<html><body>LOCAL &amp; test</body></html>'))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['libdir','freetype','font']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();LIBDIR=a.libdir.resolve();FTLIB=a.freetype.resolve();FONT=a.font.resolve()
 print(json.dumps({'platform':sys.platform,'python':sys.version,'libdir':str(LIBDIR),'freetype':str(FTLIB),'font':str(FONT),'network':'Python audit hook denies socket operations; application INTERNET must also be absent'}))
 unittest.main(argv=[sys.argv[0]],verbosity=2)
