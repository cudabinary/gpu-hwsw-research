"""Small owned CPU fixture; no GPU/library/telemetry import."""
import sys,time
if sys.argv[1]=='fail':raise SystemExit(7)
if sys.argv[1]=='hang':time.sleep(10)
else:time.sleep(.02)
