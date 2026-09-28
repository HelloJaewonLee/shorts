"""ffmpeg 실행 도우미. 시스템 ffmpeg가 없으면 imageio-ffmpeg 번들 바이너리를 쓴다."""
import re
import shutil
import subprocess


def ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def run(args: list[str]) -> None:
    cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", *args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg 실패:\n{res.stderr[-3000:]}")


def probe(path: str) -> dict:
    """길이, 해상도, 오디오 유무. ffprobe 없이 ffmpeg -i 출력으로 읽는다."""
    res = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", path], capture_output=True, text=True)
    err = res.stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if not m:
        raise RuntimeError(f"영상 정보를 읽을 수 없음: {path}")
    h, mi, s = m.groups()
    info = {"duration": int(h) * 3600 + int(mi) * 60 + float(s), "has_audio": "Audio:" in err}
    v = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", err)
    info["width"], info["height"] = (int(v.group(1)), int(v.group(2))) if v else (0, 0)
    return info
