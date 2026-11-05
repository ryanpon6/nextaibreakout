"""Pre-deploy gate: fail if CJK text appears in the built homepage."""
import re, sys
h = open(sys.argv[1] if len(sys.argv) > 1 else "dist/index.html", encoding="utf-8").read()
m = re.findall(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+", h)
if m: print("CJK FOUND:", m[:10]); sys.exit(4)
print("cjkcheck OK")
