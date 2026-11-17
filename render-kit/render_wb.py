#!/usr/bin/env python3
"""VONKIO – renderer krajských postov (šablóna „Krajský post“, schválená 1. 11. 2026). Workbench verzia (JPEG)."""
import base64, html, json, os, re, sys, unicodedata, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

PAL = {
 "Bratislavský":     dict(c1="#4C8DFF", c2="#39D3FF", c3="#6A5BFF", bg1="#0C1A3D", bg2="#070D20", bg3="#04060E", text="#EAF2FF", muted="#9FB3D9", sk="BA"),
 "Trnavský":         dict(c1="#FF5C8A", c2="#FF9EC0", c3="#E83A73", bg1="#2A0B18", bg2="#16060E", bg3="#0A0306", text="#FFEFF4", muted="#D9A3B6", sk="TT"),
 "Trenčiansky":      dict(c1="#FFC83D", c2="#FFE98A", c3="#FF9F1C", bg1="#2B2108", bg2="#171105", bg3="#0A0803", text="#FFF8E6", muted="#D9C79A", sk="TN"),
 "Nitriansky":       dict(c1="#B5E03A", c2="#E5F77A", c3="#6FCF3A", bg1="#1C2608", bg2="#0F1505", bg3="#070A03", text="#F6FBE6", muted="#B9CC93", sk="NR"),
 "Žilinský":         dict(c1="#1FD1C1", c2="#7DF2E3", c3="#2AA8E8", bg1="#062A2A", bg2="#041818", bg3="#020A0B", text="#E8FFFC", muted="#93CCC5", sk="ZA"),
 "Banskobystrický":  dict(c1="#2ECC71", c2="#9BF0B5", c3="#19B394", bg1="#072A17", bg2="#04170D", bg3="#020A06", text="#EAFFF1", muted="#95C9A8", sk="BB"),
 "Prešovský":        dict(c1="#FF4D4D", c2="#FF8A70", c3="#E8325A", bg1="#2E0A0A", bg2="#190606", bg3="#0B0303", text="#FFEDEB", muted="#D9A19B", sk="PO"),
 "Košický":          dict(c1="#9D7BFF", c2="#C9B5FF", c3="#6A4BFF", bg1="#1A1240", bg2="#0E0A24", bg3="#06040F", text="#F1EDFF", muted="#B0A6D9", sk="KE"),
}
ORDER = ["Bratislavský", "Košický", "Žilinský", "Banskobystrický", "Nitriansky", "Prešovský", "Trnavský", "Trenčiansky"]


def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def mix(h1, h2, t):
    a, b = hex2rgb(h1), hex2rgb(h2)
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def rgba(h, a):
    r, g, b = hex2rgb(h); return f"rgba({r},{g},{b},{a})"

def T(s):
    s = html.escape(str(s or ""))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("\n", "<br>")


def head(p, A):
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
function fitH(el,maxH){let fs=parseFloat(getComputedStyle(el).fontSize);let n=0;
 while(el.scrollHeight>maxH&&fs>30&&n<200){fs-=3;el.style.fontSize=fs+'px';n++}}
window.__fit=async function(){await document.fonts.ready;
 document.querySelectorAll('[data-fitw]').forEach(el=>{el.style.display='inline-block';fitW(el)});
 document.querySelectorAll('[data-fith]').forEach(el=>fitH(el,parseFloat(el.dataset.fith)));
 const L=document.querySelector('[data-list]');
 if(L){let k=0;while(L.scrollHeight>L.clientHeight+1&&k<40){k++;
   L.querySelectorAll('.nm').forEach(e=>e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)-1.5)+'px');
   L.querySelectorAll('.sb').forEach(e=>e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)-0.8)+'px');
   L.querySelectorAll('.rw').forEach(e=>{const p=parseFloat(getComputedStyle(e).paddingTop);if(p>6){e.style.paddingTop=e.style.paddingBottom=(p-1.5)+'px'}});}}
 return true};
