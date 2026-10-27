"""Terminal text effects engine for SigmaOS-terminal-text-effects / SigmaOS-tte-go
(inspired by ttfx and tte-go).

Principles: effects are pure functions text -> text (composable, deterministic,
no randomness, no I/O), fail-fast on unknown effects/options/glyphs, ANSI codes
are transparent to every effect so chaining never corrupts output.
"""
import argparse, colorsys, inspect, math, re, sys

ENGINE = {
    "name": "sigma-tte",
    "summary": "Terminal text effects: box, wave, center, block banner",
    "language": "python",
    "verbs": ["effect", "render", "list", "banner"],
    "principles": ["Separation of Concerns", "Composability", "Fail-Fast",
                   "Least Astonishment", "KISS", "Deterministic Testing"],
}

cli_doc = """\
$ sigma-tte effect box "hi"
┌────┐
│ hi │
└────┘
$ sigma-tte banner SIGMA
$ sigma-tte render "hi" --effects banner,box
$ sigma-tte list
"""


class TteError(ValueError):
    pass


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

_STYLES = {
    "single": ("┌", "─", "┐", "│", "└", "┘"),
    "double": ("╔", "═", "╗", "║", "╚", "╝"),
    "ascii":  ("+", "-", "+", "|", "+", "+"),
}


def strip_ansi(text):
    return _ANSI_RE.sub("", text)


def _visible_len(line):
    return len(strip_ansi(line))


def _map_visible(text, fn):
    """Apply fn(char) to non-ANSI characters only; keep escapes intact."""
    out, i, n = [], 0, 0
    while i < len(text):
        ch = text[i]
        if ch == "\x1b":
            m = _ANSI_RE.match(text, i)
            if m:
                out.append(m.group())
                i = m.end()
                continue
        out.append(fn(ch, n))
        n += 1
        i += 1
    return "".join(out)


# --------------------------------------------------------------------------- #
#  Effects (pure)
# --------------------------------------------------------------------------- #
def box(text, style="single"):
    if not isinstance(text, str) or not text.strip():
        raise TteError("box needs non-empty text")
    if style not in _STYLES:
        raise TteError(f"unknown box style {style!r} "
                       f"(have: {', '.join(sorted(_STYLES))})")
    tl, h, tr, v, bl, br = _STYLES[style]
    lines = text.split("\n")
    width = max(_visible_len(l) for l in lines)
    rule = h * (width + 2)
    out = [tl + rule + tr]
    for line in lines:
        pad = width - _visible_len(line)
        out.append(f"{v} {line}{' ' * pad} {v}")
    out.append(bl + rule + br)
    return "\n".join(out)


def wave(text, hue=180, period=8.0, colorize=True):
    """Sine-shifted truecolour gradient over the visible characters."""
    if not isinstance(hue, (int, float)) or not 0 <= hue < 360:
        raise TteError(f"hue must be in [0, 360), got {hue!r}")
    if not isinstance(period, (int, float)) or period <= 0:
        raise TteError(f"period must be > 0, got {period!r}")
    if not colorize:
        return text

    def paint(ch, n):
        offset = 40.0 * math.sin(2 * math.pi * n / period)
        h = ((hue + offset) % 360) / 360
        r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
        return (f"\x1b[38;2;{round(r * 255)};{round(g * 255)};"
                f"{round(b * 255)}m{ch}")

    lines = [_map_visible(l, paint) for l in text.split("\n")]
    return "\n".join(lines)


def center(text, width=0):
    lines = text.split("\n")
    target = width or max(_visible_len(l) for l in lines)
    if not isinstance(target, int) or target < max(_visible_len(l) for l in lines):
        raise TteError(f"width {target!r} smaller than the longest line")
    out = []
    for line in lines:
        slack = target - _visible_len(line)
        left = slack // 2
        out.append(" " * left + line + " " * (slack - left))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  Block banner: 5x5 bitmap font
