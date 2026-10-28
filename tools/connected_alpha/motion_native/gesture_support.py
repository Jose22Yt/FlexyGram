"""Copy primitive production continuation fields into explicit probes; only test visibility changes."""
def fields(source):
 start='    private boolean instantGesturePending, instantGestureActive;'
 if start not in source:return ''
 a=source.index(start);b=source.index('    private void clearInstantGesture()',a)
 return source[a:b].replace('private ','')
