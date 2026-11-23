"""measure.py: facts and derived images from PNG captures.

Run: cd tests && python3 -m unittest test_measure
"""
import contextlib
import importlib.util
import io
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "skills" / "game-review" / "scripts" / "measure.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("measure", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


measure = load_tool()


def px(hex_colour):
    h = hex_colour.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


class MeasureCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def png(self, name, rows):
        path = self.dir / name
        measure.write_png(str(path), len(rows[0]), len(rows), rows)
        return str(path)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                measure.main([str(a) for a in argv])
            except SystemExit as e:
                code = e.code or 0
        return code, out.getvalue(), err.getvalue()

    def run_json(self, *argv):
        code, out, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)
        return json.loads(out)


class Commands(MeasureCase):
    def test_palette_share_of_a_two_colour_image(self):
        path = self.png("a.png", [[px("#112233")] * 3 + [px("#ffffff")]])
        result = self.run_json("palette", path, "--hex", "#112233")
        self.assertAlmostEqual(result["match_share"], 0.75)
        self.assertAlmostEqual(result["off_palette_share"], 0.25)
        self.assertAlmostEqual(result["per_colour"]["#112233"], 0.75)

    def test_values_put_mid_grey_in_the_midtones(self):
        path = self.png("g.png", [[px("#808080")] * 2] * 2)
        result = self.run_json("values", path)
        self.assertEqual(len(result["bins"]), 10)
        self.assertAlmostEqual(result["midtone_share"], 1.0)

    def test_contrast_black_on_white_is_21(self):
        path = self.png("bw.png", [[px("#000000"), px("#ffffff")]])
        result = self.run_json("contrast", path, "--a", "0,0,1,1", "--b", "1,0,1,1")
        self.assertAlmostEqual(result["ratio"], 21.0, delta=0.05)

    def test_derive_writes_five_images_that_round_trip(self):
        path = self.png("big.png", [[px("#c03020")] * 400] * 200)
        out = self.dir / "out"
        result = self.run_json("derive", path, "--out", out)
        names = sorted(Path(p).name for p in result["written"])
        self.assertEqual(names, ["cvd-deutan.png", "cvd-protan.png", "cvd-tritan.png", "grayscale.png", "thumb.png"])
        for p in result["written"]:
            w, h, rows = measure.read_png(p)
            self.assertEqual((len(rows), len(rows[0])), (h, w))
        w, h, _ = measure.read_png(str(out / "thumb.png"))
        self.assertLessEqual(max(w, h), 160)

    def test_cvd_keeps_white_and_black(self):
        path = self.png("bw.png", [[px("#000000"), px("#ffffff")]])
        self.run_json("derive", path, "--out", self.dir / "o")
        for kind in ("protan", "deutan", "tritan"):
            _, _, rows = measure.read_png(str(self.dir / "o" / f"cvd-{kind}.png"))
            self.assertEqual(rows[0][0][:3], (0, 0, 0))
            for c in rows[0][1][:3]:
                self.assertGreaterEqual(c, 253)

    def test_sheet_tiles_frames(self):
        colours = ["#ff0000", "#00ff00", "#0000ff", "#ffff00"]
        frames = [self.png(f"f{i}.png", [[px(c)] * 2] * 2) for i, c in enumerate(colours)]
        out = self.dir / "sheet.png"
        result = self.run_json("sheet", *frames, "--out", out, "--cols", 2)
        self.assertEqual(result["frames"], 4)
        w, h, rows = measure.read_png(str(out))
        self.assertEqual((w, h), (4, 4))
        self.assertEqual(rows[0][3], px("#00ff00"))
        self.assertEqual(rows[3][0], px("#0000ff"))