# --------------------------------------------------------------------------- #
_FONT = {
    "A": (" ### ", "#   #", "#####", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#### ", "#   #", "#### "),
    "C": (" ### ", "#    ", "#    ", "#    ", " ### "),
    "D": ("#### ", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#### ", "#    ", "#####"),
    "F": ("#####", "#    ", "#### ", "#    ", "#    "),
    "G": (" ### ", "#    ", "#  ##", "#   #", " ### "),
    "H": ("#   #", "#   #", "#####", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("    #", "    #", "    #", "#   #", " ### "),
    "K": ("#   #", "#  # ", "###  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#### ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#### ", "#  # ", "#   #"),
    "S": (" ####", "#    ", " ### ", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#   #", " # # ", "  #  ", " # # ", "#   #"),
    "Y": ("#   #", " # # ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", "#####"),
    "0": (" ### ", "#  ##", "# # #", "##  #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "   # ", "  #  ", "#####"),
    "3": ("#####", "    #", " ### ", "    #", "#####"),
    "4": ("   # ", "  ## ", " # # ", "#####", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "#### "),
    "6": (" ### ", "#    ", "#### ", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", "  #  "),
    "8": (" ### ", "#   #", " ### ", "#   #", " ### "),
    "9": (" ### ", "#   #", " ####", "    #", " ### "),
    " ": ("     ", "     ", "     ", "     ", "     "),
    "-": ("     ", "     ", "#####", "     ", "     "),
    ".": ("     ", "     ", "     ", "     ", "  #  "),
    "!": ("  #  ", "  #  ", "  #  ", "     ", "  #  "),
    ":": ("     ", "  #  ", "     ", "  #  ", "     "),
}


def banner(text, fill="#", frame=False, style="single"):
    if not isinstance(text, str) or not text.strip():
        raise TteError("banner needs non-empty text")
    if not isinstance(fill, str) or len(fill) != 1 or fill in "\n\r\x1b":
        raise TteError(f"fill must be a single character, got {fill!r}")
    rows = [""] * 5
    for idx, raw in enumerate(text.upper()):
        if raw not in _FONT:
            raise TteError(f"no glyph for {raw!r}")
        glyph = _FONT[raw]
        sep = "" if idx == 0 else " "
        for r in range(5):
            rows[r] += sep + glyph[r]
    out = "\n".join(row.replace("#", fill) for row in rows)
    if frame:
        out = box(out, style)
    return out


# --------------------------------------------------------------------------- #
#  Registry / dispatcher
# --------------------------------------------------------------------------- #
EFFECTS = {"box": box, "wave": wave, "center": center, "banner": banner}
DESCRIPTIONS = {
    "box": "frame the text in a border",
    "wave": "sine truecolour gradient per character",
    "center": "centre every line to a common width",
    "banner": "render text as a 5-row block banner",
}


def effect(name, text, **opts):
    fn = EFFECTS.get(name)
    if fn is None:
        raise TteError(f"unknown effect {name!r} "
                       f"(have: {', '.join(sorted(EFFECTS))})")
    allowed = set(inspect.signature(fn).parameters)
    unknown = sorted(set(opts) - allowed)
    if unknown:
        raise TteError(f"effect {name!r} does not accept option(s): "
                       f"{', '.join(unknown)}")
    return fn(text, **opts)


def render(text, names=("box",), **opts):
    """Chain effects in order; options are filtered per effect."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]
    if not names:
        raise TteError("no effects given")
    out = text
    for name in names:
        fn = EFFECTS.get(name)
        if fn is None:
            raise TteError(f"unknown effect {name!r}")
        allowed = set(inspect.signature(fn).parameters)
        out = fn(out, **{k: v for k, v in opts.items() if k in allowed})
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=ENGINE["name"], description=ENGINE["summary"])
    sub = p.add_subparsers(dest="cmd", required=True)
    ef = sub.add_parser("effect", help="apply one named effect")
    ef.add_argument("name")
    ef.add_argument("text")
    ef.add_argument("--hue", type=float, default=None)
    ef.add_argument("--period", type=float, default=None)
    ef.add_argument("--width", type=int, default=None)
    ef.add_argument("--style", default=None, choices=sorted(_STYLES))
    ef.add_argument("--fill", default=None)
    ef.add_argument("--frame", action="store_true")
    rd = sub.add_parser("render", help="chain effects in order")
    rd.add_argument("text")
    rd.add_argument("--effects", default="box",
                    help="comma list, e.g. banner,box")
    rd.add_argument("--hue", type=float, default=None)
    rd.add_argument("--style", default=None, choices=sorted(_STYLES))
    rd.add_argument("--fill", default=None)
    rd.add_argument("--frame", action="store_true")
    sub.add_parser("list", help="list available effects")
    bn = sub.add_parser("banner", help="block banner of the text")
    bn.add_argument("text")
    bn.add_argument("--fill", default="#")
    bn.add_argument("--frame", action="store_true")
    bn.add_argument("--style", default="single", choices=sorted(_STYLES))
    return p


def _opts(args):
    opts = {}
    for key in ("hue", "period", "width", "style", "fill"):
        value = getattr(args, key, None)
        if value is not None:
            opts[key] = value
    if getattr(args, "frame", False):
        opts["frame"] = True
    return opts


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "effect":
            print(effect(args.name, args.text, **_opts(args)))
        elif args.cmd == "render":
            print(render(args.text, args.effects, **_opts(args)))
        elif args.cmd == "list":
            for name in sorted(EFFECTS):
                print(f"{name:<10} {DESCRIPTIONS[name]}")
        elif args.cmd == "banner":
            print(banner(args.text, args.fill, args.frame, args.style))
        return 0
    except TteError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def self_test() -> None:
    # --- box ---------------------------------------------------------------
    framed = box("hi")
    assert framed == "┌────┐\n│ hi │\n└────┘", repr(framed)
    ascii_box = box("hi", style="ascii")
    assert ascii_box == "+----+\n| hi |\n+----+", repr(ascii_box)
    ragged = box("ab\ncdef")
    widths = {len(l) for l in ragged.split("\n")}
    assert len(widths) == 1, ragged           # uniform width
    assert "│ ab   │" in ragged and "│ cdef │" in ragged
    for bad_call in ((box, ("",)), (box, ("x", "fancy")),
                     (box, (None,))):
        try:
            bad_call[0](*bad_call[1])
        except TteError:
            pass
        else:
            raise AssertionError(f"should have rejected: {bad_call}")

    # --- wave (ANSI-safe, deterministic) ------------------------------------
    w = wave("abcdef", hue=200)
    assert strip_ansi(w) == "abcdef", repr(strip_ansi(w))
    codes = set(re.findall(r"\x1b\[38;2;\d+;\d+;\d+m", w))
    assert len(codes) >= 3, codes              # gradient actually varies
    for code in re.findall(r"\x1b\[38;2;(\d+);(\d+);(\d+)m", w):
        assert all(0 <= int(c) <= 255 for c in code), code
    assert wave("abc", colorize=False) == "abc"
    assert strip_ansi(wave("a\nb")) == "a\nb"  # newlines survive
    assert wave("abcdef", hue=200) == w       # deterministic
    for bad_call in ((wave, ("x", -1)), (wave, ("x", 400)), (wave, ("x", 180, 0))):
        try:
            bad_call[0](*bad_call[1])
        except TteError:
            pass
        else:
            raise AssertionError(f"should have rejected: {bad_call}")

    # --- center -------------------------------------------------------------
    assert center("hi", 6) == "  hi  "
    assert center("hi", 7) == "  hi   "
    assert len(center("ab\ncd", 10).split("\n")[0]) == 10
    try:
        center("hello", 3)
    except TteError:
        pass
    else:
        raise AssertionError("too-narrow center not rejected")

    # --- banner -------------------------------------------------------------
    b = banner("SIGMA")
    rows = b.split("\n")
    assert len(rows) == 5, rows
    assert {len(r) for r in rows} == {5 * 5 + 4}, {len(r) for r in rows}
    assert "#" in b and any("#" in r for r in rows)
    assert banner("sig") == banner("SIG")      # case-insensitive
    assert banner("A") == _FONT["A"][0][:0] + "\n".join(_FONT["A"])
    at = banner("A", fill="@")
    assert "#" not in at and "@" in at
    framed_banner = banner("OK", frame=True)
    assert framed_banner.startswith("┌") and framed_banner.endswith("┘")
    assert banner("SIGMA") == b               # deterministic
    for bad in (("é",), ("",), ("AB C$1",)):
        try:
            banner(*bad)
        except TteError:
            pass
        else:
            raise AssertionError(f"banner should have rejected: {bad}")

    # --- dispatcher / chaining ---------------------------------------------
    assert sorted(EFFECTS) == ["banner", "box", "center", "wave"]
    assert all(DESCRIPTIONS[n] for n in EFFECTS)
    assert effect("box", "hi") == framed
    try:
        effect("nope", "hi")
    except TteError:
        pass
    else:
        raise AssertionError("unknown effect not rejected")
    try:
        effect("box", "hi", hue=10)
    except TteError:
        pass
    else:
        raise AssertionError("unknown option not rejected")
    ch = render("hi", ["box"])
    assert "┌" in ch and "│ hi │" in ch
    ch2 = render("hi", ["center", "box"], width=8)
    assert "│    hi    │" in ch2, ch2
    assert render("ABC", ["banner"]) == banner("ABC")
    assert render("hi", ["banner", "box"]).startswith("┌")
    try:
        render("hi", ["box", "nope"])
    except TteError:
        pass
    else:
        raise AssertionError("unknown chained effect not rejected")
    try:
        render("hi", [])
    except TteError:
        pass
    else:
        raise AssertionError("empty chain not rejected")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
