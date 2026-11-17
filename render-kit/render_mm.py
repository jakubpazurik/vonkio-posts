#!/usr/bin/env python3
"""VONKIO – renderer rubriky „Objav Slovensko / Mimo mesta“. Použitie: python3 render_mm.py spec.json OUT_DIR [jpg|png]"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = dict(c1="#C98B5A", c2="#F3C892", c3="#F86E30", bg1="#2A1A0E", bg2="#160E07", bg3="#0A0603",
         text="#FFF4E8", muted="#D4B79A", sk="MM")
KRAJ_C = {"BA": "#4C8DFF", "TT": "#FF5C8A", "TN": "#FFC83D", "NR": "#B5E03A", "ZA": "#1FD1C1",
          "BB": "#2ECC71", "PO": "#FF4D4D", "KE": "#9D7BFF"}


def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgba(h, a):
    r, g, b = hex2rgb(h); return f"rgba({r},{g},{b},{a})"

def T(s):
    s = html.escape(str(s or ""))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("\n", "<br>")


def head(A):
    p = P
    ff = "".join(
        f"@font-face{{font-family:'{f['family']}';font-weight:{f['weight']};font-style:normal;"
        f"src:url(data:font/ttf;base64,{f['ttf']}) format('truetype');}}" for f in A["fonts"])
    return f"""<!doctype html><html lang="sk"><head><meta charset="utf-8"><style>{ff}
html,body{{margin:0;background:{p['bg3']}}}
*{{box-sizing:border-box}}
.vmask{{-webkit-mask:url(data:image/png;base64,{A['vsymbol_png']}) center/contain no-repeat;mask:url(data:image/png;base64,{A['vsymbol_png']}) center/contain no-repeat}}
.lmask{{-webkit-mask:url(data:image/png;base64,{A['logo_png']}) left center/contain no-repeat;mask:url(data:image/png;base64,{A['logo_png']}) left center/contain no-repeat}}
.gt{{background:linear-gradient(90deg,{p['c2']} 0%,{p['c1']} 60%,{p['c3']} 100%);-webkit-background-clip:text;background-clip:text;color:transparent}}
.fitw{{white-space:nowrap}}
.fitw.gt{{padding-top:.2em;margin-top:-.2em;padding-bottom:.04em;margin-bottom:-.04em}}
</style></head><body>"""

FOOT = """<script>
function fitW(el){let fs=parseFloat(getComputedStyle(el).fontSize);const max=el.parentElement.clientWidth;let n=0;
 while(el.scrollWidth>max&&fs>20&&n<200){fs-=2;el.style.fontSize=fs+'px';n++}}
window.__fit=async function(){await document.fonts.ready;
 document.querySelectorAll('[data-fitw]').forEach(el=>{el.style.display='inline-block';fitW(el)});
 const L=document.querySelector('[data-list]');
 if(L){let k=0;while(L.scrollHeight>L.clientHeight+1&&k<40){k++;
   L.querySelectorAll('.nm').forEach(e=>e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)-1.5)+'px');
   L.querySelectorAll('.sb').forEach(e=>e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)-0.8)+'px');
   L.querySelectorAll('.rw').forEach(e=>{const p=parseFloat(getComputedStyle(e).paddingTop);if(p>6){e.style.paddingTop=e.style.paddingBottom=(p-1.5)+'px'}});}}
 return true};