class BadInput(MeasureCase):
    def test_unsupported_png_exits_2(self):
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

        deep = self.dir / "deep.png"
        ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 2, 0, 0, 0)
        deep.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IEND", b""))
        text = self.dir / "text.png"
        text.write_text("not a png")
        for path in (deep, text):
            with self.subTest(path=path.name):
                code, _, err = self.run_cli("values", path)
                self.assertEqual(code, 2)
                self.assertTrue(err.startswith("measure:"), err)
        code, _, err = self.run_cli("values", self.dir / "missing.png")
        self.assertEqual(code, 2)


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def filter_line(ftype, line, prev, bpp):
    """Independent tiny PNG encoder for one scanline."""
    out = bytearray()
    for i, x in enumerate(line):
        a = line[i - bpp] if i >= bpp else 0
        b = prev[i]
        c = prev[i - bpp] if i >= bpp else 0
        pred = [0, a, b, (a + b) // 2, paeth(a, b, c)][ftype]
        out.append((x - pred) & 255)
    return bytes([ftype]) + bytes(out)


def encode(width, height, ctype, raster, ftypes, extra=()):
    """raster: list of byte rows; ftypes: filter type per row. extra: (kind, data) chunks before IDAT."""
    bpp = CHANNELS[ctype]
    data, prev = b"", bytes(width * bpp)
    for line, ft in zip(raster, ftypes):
        data += filter_line(ft, line, prev, bpp)
        prev = line
    ihdr = struct.pack(">IIBBBBB", width, height, 8, ctype, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + b"".join(chunk(k, d) for k, d in extra)
            + chunk(b"IDAT", zlib.compress(data)) + chunk(b"IEND", b""))


CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4, 3: 1}


class Decoder(MeasureCase):
    def test_every_filter_type_decodes_bit_exact_for_every_colour_type(self):
        w, h = 5, 5
        for ctype, n in ((0, 1), (2, 3), (4, 2), (6, 4)):
            raster = [bytes((x * 37 + y * 91 + k * 53) % 256 for x in range(w) for k in range(n)) for y in range(h)]
            for ft in range(5):
                with self.subTest(colour_type=ctype, filter=ft):
                    path = self.dir / "f.png"
                    path.write_bytes(encode(w, h, ctype, raster, [ft] * h))
                    rw, rh, rows = measure.read_png(str(path))
                    self.assertEqual((rw, rh), (w, h))
                    for y in range(h):
                        for x in range(w):
                            v = raster[y][x * n:(x + 1) * n]
                            want = {0: lambda: (v[0], v[0], v[0], 255), 2: lambda: (*v, 255),
                                    4: lambda: (v[0], v[0], v[0], v[1]), 6: lambda: tuple(v)}[ctype]()
                            self.assertEqual(rows[y][x], want)

    def test_mixed_filters_per_row(self):
        raster = [bytes((x * 29 + y * 7) % 256 for x in range(12)) for y in range(5)]
        path = self.dir / "m.png"
        path.write_bytes(encode(4, 5, 2, raster, [4, 3, 2, 1, 0]))
        _, _, rows = measure.read_png(str(path))
        self.assertEqual(rows[3][2], (*raster[3][6:9], 255))

    def test_palette_with_transparency(self):
        plte = bytes([10, 20, 30, 200, 100, 50, 0, 255, 0])
        raster = [bytes([0, 1, 2]), bytes([2, 1, 0])]
        path = self.dir / "p.png"
        path.write_bytes(encode(3, 2, 3, raster, [4, 1], extra=[(b"PLTE", plte), (b"tRNS", bytes([128, 7]))]))
        _, _, rows = measure.read_png(str(path))
        self.assertEqual(rows[0], [(10, 20, 30, 128), (200, 100, 50, 7), (0, 255, 0, 255)])
        self.assertEqual(rows[1][0], (0, 255, 0, 255))


class Corrupt(MeasureCase):
    def assert_exits_2(self, *argv):
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 2, err)
        self.assertTrue(err.startswith("measure:"), err)

    def good_bytes(self):
        return Path(self.png("ok.png", [[px("#102030")] * 4] * 4)).read_bytes()

    def test_truncated_files_exit_2(self):
        good = self.good_bytes()
        for cut in (12, 20, 30, 40, len(good) - 20):
            with self.subTest(cut=cut):
                path = self.dir / "cut.png"
                path.write_bytes(good[:cut])
                self.assert_exits_2("values", path)

    def test_empty_image_data_exits_2(self):
        ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
        path = self.dir / "empty.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"")) + chunk(b"IEND", b""))
        self.assert_exits_2("values", path)

    def test_unwritable_output_exits_2(self):
        src = self.png("a.png", [[px("#102030")] * 2] * 2)
        blocker = self.dir / "file"
        blocker.write_text("x")
        self.assert_exits_2("derive", src, "--out", blocker / "sub")
        self.assert_exits_2("sheet", src, "--out", self.dir / "nodir" / "s.png")


if __name__ == "__main__":
    unittest.main()
