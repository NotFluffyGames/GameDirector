#!/usr/bin/env python3
"""Measure game captures (PNG screenshots) so role reviewers work from facts. Engine-independent, stdlib only.

Usage: python3 measure.py <command> ...   (prints JSON to stdout; exit 2 with "measure: <reason>" on bad input)
  palette PNG --hex "#rrggbb,..." [--tolerance 24]   share of opaque pixels near the listed colours
  values PNG                                         luma histogram (Rec. 709, 10 bins) and midtone share
  contrast PNG --a x,y,w,h --b x,y,w,h               WCAG contrast ratio of two regions' mean luminance
  derive PNG --out DIR                               grayscale, thumb and three colour-blindness simulations
  shrink PNG --out PNG [--max 1280]                  copy with the longest side at most --max (box average)
  sheet PNG... --out PNG [--cols 4]                  contact sheet of equal-size frames, row-major

Reads PNG bit depth 8, colour types 0, 2, 3, 4, 6, no interlace. Writes 8-bit RGB or RGBA.
"""
import argparse
import json
import math
import struct
import sys
import zlib
from collections import Counter
from itertools import chain, repeat
from pathlib import Path

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}

# Machado, Oliveira and Fernandes (2009), "A Physiologically-based Model for Simulation of Color Vision
# Deficiency", IEEE TVCG 15(6): severity 1.0 matrices, applied to linear RGB. Values are the widely
# republished 6-digit table, transcribed from memory of that table and not re-checked against the paper.
CVD_MATRICES = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


class Bad(Exception):
    """Bad input; reported as `measure: <reason>` with exit code 2."""