</script></body></html>"""


def frame(inner, extra=""):
    p = P
    return (f"<div id=\"slide\" style=\"width:1080px;height:1350px;position:relative;overflow:hidden;"
            f"background:linear-gradient(165deg,{p['bg1']} 0%,{p['bg2']} 45%,{p['bg3']} 100%);"
            f"color:{p['text']};font-family:'Manrope',sans-serif;{extra}\">{inner}</div>")

def vbig(style, op):
    p = P
    return (f"<div class=\"vmask\" aria-hidden=\"true\" style=\"position:absolute;{style};opacity:{op};"
            f"background:linear-gradient(135deg,{p['c2']} 0%,{p['c1']} 55%,{p['c3']} 100%)\"></div>")

def logo(w, h):
    p = P
    return (f"<div class=\"lmask\" role=\"img\" aria-label=\"VONKIO\" style=\"width:{w}px;height:{h}px;"
            f"background:linear-gradient(90deg,{p['c2']} 0%,{p['c1']} 50%,{p['c3']} 100%)\"></div>")

def label():
    return (f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:26px;letter-spacing:6px;"
            f"color:{P['muted']}\">OBJAV SLOVENSKO</div>")


def s_hook(spec):
    p = P
    lines = ""
    for txt, acc in spec["hook"]:
        if acc:
            lines += (f"<div style=\"align-self:flex-start;max-width:100%\"><div data-fitw class=\"fitw gt\" style=\"font-family:'Anton',sans-serif;"
                      f"font-size:196px;line-height:0.9;text-transform:uppercase\">{T(txt)}</div></div>")
        else:
            lines += (f"<div style=\"max-width:100%\"><div data-fitw class=\"fitw\" style=\"font-family:'Anton',sans-serif;font-size:150px;"
                      f"line-height:0.95;text-transform:uppercase\">{T(txt)}</div></div>")
    n = sum(len(c["rows"]) for c in spec["cats"] if c["rows"])
    kraje = sorted({r["kraj"] for c in spec["cats"] for r in c["rows"]})
    chips = "".join(f"<div style=\"padding:6px 14px;border-radius:999px;border:2px solid {KRAJ_C[k]};color:{KRAJ_C[k]};"
                    f"font-weight:800;font-size:22px;letter-spacing:2px\">{k}</div>" for k in kraje)
    sticker = (f"<div style=\"position:absolute;right:70px;top:820px;transform:rotate(8deg);width:250px;height:250px;border-radius:50%;"
               f"background:linear-gradient(135deg,{p['c2']},{p['c1']});color:{p['bg3']};display:flex;flex-direction:column;"
               f"align-items:center;justify-content:center;text-align:center\">"
               f"<div style=\"font-family:'Anton',sans-serif;font-size:110px;line-height:0.9\">{n}</div>"
               f"<div style=\"font-weight:800;font-size:28px;line-height:1.1\">tipov<br>mimo miest</div></div>")
    inner = (vbig("width:1400px;height:1400px;left:-380px;top:-260px;transform:rotate(180deg)", 0.5) +
        f"<div style=\"position:absolute;left:80px;top:80px;right:80px;display:flex;justify-content:space-between;align-items:center\">"
        f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:28px;letter-spacing:8px\">OBJAV SLOVENSKO · {T(spec['dates'])}</div>"
        f"<div style=\"width:18px;height:18px;border-radius:50%;background:{p['c2']}\"></div></div>"
        f"<div style=\"position:absolute;left:72px;right:72px;top:290px;display:flex;flex-direction:column\">{lines}</div>"
        + sticker +
        f"<div style=\"position:absolute;left:80px;top:1070px;display:flex;gap:12px;flex-wrap:wrap;max-width:640px\">{chips}</div>"
        f"<div style=\"position:absolute;left:80px;bottom:70px;right:80px;display:flex;justify-content:space-between;align-items:center\">"
        + logo(380, 120) +
        f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:26px;letter-spacing:6px;color:{p['muted']}\">SWIPNI</div></div>")
    return frame(inner)


def s_cat(cat, page, total):
    p = P
    line = rgba(p["text"], 0.18)
    sec = "#E6D2BE"
    hdr = (f"<div style=\"display:grid;grid-template-columns:200px minmax(0,1fr) 96px;gap:22px;padding-bottom:10px;"
           f"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:22px;letter-spacing:4px;color:{p['muted']}\">"
           f"<div>KEDY</div><div>AKCIA · KDE</div><div style=\"text-align:right\">KRAJ</div></div>")
    body = ""
    for r in cat["rows"]:
        kc = KRAJ_C[r["kraj"]]
        body += (f"<div class=\"rw\" style=\"display:grid;grid-template-columns:200px minmax(0,1fr) 96px;gap:22px;align-items:center;"
                 f"padding:26px 0;border-bottom:2px solid {line}\">"
                 f"<div style=\"display:flex;flex-direction:column;gap:4px\"><div style=\"font-family:'Anton',sans-serif;font-size:56px;line-height:1;color:{p['c2']}\">{T(r['day'])}</div>"
                 f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:700;font-size:26px;letter-spacing:2px;color:{p['muted']}\">{T(r['date'])}</div></div>"
                 f"<div style=\"display:flex;flex-direction:column;gap:6px;min-width:0\">"
                 f"<div class=\"nm\" style=\"font-family:'Anton',sans-serif;font-size:46px;line-height:1.02;text-transform:uppercase\">{T(r['name'])}</div>"
                 f"<div style=\"font-weight:800;font-size:28px;color:{p['text']}\">{T(r['obec'])}</div>"
                 f"<div class=\"sb\" style=\"font-size:24px;color:{sec};opacity:.85\">{T(r.get('sub',''))}</div></div>"
                 f"<div style=\"justify-self:end;width:86px;height:56px;border-radius:14px;border:3px solid {kc};color:{kc};display:flex;"
                 f"align-items:center;justify-content:center;font-family:'Anton',sans-serif;font-size:32px\">{r['kraj']}</div></div>")
    inner = (vbig("width:1000px;height:1000px;right:-430px;bottom:-400px", 0.32) +
        f"<div style=\"position:relative;display:flex;justify-content:space-between;align-items:center\">" + logo(300, 90) + label() + "</div>"
        f"<div style=\"position:relative;display:flex;flex-direction:column;gap:10px\">"
        f"<div style=\"align-self:flex-start;padding:10px 24px;border-radius:999px;background:linear-gradient(90deg,{p['c2']},{p['c1']});color:{p['bg3']};"
        f"font-weight:800;font-size:24px;letter-spacing:3px\">{T(cat['tag'])}</div>"
        f"<h1 style=\"margin:0;font-family:'Anton',sans-serif;font-weight:400;font-size:128px;line-height:0.93;text-transform:uppercase\">{cat['title']}</h1></div>"
        f"<div style=\"position:relative;flex-grow:1;min-height:0;display:flex;flex-direction:column\">{hdr}"
        f"<div data-list style=\"flex:1 1 auto;min-height:0;overflow:hidden;display:flex;flex-direction:column;border-top:2px solid {line}\">{body}</div></div>"
        f"<div style=\"position:relative;display:flex;justify-content:space-between;align-items:center;font-family:'Josefin Sans',sans-serif;font-weight:600;"
        f"font-size:26px;letter-spacing:5px;color:{p['muted']}\"><div>@VONKIOEVENTS</div>"
        f"<div style=\"color:{p['text']}\">{page:02d} / {total:02d} · SWIPNI</div></div>")
    return frame(inner, "padding:80px;display:flex;flex-direction:column;gap:36px")


def s_follow(spec):
    p = P
    l1, l2 = spec["follow"]
    inner = (vbig("width:1200px;height:1200px;right:-520px;bottom:-180px", 0.42) +
        f"<svg aria-hidden=\"true\" width=\"1080\" height=\"1350\" viewBox=\"0 0 1080 1350\" style=\"position:absolute;left:0;top:0\">"
        f"<defs><linearGradient id=\"arrMM\" x1=\"1\" y1=\"1\" x2=\"0\" y2=\"0\"><stop offset=\"0\" stop-color=\"{p['c1']}\"></stop><stop offset=\"1\" stop-color=\"{p['c2']}\"></stop></linearGradient></defs>"
        f"<path d=\"M 640 640 C 660 360 390 150 132 96\" fill=\"none\" stroke=\"url(#arrMM)\" stroke-width=\"20\" stroke-linecap=\"round\"></path>"
        f"<path d=\"M 188 154 L 132 96 L 204 62\" fill=\"none\" stroke=\"{p['c2']}\" stroke-width=\"20\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg>"
        f"<div style=\"position:absolute;left:120px;top:230px;transform:rotate(-6deg);padding:20px 34px;border-radius:999px;background:{p['text']};color:{p['bg3']};font-weight:800;font-size:38px\">Sleduj @vonkioevents</div>"
        f"<div style=\"position:absolute;left:72px;right:72px;top:600px;display:flex;flex-direction:column\">"
        f"<div style=\"max-width:100%\"><div data-fitw class=\"fitw\" style=\"font-family:'Anton',sans-serif;font-size:200px;line-height:0.9;text-transform:uppercase\">{T(l1)}</div></div>"
        f"<div style=\"align-self:flex-start;max-width:100%\"><div data-fitw class=\"fitw gt\" style=\"font-family:'Anton',sans-serif;font-size:260px;line-height:0.88;text-transform:uppercase\">{T(l2)}</div></div>"
        f"<div style=\"margin-top:34px;font-size:36px;font-weight:700;color:{p['text']}\">{T(spec.get('follow_note',''))}</div></div>"
        f"<div style=\"position:absolute;left:80px;right:80px;bottom:70px;display:flex;justify-content:space-between;align-items:flex-end\">"
        + logo(320, 100) + "</div>")
    return frame(inner)


def build(spec):
    cats = [c for c in spec["cats"] if c["rows"]]
    total = len(cats) + 2
    out = [("01-MM-Hook", s_hook(spec))]
    for i, c in enumerate(cats):
        out.append((f"{i+2:02d}-MM-{c['slug']}", s_cat(c, i + 2, total)))
    out.append((f"{total:02d}-MM-Follow", s_follow(spec)))
    return out


def main(spec_path, out_dir, fmt="jpg"):
    A = json.load(open(os.path.join(HERE, "assets.json")))
    spec = json.load(open(spec_path, encoding="utf-8"))
    os.makedirs(out_dir, exist_ok=True)
    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for name, body in build(spec):
            pg.set_content(head(A) + body + FOOT, wait_until="load")
            pg.evaluate("window.__fit()")
            f = os.path.join(out_dir, f"{name}.{fmt}")
            if fmt == "jpg":
                pg.locator("#slide").screenshot(path=f, type="jpeg", quality=92)
            else:
                pg.locator("#slide").screenshot(path=f)
            made.append(f)
        br.close()
    print(json.dumps({"slides": made}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "jpg")