</script></body></html>"""

def frame(p, inner, extra_style=""):
    return (f"<div id=\"slide\" style=\"width:1080px;height:1350px;position:relative;overflow:hidden;"
            f"background:linear-gradient(165deg,{p['bg1']} 0%,{p['bg2']} 45%,{p['bg3']} 100%);"
            f"color:{p['text']};font-family:'Manrope',sans-serif;{extra_style}\">{inner}</div>")

def vbig(p, style, op):
    return (f"<div class=\"vmask\" aria-hidden=\"true\" style=\"position:absolute;{style};opacity:{op};"
            f"background:linear-gradient(135deg,{p['c2']} 0%,{p['c1']} 55%,{p['c3']} 100%)\"></div>")

def logo(p, w, h):
    return (f"<div class=\"lmask\" role=\"img\" aria-label=\"VONKIO\" style=\"width:{w}px;height:{h}px;"
            f"background:linear-gradient(90deg,{p['c2']} 0%,{p['c1']} 50%,{p['c3']} 100%)\"></div>")

def tipov(n):
    return "tip na" if n == 1 else ("tipy na" if 2 <= n <= 4 else "tipov na")


def s_hook(p, post, week_dates):
    lines = ""
    for txt, acc in post["hook"]:
        if acc:
            lines += (f"<div style=\"align-self:flex-start;max-width:100%\"><div data-fitw class=\"fitw gt\" style=\"font-family:'Anton',sans-serif;"
                      f"font-size:196px;line-height:0.9;text-transform:uppercase\">{T(txt)}</div></div>")
        else:
            lines += (f"<div style=\"max-width:100%\"><div data-fitw class=\"fitw\" style=\"font-family:'Anton',sans-serif;font-size:150px;"
                      f"line-height:0.95;text-transform:uppercase\">{T(txt)}</div></div>")
    n = int(post.get("count") or 0)
    sticker = (f"<div style=\"position:absolute;right:70px;top:800px;transform:rotate(8deg);width:250px;height:250px;border-radius:50%;"
               f"background:linear-gradient(135deg,{p['c2']},{p['c1']});color:{p['bg3']};display:flex;flex-direction:column;"
               f"align-items:center;justify-content:center;text-align:center\">"
               f"<div style=\"font-family:'Anton',sans-serif;font-size:110px;line-height:0.9\">{n}</div>"
               f"<div style=\"font-weight:800;font-size:28px;line-height:1.1\">{tipov(n)}<br>tento týždeň</div></div>") if n else ""
    inner = (vbig(p, "width:1400px;height:1400px;left:-380px;top:-260px;transform:rotate(180deg)", 0.55) +
        f"<div style=\"position:absolute;left:80px;top:80px;right:80px;display:flex;justify-content:space-between;align-items:center\">"
        f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:28px;letter-spacing:8px\">{T(post['kraj'].upper())} KRAJ · {T(week_dates)}</div>"
        f"<div style=\"width:18px;height:18px;border-radius:50%;background:{p['c2']}\"></div></div>"
        f"<div style=\"position:absolute;left:72px;right:72px;top:300px;display:flex;flex-direction:column\">{lines}</div>"
        + sticker +
        f"<div style=\"position:absolute;left:80px;bottom:70px;right:80px;display:flex;justify-content:space-between;align-items:center\">"
        + logo(p, 380, 120) +
        f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:26px;letter-spacing:6px;color:{p['muted']}\">SWIPNI</div></div>")
    return frame(p, inner)


def s_list(p, post, rows, title_html, page, total, with_v, h1_size, row_pad, gap):
    line = rgba(p["text"], 0.18)
    sec = mix(p["text"], p["muted"], 0.45)
    hdr = (f"<div style=\"display:grid;grid-template-columns:190px minmax(0,1fr) 110px;gap:22px;padding-bottom:10px;"
           f"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:22px;letter-spacing:4px;color:{p['muted']}\">"
           f"<div>DEŇ</div><div>AKCIA</div><div style=\"text-align:right\">SKÓRE</div></div>")
    body = ""
    for r in rows:
        body += (f"<div class=\"rw\" style=\"display:grid;grid-template-columns:190px minmax(0,1fr) 110px;gap:22px;align-items:center;"
                 f"padding:{row_pad}px 0;border-bottom:2px solid {line}\">"
                 f"<div style=\"font-family:'Anton',sans-serif;font-size:54px;line-height:1;color:{p['c1']}\">{T(r['day'])}</div>"
                 f"<div style=\"display:flex;flex-direction:column;gap:4px;min-width:0\">"
                 f"<div class=\"nm\" style=\"font-family:'Anton',sans-serif;font-size:44px;line-height:1;text-transform:uppercase\">{T(r['name'])}</div>"
                 f"<div class=\"sb\" style=\"font-size:25px;color:{sec}\">{T(r.get('sub',''))}</div></div>"
                 f"<div style=\"font-family:'Anton',sans-serif;font-size:58px;line-height:1;text-align:right\">{T(r.get('score',''))}</div></div>")
    rel = "position:relative;" if with_v else ""
    inner = ((vbig(p, "width:1000px;height:1000px;right:-420px;bottom:-380px", 0.4) if with_v else "") +
        f"<div style=\"{rel}display:flex;justify-content:space-between;align-items:center\">" + logo(p, 300, 90) +
        f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:26px;letter-spacing:6px;color:{p['muted']}\">{T(post['kraj'].upper())} KRAJ</div></div>"
        f"<h1 style=\"{rel}margin:0;font-family:'Anton',sans-serif;font-weight:400;font-size:{h1_size}px;line-height:0.93;text-transform:uppercase\">{title_html}</h1>"
        f"<div style=\"{rel}flex-grow:1;min-height:0;display:flex;flex-direction:column\">{hdr}"
        f"<div data-list style=\"flex:1 1 auto;min-height:0;overflow:hidden;display:flex;flex-direction:column;border-top:2px solid {line}\">{body}</div></div>"
        f"<div style=\"{rel}display:flex;justify-content:space-between;align-items:center;font-family:'Josefin Sans',sans-serif;font-weight:600;"
        f"font-size:26px;letter-spacing:5px;color:{p['muted']}\"><div>@VONKIOEVENTS</div>"
        f"<div style=\"color:{p['text']}\">{page:02d} / {total:02d} · SWIPNI</div></div>")
    return frame(p, inner, f"padding:80px;display:flex;flex-direction:column;gap:{gap}px")


ICON = {
 "lineup": "<path d=\"M9 18V5l12-2v13\"></path><circle cx=\"6\" cy=\"18\" r=\"3\"></circle><circle cx=\"18\" cy=\"16\" r=\"3\"></circle>",
 "venue": "<path d=\"M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z\"></path><circle cx=\"12\" cy=\"10\" r=\"2.5\"></circle>",
 "tickets": "<rect x=\"3\" y=\"7\" width=\"18\" height=\"10\" rx=\"2\"></rect><path d=\"M9 7v10\"></path>",
}

def s_card(p, post, c, rank, page, total):
    sc = int(c["score"]); dash = round(sc / 100 * 628.32, 2)
    rid = f"ring{p['sk']}{rank}"
    info = ""
    for k in ("lineup", "venue", "tickets"):
        if c.get(k):
            info += (f"<div style=\"display:flex;align-items:center;gap:20px\"><svg aria-hidden=\"true\" width=\"40\" height=\"40\" style=\"flex:none\" viewBox=\"0 0 24 24\" fill=\"none\" "
                     f"stroke=\"{p['c2']}\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">{ICON[k]}</svg><div>{T(c[k])}</div></div>")
    genre = (f"<div style=\"padding:12px 26px;border-radius:999px;border:2px solid {p['c2']};color:{p['c2']};font-weight:800;font-size:26px;letter-spacing:2px\">{T(c['genre'].upper())}</div>") if c.get("genre") else "<div></div>"
    inner = (vbig(p, "width:900px;height:900px;right:-300px;top:120px", 0.45) +
        f"<div style=\"position:relative;display:flex;justify-content:space-between;align-items:center\">" + logo(p, 300, 90) + genre + "</div>"
        f"<div style=\"position:relative;display:flex;justify-content:space-between;align-items:flex-end\">"
        f"<div style=\"display:flex;flex-direction:column\"><div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:40px;letter-spacing:10px;color:{p['muted']}\">{T(c['when'].upper())}</div>"
        f"<div class=\"gt\" style=\"font-family:'Anton',sans-serif;font-size:300px;line-height:0.9\">{T(c['date'])}</div></div>"
        f"<div style=\"display:flex;flex-direction:column;align-items:center;gap:14px;margin-bottom:20px\">"
        f"<div style=\"padding:8px 18px;border-radius:999px;background:linear-gradient(90deg,{p['c2']},{p['c1']});color:{p['bg3']};font-weight:800;font-size:22px;letter-spacing:2px\">#{rank} V KRAJI</div>"
        f"<div style=\"position:relative;width:230px;height:230px\"><svg role=\"img\" aria-label=\"VONKIO skóre {sc} zo 100\" width=\"230\" height=\"230\" viewBox=\"0 0 230 230\" style=\"position:absolute;left:0;top:0\">"
        f"<defs><linearGradient id=\"{rid}\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop offset=\"0\" stop-color=\"{p['c2']}\"></stop><stop offset=\"0.55\" stop-color=\"{p['c1']}\"></stop><stop offset=\"1\" stop-color=\"{p['c3']}\"></stop></linearGradient></defs>"
        f"<circle cx=\"115\" cy=\"115\" r=\"100\" fill=\"none\" stroke=\"{rgba(p['text'],0.14)}\" stroke-width=\"18\"></circle>"
        f"<circle cx=\"115\" cy=\"115\" r=\"100\" fill=\"none\" stroke=\"url(#{rid})\" stroke-width=\"18\" stroke-linecap=\"round\" stroke-dasharray=\"{dash} 628.32\" transform=\"rotate(-90 115 115)\"></circle></svg>"
        f"<div style=\"position:absolute;left:0;top:0;width:230px;height:230px;display:flex;flex-direction:column;align-items:center;justify-content:center\">"
        f"<div style=\"font-family:'Anton',sans-serif;font-size:100px;line-height:0.95\">{sc}</div>"
        f"<div style=\"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:18px;letter-spacing:4px;color:{p['muted']}\">SKÓRE</div></div></div></div></div>"
        f"<div style=\"position:relative;display:flex;flex-direction:column;gap:36px\">"
        f"<h1 data-fith=\"370\" style=\"margin:0;font-family:'Anton',sans-serif;font-weight:400;font-size:130px;line-height:0.92;text-transform:uppercase\">{T(c['title'])}</h1>"
        f"<div style=\"display:flex;flex-direction:column;gap:16px;font-size:36px\">{info}</div></div>"
        f"<div style=\"position:relative;display:flex;justify-content:space-between;align-items:center;padding-top:28px;border-top:1px solid {rgba(p['text'],0.18)};"
        f"font-family:'Josefin Sans',sans-serif;font-weight:600;font-size:26px;letter-spacing:5px;color:{p['muted']}\"><div>@VONKIOEVENTS</div>"
        f"<div style=\"color:{p['text']}\">{page:02d} / {total:02d}</div></div>")
    return frame(p, inner, "padding:80px;display:flex;flex-direction:column;justify-content:space-between")


def s_follow(p, post):
    l1, l2 = post["follow"]
    note = mix(p["muted"], p["bg1"], 0.25)
    inner = (vbig(p, "width:1200px;height:1200px;right:-520px;bottom:-180px", 0.45) +
        f"<svg aria-hidden=\"true\" width=\"1080\" height=\"1350\" viewBox=\"0 0 1080 1350\" style=\"position:absolute;left:0;top:0\">"
        f"<defs><linearGradient id=\"arr{p['sk']}\" x1=\"1\" y1=\"1\" x2=\"0\" y2=\"0\"><stop offset=\"0\" stop-color=\"{p['c1']}\"></stop><stop offset=\"1\" stop-color=\"{p['c2']}\"></stop></linearGradient></defs>"
        f"<path d=\"M 640 640 C 660 360 390 150 132 96\" fill=\"none\" stroke=\"url(#arr{p['sk']})\" stroke-width=\"20\" stroke-linecap=\"round\"></path>"
        f"<path d=\"M 188 154 L 132 96 L 204 62\" fill=\"none\" stroke=\"{p['c2']}\" stroke-width=\"20\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path></svg>"
        f"<div style=\"position:absolute;left:120px;top:230px;transform:rotate(-6deg);padding:20px 34px;border-radius:999px;background:{p['text']};color:{p['bg3']};font-weight:800;font-size:38px\">Sleduj @vonkioevents</div>"
        f"<div style=\"position:absolute;left:72px;right:72px;top:700px;display:flex;flex-direction:column\">"
        f"<div style=\"max-width:100%\"><div data-fitw class=\"fitw\" style=\"font-family:'Anton',sans-serif;font-size:226px;line-height:0.9;text-transform:uppercase\">{T(l1)}</div></div>"
        f"<div style=\"align-self:flex-start;max-width:100%\"><div data-fitw class=\"fitw gt\" style=\"font-family:'Anton',sans-serif;font-size:290px;line-height:0.88;text-transform:uppercase\">{T(l2)}</div></div></div>"
        f"<div style=\"position:absolute;left:80px;right:80px;bottom:70px;display:flex;justify-content:space-between;align-items:flex-end\">"
        + logo(p, 320, 100) +
        f"<div style=\"font-size:24px;font-weight:500;color:{note};padding-bottom:14px\">Čo znamená skóre? Pozri Highlights.</div></div>")
    return frame(p, inner)


def build_slides(post, week_dates):
    p = dict(PAL[post["kraj"]])
    mimo = post.get("mimo") or []
    total = 6 if mimo else 5
    slides = [("01-Hook", s_hook(p, post, week_dates))]
    slides.append(("02-Tento-tyzden", s_list(p, post, post["tyzden"],
        f"Tento <span class=\"gt\">týždeň</span>", 2, total, False, 112, 14, 30)))
    n = 3
    if mimo:
        slides.append(("03-Mimo-mesta", s_list(p, post, mimo,
            f"Mimo<br><span class=\"gt\">mesta</span>", 3, total, True, 140, 28, 40)))
        n = 4
    for i, c in enumerate(post["cards"][:2]):
        slides.append((f"{n:02d}-Karta{i+1}", s_card(p, post, c, i + 1, n, total))); n += 1
    slides.append((f"{n:02d}-Follow", s_follow(p, post)))
    return p, slides


def main(spec_path, out_dir):
    from PIL import Image
    A = json.load(open(os.path.join(HERE, "assets.json")))
    spec = json.load(open(spec_path, encoding="utf-8"))
    week = spec["week"]; week_dates = spec["dates"]
    from playwright.sync_api import sync_playwright
    made = []
    posts = sorted(spec["posts"], key=lambda q: ORDER.index(q["kraj"]))
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for post in posts:
            p, slides = build_slides(post, week_dates)
            folder = os.path.join(out_dir, week, p["sk"]); os.makedirs(folder, exist_ok=True)
            for f0 in os.listdir(folder): os.remove(os.path.join(folder, f0))
            for i, (name, body) in enumerate(slides, 1):
                pg.set_content(head(p, A) + body + FOOT, wait_until="load")
                pg.evaluate("window.__fit()")
                png = os.path.join(folder, f"{i:02d}.png")
                pg.locator("#slide").screenshot(path=png)
                jpg = os.path.join(folder, f"{i:02d}-{p['sk']}-{name}.jpg")
                Image.open(png).convert("RGB").save(jpg, "JPEG", quality=92, optimize=True)
                os.remove(png); made.append(jpg)
            with open(os.path.join(folder, "caption.txt"), "w", encoding="utf-8") as fh:
                fh.write(post.get("caption", "").strip() + "\n")
        br.close()
    print(json.dumps({"slides": len(made), "posts": len(posts), "out": os.path.join(out_dir, week)}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
