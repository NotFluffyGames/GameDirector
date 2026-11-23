#!/usr/bin/env python3
"""Measure game captures (PNG screenshots) so role reviewers work from facts. Engine-independent, stdlib only.

Usage: python3 measure.py <command> ...   (prints JSON to stdout; exit 2 with "measure: <reason>" on bad input)
  palette PNG --hex "#rrggbb,..." [--tolerance 24]   share of opaque pixels near the listed colours
  values PNG                                         luma histogram (Rec. 709, 10 bins) and midtone share
  contrast PNG --a x,y,w,h --b x,y,w,h               WCAG contrast ratio of two regions' mean luminance
  derive PNG --out DIR                               grayscale, thumb and three colour-blindness simulations
  sheet PNG... --out PNG [--cols 4]                  contact sheet of equal-size frames, row-major

Reads PNG bit depth 8, colour types 0, 2, 3, 4, 6, no interlace. Writes 8-bit RGB or RGBA.
"""
import argparse
import json
import math
import struct
import sys
import zlib
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


def _unfilter(data, height, stride, bpp):
    out, prev, pos = [], bytearray(stride), 0
    for _ in range(height):
        ftype, line = data[pos], bytearray(data[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if len(line) != stride:
            raise Bad("unsupported PNG (truncated data)")
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], (prev[i - bpp] if i >= bpp else 0)
            if ftype == 1:
                line[i] = (line[i] + a) & 255
            elif ftype == 2:
                line[i] = (line[i] + b) & 255
            elif ftype == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif ftype == 4:
                line[i] = (line[i] + _paeth(a, b, c)) & 255
            elif ftype != 0:
                raise Bad(f"unsupported PNG (filter type {ftype})")
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
            row = [tuple(line[i:i + 4]) for i in range(0, len(line), 4)]
        elif ctype == 2:
            row = [(line[i], line[i + 1], line[i + 2], 255) for i in range(0, len(line), 3)]
        elif ctype == 0:
            row = [(v, v, v, 255) for v in line]
        elif ctype == 4:
            row = [(line[i], line[i], line[i], line[i + 1]) for i in range(0, len(line), 2)]
        else:
            row = []
            for idx in line:
                if idx * 3 + 3 > len(plte):
                    raise Bad("unsupported PNG (palette index out of range)")
                r, g, b = plte[idx * 3:idx * 3 + 3]
                row.append((r, g, b, trns[idx] if idx < len(trns) else 255))
        rows.append(row)
    return width, height, rows


def write_png(path, width, height, rows):
    """Write 8-bit RGBA, or RGB when every pixel is opaque."""
    opaque = all(p[3] == 255 for row in rows for p in row)
    n = 3 if opaque else 4
    body = bytearray()
    for row in rows:
        body.append(0)
        for p in row:
            body.extend(p[:n])

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2 if opaque else 6, 0, 0, 0)
    Path(path).write_bytes(SIGNATURE + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(body))) + chunk(b"IEND", b""))


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


def opaque_pixels(rows):
    return [p for row in rows for p in row if p[3] >= 128]


# --- commands ----------------------------------------------------------------------------------------

def cmd_palette(args):
    _, _, rows = read_png(args.png)
    colours = [c for c in args.hex.split(",") if c.strip()]
    if not colours:
        raise Bad("palette needs at least one colour in --hex")
    targets = [(f"#{c.strip().lstrip('#').lower()}", parse_hex(c)) for c in colours]
    pixels = opaque_pixels(rows)
    total = len(pixels) or 1
    counts = {name: 0 for name, _ in targets}
    matched = 0
    for p in pixels:
        hit = False
        for name, t in targets:
            if math.dist(p[:3], t) <= args.tolerance:
                counts[name] += 1
                hit = True
        matched += hit
    return {"match_share": matched / total, "per_colour": {k: v / total for k, v in counts.items()},
            "off_palette_share": (len(pixels) - matched) / total if pixels else 0.0}


def cmd_values(args):
    _, _, rows = read_png(args.png)
    pixels = opaque_pixels(rows)
    bins = [0] * 10
    for p in pixels:
        bins[min(9, int(luma(p) * 10))] += 1
    total = len(pixels) or 1
    shares = [b / total for b in bins]
    return {"bins": shares, "midtone_share": sum(shares[3:7])}


def cmd_contrast(args):
    width, height, rows = read_png(args.png)

    def mean_lum(text):
        x, y, w, h = parse_region(text, width, height)
        vals = [luminance(p) for row in rows[y:y + h] for p in row[x:x + w]]
        return sum(vals) / len(vals)

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


def simulate(rows, matrix):
    cache, out = {}, []
    for row in rows:
        new = []
        for p in row:
            if p not in cache:
                lin = [to_linear(c) for c in p[:3]]
                cache[p] = tuple(to_srgb(sum(m * v for m, v in zip(mrow, lin))) for mrow in matrix) + (p[3],)
            new.append(cache[p])
        out.append(new)
    return out


def cmd_derive(args):
    width, height, rows = read_png(args.png)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    gray = [[(v, v, v, p[3]) for p in row for v in [round(luma(p) * 255)]] for row in rows]
    tw, th, trows = thumbnail(width, height, rows)
    images = {"grayscale.png": (width, height, gray), "thumb.png": (tw, th, trows)}
    for kind, matrix in CVD_MATRICES.items():
        images[f"cvd-{kind}.png"] = (width, height, simulate(rows, matrix))
    written = []
    for name, (w, h, r) in images.items():
        write_png(str(out / name), w, h, r)
        written.append(str(out / name))
    return {"written": written}


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
