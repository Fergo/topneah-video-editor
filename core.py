"""Topneah Video APP - motor de video (FFmpeg).

Regras de qualidade:
  * Cortar  = copia direta (-c copy), sem recodificar.
  * Mesclar = concat demuxer com -c copy (se os trechos forem compativeis).
  * Audio   = copia da faixa original quando possivel.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Optional

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
ProgressCb = Optional[Callable[[float], None]]


class VideoError(Exception):
    pass


# --------------------------------------------------------------------------
# Localizar ffmpeg / ffprobe
# --------------------------------------------------------------------------
def find_ffmpeg() -> str:
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise VideoError(
            "FFmpeg nao encontrado. Rode: pip install imageio-ffmpeg "
            "(ou instale o FFmpeg e coloque no PATH)."
        )


def find_ffprobe() -> Optional[str]:
    return shutil.which("ffprobe")


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        creationflags=CREATE_NO_WINDOW, **kw,
    )


# --------------------------------------------------------------------------
# Informacoes do video
# --------------------------------------------------------------------------
@dataclass
class AudioTrack:
    index: int            # indice entre as faixas de audio (0,1,..)
    codec: str
    channels: int
    sample_rate: int
    bit_rate: int
    title: str = ""


@dataclass
class VideoInfo:
    path: str
    duration: float
    vcodec: str
    width: int
    height: int
    fps: float
    pix_fmt: str
    vbitrate: int
    audio: list[AudioTrack] = field(default_factory=list)
    rotation: float = 0.0
    sample_aspect_ratio: float = 1.0

    def display_dimensions(self) -> tuple[float, float]:
        """Dimensions after pixel aspect correction and FFmpeg autorotation."""
        width, height = self.width * self.sample_aspect_ratio, float(self.height)
        if round(self.rotation / 90) % 2:
            width, height = height, width
        return width, height


    def signature(self) -> tuple:
        """Parametros que precisam ser iguais para juntar sem recodificar."""
        a = self.audio[0] if self.audio else None
        return (
            self.vcodec, self.width, self.height, round(self.fps, 2), self.pix_fmt,
            round(self.rotation % 360, 2), round(self.sample_aspect_ratio, 6),
            (a.codec, a.channels, a.sample_rate) if a else None,
        )

    def describe(self) -> str:
        a = self.audio[0] if self.audio else None
        w, h = self.display_dimensions()
        s = f"{self.vcodec.upper()} {w:g}x{h:g} {self.fps:.0f}fps"
        if self.vbitrate:
            s += f" {self.vbitrate / 1e6:.1f} Mbps"
        if a:
            s += f" | {a.codec.upper()} {a.sample_rate // 1000}kHz"
            if len(self.audio) > 1:
                s += f" ({len(self.audio)} faixas)"
        return s


def _frac(s: str) -> float:
    try:
        if "/" in s:
            n, d = s.split("/")
            return float(n) / float(d) if float(d) else 0.0
        if ":" in s:
            n, d = s.split(":")
            return float(n) / float(d) if float(d) else 0.0
        return float(s)
    except Exception:
        return 0.0


def probe(path: str) -> VideoInfo:
    ffprobe = find_ffprobe()
    if ffprobe:
        r = _run([ffprobe, "-v", "error", "-show_format", "-show_streams",
                  "-of", "json", path])
        if r.returncode != 0:
            raise VideoError(f"Nao consegui ler o video:\n{r.stderr.strip()}")
        d = json.loads(r.stdout)
        v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
        if not v:
            raise VideoError("O arquivo nao tem faixa de video.")
        audio = []
        for i, s in enumerate(x for x in d["streams"] if x["codec_type"] == "audio"):
            audio.append(AudioTrack(
                i, s.get("codec_name", "?"), int(s.get("channels", 2)),
                int(s.get("sample_rate", 48000)), int(s.get("bit_rate", 0) or 0),
                s.get("tags", {}).get("title", ""),
            ))
        rotation = float(v.get("tags", {}).get("rotate", 0) or 0)
        for side_data in v.get("side_data_list", []):
            if "rotation" in side_data:
                rotation = float(side_data["rotation"])
                break
        sar = _frac(v.get("sample_aspect_ratio", "1:1")) or 1.0
        return VideoInfo(
            path, float(d["format"].get("duration", v.get("duration", 0))),
            v.get("codec_name", "?"), int(v["width"]), int(v["height"]),
            _frac(v.get("avg_frame_rate", "0")) or _frac(v.get("r_frame_rate", "0")),
            v.get("pix_fmt", "?"), int(v.get("bit_rate", 0) or 0), audio, rotation, sar,
        )
    # --- sem ffprobe: le a saida de "ffmpeg -i"
    r = _run([find_ffmpeg(), "-hide_banner", "-i", path])
    t = r.stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", t)
    if not m:
        raise VideoError(f"Nao consegui ler o video:\n{t.strip()[-500:]}")
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    vm = re.search(r"Video: (\w+).*?, (\w+)[^,]*, (\d+)x(\d+)", t)
    if not vm:
        raise VideoError("O arquivo nao tem faixa de video.")
    fm = re.search(r"([\d.]+) fps", t)
    bm = re.search(r"bitrate: (\d+) kb/s", t)
    audio = []
    for i, am in enumerate(re.finditer(r"Audio: (\w+).*?, (\d+) Hz, (\w+)", t)):
        ch = 1 if am[3] == "mono" else 2
        audio.append(AudioTrack(i, am[1], ch, int(am[2]), 0))
    rotation_match = re.search(r"rotation of\s+(-?[\d.]+) degrees", t)
    if not rotation_match:
        rotation_match = re.search(r"rotate\s*:\s*(-?[\d.]+)", t)
    rotation = float(rotation_match[1]) if rotation_match else 0.0
    sar_match = re.search(r"\bSAR (\d+:\d+)", vm[0] + t[vm.end():].split("\n", 1)[0])
    sar = (_frac(sar_match[1]) if sar_match else 1.0) or 1.0
    return VideoInfo(path, dur, vm[1], int(vm[3]), int(vm[4]),
                     float(fm[1]) if fm else 30.0, vm[2],
                     int(bm[1]) * 1000 if bm else 0, audio, rotation, sar)


def _mp4_keyframes(path: str) -> list[float]:
    """Le so o 'moov' do MP4 (tabela de sync samples): instantaneo, sem ffprobe."""
    import struct

    def boxes(buf, start=0, end=None):
        end = len(buf) if end is None else end
        i = start
        while i + 8 <= end:
            size, typ = struct.unpack(">I4s", buf[i:i + 8])
            hdr = 8
            if size == 1:
                size = struct.unpack(">Q", buf[i + 8:i + 16])[0]
                hdr = 16
            elif size == 0:
                size = end - i
            if size < hdr:
                return
            yield typ.decode("latin1"), i + hdr, i + size
            i += size

    moov = None
    with open(path, "rb") as f:
        f.seek(0, 2)
        total = f.tell()
        pos = 0
        while pos + 8 <= total:
            f.seek(pos)
            h = f.read(16)
            size, typ = struct.unpack(">I4s", h[:8])
            hdr = 8
            if size == 1:
                size = struct.unpack(">Q", h[8:16])[0]
                hdr = 16
            elif size == 0:
                size = total - pos
            if size < hdr:
                break
            if typ == b"moov":
                f.seek(pos + hdr)
                moov = f.read(size - hdr)
                break
            pos += size
    if moov is None:
        return []

    for typ, a, b in boxes(moov):
        if typ != "trak":
            continue
        tk = {t: (x, y) for t, x, y in boxes(moov, a, b)}
        if "mdia" not in tk:
            continue
        md = {t: (x, y) for t, x, y in boxes(moov, *tk["mdia"])}
        hx = md["hdlr"][0]
        if moov[hx + 8:hx + 12] != b"vide":
            continue
        mx = md["mdhd"][0]
        ver = moov[mx]
        timescale = struct.unpack(">I", moov[mx + (12 if ver == 0 else 20):mx + (16 if ver == 0 else 24)])[0]
        minf = {t: (x, y) for t, x, y in boxes(moov, *md["minf"])}
        st = {t: (x, y) for t, x, y in boxes(moov, *minf["stbl"])}

        def table(name, fmt, size):
            if name not in st:
                return None
            x = st[name][0]
            n = struct.unpack(">I", moov[x + 4:x + 8])[0]
            return [struct.unpack(fmt, moov[x + 8 + k * size:x + 8 + (k + 1) * size]) for k in range(n)]

        stts = table("stts", ">II", 8)
        stss = table("stss", ">I", 4)
        ctts = table("ctts", ">Ii", 8)
        if stts is None:
            return []
        # dts de cada sample (so os que importam)
        wanted = sorted(x[0] for x in stss) if stss else None
        if wanted is None:
            return []
        dts_at: dict[int, int] = {}
        sample, t, wi = 1, 0, 0
        for count, delta in stts:
            while wi < len(wanted) and wanted[wi] < sample + count:
                dts_at[wanted[wi]] = t + (wanted[wi] - sample) * delta
                wi += 1
            t += count * delta
            sample += count
        off_at: dict[int, int] = {}
        if ctts:
            sample, wi = 1, 0
            for count, off in ctts:
                while wi < len(wanted) and wanted[wi] < sample + count:
                    off_at[wanted[wi]] = off
                    wi += 1
                sample += count
        return sorted((dts_at[k] + off_at.get(k, 0)) / timescale for k in wanted if k in dts_at)
    return []


def keyframes(path: str) -> list[float]:
    """Tempos (s) dos keyframes. Usado para o 'iman' do inicio do corte."""
    if path.lower().endswith((".mp4", ".m4v", ".mov")):
        try:
            out = _mp4_keyframes(path)
            if out:
                return out
        except Exception:
            pass
    ffprobe = find_ffprobe()
    if ffprobe:  # le so os pacotes (rapido)
        r = _run([ffprobe, "-v", "error", "-select_streams", "v:0",
                  "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", path])
        out = []
        for line in r.stdout.splitlines():
            parts = line.split(",")
            if len(parts) >= 2 and "K" in parts[1]:
                try:
                    out.append(float(parts[0]))
                except ValueError:
                    pass
        if out:
            return sorted(out)
    r = _run([find_ffmpeg(), "-hide_banner", "-skip_frame", "nokey", "-i", path,
              "-an", "-vf", "showinfo", "-f", "null", "-"])
    return sorted(float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr))


# --------------------------------------------------------------------------
# Execucao do ffmpeg com progresso
# --------------------------------------------------------------------------
def _run_ffmpeg(args: list[str], total: float, cb: ProgressCb = None,
                cancel: Optional[Callable[[], bool]] = None) -> None:
    cmd = [find_ffmpeg(), "-hide_banner", "-y", "-nostdin",
           "-progress", "pipe:1", "-nostats", *args]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8", errors="replace",
                         creationflags=CREATE_NO_WINDOW)
    # stderr em thread para nao travar o pipe
    import threading
    err: list[str] = []
    t = threading.Thread(target=lambda: err.append(p.stderr.read()), daemon=True)
    t.start()
    for line in p.stdout:
        if cancel and cancel():
            p.kill()
            raise VideoError("Cancelado.")
        if line.startswith("out_time_us=") and cb and total > 0:
            try:
                cb(min(1.0, int(line.split("=")[1]) / 1e6 / total))
            except ValueError:
                pass
    p.wait()
    t.join(timeout=2)
    if p.returncode != 0:
        msg = (err[0] if err else "").strip().splitlines()[-6:]
        raise VideoError("FFmpeg falhou:\n" + "\n".join(msg))
    if cb:
        cb(1.0)


def _fmt(t: float) -> str:
    return f"{max(t, 0):.3f}"


def unique_path(folder: str, name: str, ext: str) -> str:
    base = re.sub(r'[<>:"/\\|?*]+', "_", name).strip() or "video"
    p = os.path.join(folder, base + ext)
    n = 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{base}_{n}{ext}")
        n += 1
    return p


# --------------------------------------------------------------------------
# Configuracoes de exportacao
# --------------------------------------------------------------------------
QUALITY_LEVELS = ["Máxima", "Alta", "Média", "Baixa"]
_CRF_X264 = [16, 20, 24, 28]
_CQ_NVENC = [17, 21, 25, 29]


@dataclass
class ExportSettings:
    """mode='copy' = sem recodificar (qualidade identica). 'encode' = recodifica."""
    mode: str = "copy"
    height: Optional[int] = None      # 1080 / 720 / 480: limite do lado menor; nunca amplia
    fps: Optional[int] = None         # 60 / 30 / 24 (nunca aumenta o fps)
    quality: int = 1                  # indice em QUALITY_LEVELS
    max_mb: Optional[float] = None    # limite de tamanho final (MB)
    use_gpu: bool = True
    audio_kbps: int = 128


def target_dims(info: VideoInfo, s: ExportSettings) -> tuple[int, int, float]:
    # Resolution presets constrain the shorter side in either orientation.
    display_w, display_h = info.display_dimensions()
    short_side = min(display_w, display_h)
    scale = min(1.0, s.height / short_side) if s.height else 1.0
    w = max(2, int(round(display_w * scale / 2) * 2))
    h = max(2, int(round(display_h * scale / 2) * 2))
    fps = info.fps or 30.0
    if s.fps:
        fps = min(float(s.fps), fps)
    return w, h, fps


def plan_kbps(s: ExportSettings, duration: float) -> Optional[int]:
    """Taxa de video (kbps) para caber em max_mb; None = usar qualidade (CRF)."""
    if not s.max_mb or duration <= 0:
        return None
    total_kbit = s.max_mb * 8192 * 0.94          # margem de seguranca
    kbps = (total_kbit - s.audio_kbps * duration) / duration
    return max(150, int(kbps))


@lru_cache(maxsize=1)
def nvenc_available() -> bool:
    try:
        r = _run([find_ffmpeg(), "-hide_banner", "-v", "error", "-f", "lavfi", "-i",
                  "color=c=black:s=256x256:d=0.2", "-c:v", "h264_nvenc", "-f", "null", "-"])
        return r.returncode == 0
    except Exception:
        return False


def _video_codec_args(s: ExportSettings, kbps: Optional[int], gpu: bool) -> list[str]:
    q = max(0, min(s.quality, 3))
    if gpu:
        a = ["-c:v", "h264_nvenc", "-preset", "p5", "-profile:v", "high"]
        if kbps:
            a += ["-rc", "vbr", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.15)}k",
                  "-bufsize", f"{kbps * 2}k"]
        else:
            a += ["-rc", "vbr", "-cq", str(_CQ_NVENC[q]), "-b:v", "0"]
    else:
        a = ["-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high"]
        if kbps:
            a += ["-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.15)}k", "-bufsize", f"{kbps * 2}k"]
        else:
            a += ["-crf", str(_CRF_X264[q])]
    return a + ["-pix_fmt", "yuv420p"]


def _vf(info: VideoInfo, s: ExportSettings) -> str:
    w, h, fps = target_dims(info, s)
    # FFmpeg autorotates before filtering. Emit square pixels explicitly;
    # keeping the old SAR would make players stretch the scaled frame again.
    f = [f"scale={w}:{h}:flags=lanczos", "setsar=1"]
    if fps + 0.5 < (info.fps or fps):
        f.append(f"fps={fps:g}")
    f.append("format=yuv420p")
    return ",".join(f)


def _merge_vf(info: VideoInfo, width: int, height: int, fps: int) -> str:
    display_w, display_h = info.display_dimensions()
    scale = min(width / display_w, height / display_h)
    fit_w = min(width, max(2, int(round(display_w * scale / 2) * 2)))
    fit_h = min(height, max(2, int(round(display_h * scale / 2) * 2)))
    return (f"scale={fit_w}:{fit_h}:flags=lanczos,setsar=1,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p")


# --------------------------------------------------------------------------
# Cortar
# --------------------------------------------------------------------------
_KF_CACHE: dict[str, list[float]] = {}


def keyframes_cached(path: str) -> list[float]:
    key = f"{path}|{os.path.getmtime(path)}"
    if key not in _KF_CACHE:
        _KF_CACHE[key] = keyframes(path)
    return _KF_CACHE[key]


def snap_start(kfs: list[float], t: float, tol: float = 0.02) -> float:
    """Keyframe mais proximo de t, sem passar de t (tolerancia de 20 ms)."""
    best = 0.0
    for k in kfs:
        if k <= t + tol:
            best = k
        else:
            break
    return best


def cut(src: str, start: float, end: float, out: str, settings: Optional[ExportSettings] = None,
        cb: ProgressCb = None, cancel=None) -> None:
    s = settings or ExportSettings()
    if end <= start:
        raise VideoError("O fim do trecho precisa ser maior que o inicio.")
    maps = ["-map", "0:v:0", "-map", "0:a?"]

    if s.mode == "copy":
        # Copia direta so comeca em keyframe: alinha o inicio ao keyframe exato,
        # senao o ffmpeg recua para o keyframe anterior (ate 0,5 s a mais).
        start = snap_start(keyframes_cached(src), start)
        if end <= start:
            raise VideoError("O fim do trecho precisa ser maior que o inicio.")
        dur = end - start
        args = ["-ss", _fmt(start + 0.02), "-i", src, "-t", _fmt(dur), *maps,
                "-c", "copy", "-avoid_negative_ts", "make_zero",
                "-movflags", "+faststart", out]
        _run_ffmpeg(args, dur, cb, cancel)
        return

    # --- recodifica (resolucao / fps / qualidade / limite de tamanho)
    info = probe(src)
    dur = end - start
    kbps = plan_kbps(s, dur)
    gpu = s.use_gpu and nvenc_available()
    for attempt in range(3):
        try:
            args = ["-ss", _fmt(start), "-i", src, "-t", _fmt(dur), *maps,
                    "-vf", _vf(info, s), *_video_codec_args(s, kbps, gpu),
                    "-c:a", "aac", "-b:a", f"{s.audio_kbps}k", "-ac", "2",
                    "-movflags", "+faststart", out]
            _run_ffmpeg(args, dur, cb, cancel)
        except VideoError:
            if gpu:               # placa de video falhou: tenta pela CPU
                gpu = False
                continue
            raise
        # limite de tamanho: se passou, refaz uma vez com taxa menor
        if s.max_mb and kbps and os.path.getsize(out) > s.max_mb * 1024 * 1024 and attempt < 2:
            kbps = int(kbps * (s.max_mb * 1024 * 1024 / os.path.getsize(out)) * 0.93)
            continue
        return


# --------------------------------------------------------------------------
# Mesclar
# --------------------------------------------------------------------------
@dataclass
class Clip:
    src: str
    start: float
    end: float


class IncompatibleClips(VideoError):
    pass


def merge(clips: list[Clip], out: str, settings: Optional[ExportSettings] = None,
          allow_reencode: bool = False, cb: ProgressCb = None, cancel=None) -> bool:
    """Junta os trechos na ordem dada. Retorna True se foi sem perda."""
    if not clips:
        raise VideoError("Nenhum trecho selecionado.")
    s = settings or ExportSettings()
    infos = {c.src: probe(c.src) for c in clips}
    total = sum(c.end - c.start for c in clips)
    compatible = len({i.signature() for i in infos.values()}) == 1

    if s.mode == "copy" and not compatible and not allow_reencode:
        raise IncompatibleClips(
            "Os trechos tem formatos diferentes (codec/resolucao/fps/audio), "
            "entao nao da para juntar sem recodificar.")

    if s.mode == "copy" and compatible:
        tmp = tempfile.mkdtemp(prefix="topneah_")
        try:
            parts, done = [], 0.0
            for i, c in enumerate(clips):
                p = os.path.join(tmp, f"p{i:03d}.mp4")
                d = c.end - c.start
                cut(c.src, c.start, c.end, p, s,
                    cb=(lambda f, d=d, done=done: cb((done + f * d) / total * 0.9) if cb else None),
                    cancel=cancel)
                parts.append(p)
                done += d
            lst = os.path.join(tmp, "list.txt")
            with open(lst, "w", encoding="utf-8") as f:
                for p in parts:
                    f.write("file '" + p.replace("\\", "/").replace("'", r"'\''") + "'\n")
            _run_ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-map", "0:v:0",
                         "-map", "0:a?", "-c", "copy", "-movflags", "+faststart", out],
                        total, (lambda f: cb(0.9 + f * 0.1) if cb else None), cancel)
            return True
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # --- normaliza cada trecho e concatena (formatos diferentes ou recompressao)
    es = s if s.mode == "encode" else ExportSettings(mode="encode", quality=0, use_gpu=True)
    ref = infos[clips[0].src]
    w, h, fps = target_dims(ref, es)
    fps = round(fps) or 30
    kbps = plan_kbps(es, total)
    gpu = es.use_gpu and nvenc_available()
    # Encode each range independently so input EOF cannot truncate later ranges.
    with tempfile.TemporaryDirectory(prefix="topneah_merge_") as tmp:
        for attempt in range(3):
            try:
                parts, done = [], 0.0
                for i, c in enumerate(clips):
                    duration = c.end - c.start
                    part = os.path.join(tmp, f"p{i:03d}.mp4")
                    args = ["-ss", _fmt(c.start), "-i", c.src]
                    if not infos[c.src].audio:
                        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
                    args += ["-t", _fmt(duration), "-map", "0:v:0", "-map",
                             "0:a:0" if infos[c.src].audio else "1:a:0",
                             "-vf", _merge_vf(infos[c.src], w, h, fps),
                             *_video_codec_args(es, kbps, gpu), "-c:a", "aac",
                             "-b:a", f"{es.audio_kbps}k", "-ar", "48000", "-ac", "2", part]
                    _run_ffmpeg(args, duration,
                                (lambda f, done=done, d=duration: cb((done + f * d) / total * 0.9) if cb else None), cancel)
                    parts.append(part)
                    done += duration
                manifest = os.path.join(tmp, "list.txt")
                with open(manifest, "w", encoding="utf-8") as f:
                    for part in parts:
                        f.write("file '" + os.path.basename(part) + "'\n")
                _run_ffmpeg(["-f", "concat", "-safe", "0", "-i", manifest,
                             "-map", "0:v:0", "-map", "0:a:0", "-c", "copy",
                             "-movflags", "+faststart", out], total,
                            (lambda f: cb(0.9 + f * 0.1) if cb else None), cancel)
            except VideoError:
                if gpu:
                    gpu = False
                    continue
                raise
            if es.max_mb and kbps and os.path.getsize(out) > es.max_mb * 1024 * 1024 and attempt < 2:
                kbps = int(kbps * (es.max_mb * 1024 * 1024 / os.path.getsize(out)) * 0.93)
                continue
            return False
    raise VideoError("Não foi possível concluir a junção dos trechos.")


# --------------------------------------------------------------------------
# Audio
# --------------------------------------------------------------------------
# rotulo -> (tipo, extensao)
AUDIO_FORMATS = {
    "WhatsApp (m4a leve)": ("m4a-128", "m4a"),
    "Original (m4a sem perda)": ("m4a-copy", "m4a"),
    "MP3 (192 kbps)": ("mp3-192", "mp3"),
    "WAV (sem compressão)": ("wav", "wav"),
}


def extract_audio(src: str, start: float, end: float, out: str, kind: str,
                  track: int = 0, cb: ProgressCb = None, cancel=None) -> None:
    dur = end - start
    if dur <= 0:
        raise VideoError("O fim do trecho precisa ser maior que o inicio.")
    info = probe(src)
    if not info.audio:
        raise VideoError("Este video nao tem audio.")
    m = ["-map", f"0:a:{track}", "-vn"]
    if kind == "m4a-copy":
        codec = ["-c:a", "copy"] if info.audio[track].codec == "aac" else ["-c:a", "aac", "-b:a", "256k"]
    elif kind == "m4a-128":
        codec = ["-c:a", "aac", "-b:a", "128k", "-ac", "2"]
    elif kind == "mp3-192":
        codec = ["-c:a", "libmp3lame", "-b:a", "192k"]
    else:
        codec = ["-c:a", "pcm_s16le"]
    _run_ffmpeg(["-ss", _fmt(start), "-i", src, "-t", _fmt(dur), *m, *codec, out],
                dur, cb, cancel)