# --- PNG codec ---------------------------------------------------------------------------------------

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def _unfilter_line(ftype, line, prev, bpp):
    """Undo one scanline's filter in place (line is a bytearray); the filter type is dispatched once per row."""
    n = len(line)
    if ftype == 0:
        pass
    elif ftype == 1:
        for i in range(bpp, n):
            line[i] = (line[i] + line[i - bpp]) & 255
    elif ftype == 2:
        line[:] = bytes((x + b) & 255 for x, b in zip(line, prev))
    elif ftype == 3:
        for i in range(min(bpp, n)):
            line[i] = (line[i] + (prev[i] >> 1)) & 255
        for i in range(bpp, n):
            line[i] = (line[i] + ((line[i - bpp] + prev[i]) >> 1)) & 255
    elif ftype == 4:
        for i in range(min(bpp, n)):
            line[i] = (line[i] + prev[i]) & 255
        for i in range(bpp, n):
            a, b, c = line[i - bpp], prev[i], prev[i - bpp]
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            line[i] = (line[i] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
    else:
        raise Bad(f"unsupported PNG (filter type {ftype})")


def _unfilter(data, height, stride, bpp):
    if len(data) < height * (stride + 1):
        raise Bad("unsupported PNG (truncated data)")
    out, prev, pos = [], bytearray(stride), 0
    for _ in range(height):
        line = bytearray(data[pos + 1:pos + 1 + stride])
        _unfilter_line(data[pos], line, prev, bpp)
        pos += 1 + stride
        out.append(line)
        prev = line
    return out


def read_png(path):
    """Return (width, height, rows); rows is a list of lists of (r, g, b, a) tuples."""
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        raise Bad(f"cannot read {path}: {e.strerror}")
    if not raw.startswith(SIGNATURE):
        raise Bad(f"unsupported PNG (not a PNG file: {path})")
    pos, ihdr, plte, trns, idat = 8, None, b"", b"", b""
    while pos + 8 <= len(raw):
        length, kind = struct.unpack(">I4s", raw[pos:pos + 8])
        body = raw[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            if len(body) != 13:
                raise Bad("unsupported PNG (truncated IHDR)")
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            plte = body
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if ihdr is None:
        raise Bad("unsupported PNG (no IHDR)")
    width, height, depth, ctype, _, _, interlace = ihdr
    if depth != 8 or ctype not in CHANNELS or interlace:
        raise Bad(f"unsupported PNG (bit depth {depth}, colour type {ctype}, interlace {interlace})")
    try:
        data = zlib.decompress(idat)
    except zlib.error:
        raise Bad("unsupported PNG (corrupt image data)")
    n = CHANNELS[ctype]
    lines = _unfilter(data, height, width * n, n)
    rows = []
    for line in lines:
        if ctype == 6:
            row = list(zip(line[0::4], line[1::4], line[2::4], line[3::4]))
        elif ctype == 2:
            row = list(zip(line[0::3], line[1::3], line[2::3], repeat(255)))
        elif ctype == 0:
            row = list(zip(line, line, line, repeat(255)))
        elif ctype == 4:
            row = list(zip(line[0::2], line[0::2], line[0::2], line[1::2]))
        else:
            if line and max(line) * 3 + 3 > len(plte):
                raise Bad("unsupported PNG (palette index out of range)")
            lut = [(plte[i * 3], plte[i * 3 + 1], plte[i * 3 + 2], trns[i] if i < len(trns) else 255)
                   for i in range(len(plte) // 3)]
            row = [lut[i] for i in line]
        rows.append(row)
    return width, height, rows


def write_png(path, width, height, rows):
    """Write 8-bit RGBA, or RGB when every pixel is opaque."""
    flats = [bytes(chain.from_iterable(row)) for row in rows]
    opaque = all(f[3::4].count(255) == width for f in flats)
    body = bytearray()
    for f in flats:
        body.append(0)
        if opaque:
            rgb = bytearray(3 * width)
            rgb[0::3], rgb[1::3], rgb[2::3] = f[0::4], f[1::4], f[2::4]
            body.extend(rgb)
        else:
            body.extend(f)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2 if opaque else 6, 0, 0, 0)
    _write(path, SIGNATURE + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(body))) + chunk(b"IEND", b""))


def _write(path, data):
    try:
        Path(path).write_bytes(data)
    except OSError as e:
        raise Bad(f"cannot write {path}: {e.strerror}")


# --- colour maths ------------------------------------------------------------------------------------

def to_linear(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_srgb(v):
    v = min(1.0, max(0.0, v))
    return round(255 * (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055))


def luminance(p):
    return 0.2126 * to_linear(p[0]) + 0.7152 * to_linear(p[1]) + 0.0722 * to_linear(p[2])


def luma(p):
    return (0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]) / 255


def parse_hex(text):
    h = text.strip().lstrip("#")
    if len(h) != 6:
        raise Bad(f"bad colour {text!r}, expected #rrggbb")
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        raise Bad(f"bad colour {text!r}, expected #rrggbb")


def parse_region(text, width, height):
    try:
        x, y, w, h = (int(v) for v in text.split(","))
    except ValueError:
        raise Bad(f"bad region {text!r}, expected x,y,w,h")
    if w < 1 or h < 1 or x < 0 or y < 0 or x + w > width or y + h > height:
        raise Bad(f"region {text} is outside the {width}x{height} image")
    return x, y, w, h


def opaque_counts(rows):
    """Counter of opaque (alpha >= 128) pixels by colour, so per-colour work runs once per unique colour."""
    counts = Counter(chain.from_iterable(rows))
    return Counter({p: n for p, n in counts.items() if p[3] >= 128})


# --- commands ----------------------------------------------------------------------------------------

def cmd_palette(args):
    _, _, rows = read_png(args.png)
    colours = [c for c in args.hex.split(",") if c.strip()]
    if not colours:
        raise Bad("palette needs at least one colour in --hex")
    targets = [(f"#{c.strip().lstrip('#').lower()}", parse_hex(c)) for c in colours]
    colour_counts = opaque_counts(rows)
    total = sum(colour_counts.values()) or 1
    counts = {name: 0 for name, _ in targets}
    matched = 0
    for p, n in colour_counts.items():
        hit = False
        for name, t in targets:
            if math.dist(p[:3], t) <= args.tolerance:
                counts[name] += n
                hit = True
        if hit:
            matched += n
    return {"match_share": matched / total, "per_colour": {k: v / total for k, v in counts.items()},
            "off_palette_share": (sum(colour_counts.values()) - matched) / total if colour_counts else 0.0}


def cmd_values(args):
    _, _, rows = read_png(args.png)
    bins = [0] * 10
    for p, n in opaque_counts(rows).items():
        bins[min(9, int(luma(p) * 10))] += n
    total = sum(bins) or 1
    shares = [b / total for b in bins]
    return {"bins": shares, "midtone_share": sum(shares[3:7])}


def cmd_contrast(args):
    width, height, rows = read_png(args.png)

    def mean_lum(text):
        x, y, w, h = parse_region(text, width, height)
        counts = Counter(chain.from_iterable(row[x:x + w] for row in rows[y:y + h]))
        return sum(luminance(p) * n for p, n in counts.items()) / (w * h)

    a, b = mean_lum(args.a), mean_lum(args.b)
    hi, lo = max(a, b), min(a, b)
    return {"ratio": (hi + 0.05) / (lo + 0.05)}


def thumbnail(width, height, rows, longest=160):
    scale = max(width, height) / longest
    if scale <= 1:
        return width, height, rows
    nw, nh = max(1, round(width / scale)), max(1, round(height / scale))
    out = []
    for j in range(nh):
        y0, y1 = j * height // nh, max(j * height // nh + 1, (j + 1) * height // nh)
        row = []
        for i in range(nw):
            x0, x1 = i * width // nw, max(i * width // nw + 1, (i + 1) * width // nw)
            cell = [p for r in rows[y0:y1] for p in r[x0:x1]]
            row.append(tuple(round(sum(p[k] for p in cell) / len(cell)) for k in range(4)))
        out.append(row)
    return nw, nh, out


def map_colours(rows, fn):
    """Apply fn to every pixel, computing it once per unique colour."""
    cache = {p: fn(p) for p in set(chain.from_iterable(rows))}
    return [[cache[p] for p in row] for row in rows]


def simulate(rows, matrix):
    def convert(p):
        lin = [to_linear(c) for c in p[:3]]
        return tuple(to_srgb(sum(m * v for m, v in zip(mrow, lin))) for mrow in matrix) + (p[3],)
    return map_colours(rows, convert)


def cmd_derive(args):
    width, height, rows = read_png(args.png)
    out = Path(args.out)
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise Bad(f"cannot create {out}: {e.strerror}")
    gray = map_colours(rows, lambda p: (round(luma(p) * 255),) * 3 + (p[3],))
    tw, th, trows = thumbnail(width, height, rows)
    images = {"grayscale.png": (width, height, gray), "thumb.png": (tw, th, trows)}
    for kind, matrix in CVD_MATRICES.items():
        images[f"cvd-{kind}.png"] = (width, height, simulate(rows, matrix))
    written = []
    for name, (w, h, r) in images.items():
        write_png(str(out / name), w, h, r)
        written.append(str(out / name))
    return {"written": written}


def cmd_shrink(args):
    width, height, rows = read_png(args.png)
    if args.max < 1:
        raise Bad("shrink needs --max of at least 1")
    w, h, small = thumbnail(width, height, rows, longest=args.max)
    write_png(args.out, w, h, small)
    return {"written": args.out, "size": [w, h]}


def cmd_sheet(args):
    frames = [read_png(p) for p in args.png]
    w, h = frames[0][:2]
    if any(f[:2] != (w, h) for f in frames):
        raise Bad("sheet frames must all be the same size")
    cols = max(1, min(args.cols, len(frames)))
    nrows = -(-len(frames) // cols)
    blank = (0, 0, 0, 0)
    canvas = [[blank] * (cols * w) for _ in range(nrows * h)]
    for n, (_, _, rows) in enumerate(frames):
        ox, oy = (n % cols) * w, (n // cols) * h
        for y, row in enumerate(rows):
            canvas[oy + y][ox:ox + w] = row
    write_png(args.out, cols * w, nrows * h, canvas)
    return {"written": args.out, "frames": len(frames)}


def build_parser():
    parser = argparse.ArgumentParser(prog="measure", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("palette")
    p.add_argument("png")
    p.add_argument("--hex", required=True)
    p.add_argument("--tolerance", type=float, default=24)
    p.set_defaults(run=cmd_palette)
    p = sub.add_parser("values")
    p.add_argument("png")
    p.set_defaults(run=cmd_values)
    p = sub.add_parser("contrast")
    p.add_argument("png")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.set_defaults(run=cmd_contrast)
    p = sub.add_parser("derive")
    p.add_argument("png")
    p.add_argument("--out", required=True)
    p.set_defaults(run=cmd_derive)
    p = sub.add_parser("shrink")
    p.add_argument("png")
    p.add_argument("--out", required=True)
    p.add_argument("--max", type=int, default=1280)
    p.set_defaults(run=cmd_shrink)

    p = sub.add_parser("sheet")
    p.add_argument("png", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--cols", type=int, default=4)
    p.set_defaults(run=cmd_sheet)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as e:
        raise SystemExit(2 if e.code else 0)
    try:
        print(json.dumps(args.run(args)))
    except Bad as e:
        print(f"measure: {e}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
