"""Composite a MatAnyone2 alpha matte with an AI-generated background plate.

Takes the original foreground video and the alpha matte produced by
`inference_matanyone2.py` (either the `*_pha.mp4` video or a folder of
per-frame `pha/####.png` images saved with `--save_image`), blends it over
a background plate (a single image, held for the whole clip, or a video,
looped/trimmed to match length), and writes the result as an mp4.

    composite = fg * alpha + bg * (1 - alpha)

Usage:
    python composite.py \
        -f inputs/video/test-sample2.mp4 \
        -a results/test-sample2_pha.mp4 \
        -b path/to/ai_background.jpg \
        -o results/test-sample2_composite.mp4
"""
import os
import argparse

import cv2
import numpy as np
import imageio


def _is_video_file(path):
    return os.path.isfile(path) and os.path.splitext(path)[1].lower() in (".mp4", ".mov", ".avi", ".webm", ".mkv")


def read_frames(path):
    """Read a video file or a folder of frame images into a list of RGB uint8 arrays, plus fps."""
    if os.path.isdir(path):
        names = sorted(
            f for f in os.listdir(path)
            if os.path.splitext(f)[1].lower() in (".png", ".jpg", ".jpeg", ".bmp")
        )
        if not names:
            raise ValueError(f"No frame images found in folder: {path}")
        frames = []
        for name in names:
            img = cv2.imread(os.path.join(path, name), cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"Failed to read frame image: {os.path.join(path, name)}")
            frames.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return frames, None
    elif _is_video_file(path):
        reader = imageio.get_reader(path)
        meta = reader.get_meta_data()
        fps = meta.get("fps")
        frames = [np.asarray(frame)[..., :3] for frame in reader]
        reader.close()
        return frames, fps
    else:
        raise ValueError(f"Unsupported input, expected a video file or a folder of frame images: {path}")


def read_alpha_frames(path):
    """Read an alpha matte source (video or per-frame PNGs) into a list of float32 [0,1] (H,W) arrays."""
    frames, fps = read_frames(path)
    alphas = [frame.astype(np.float32).mean(axis=2) / 255.0 for frame in frames]
    return alphas, fps


def resize_to(frame, h, w):
    if frame.shape[0] == h and frame.shape[1] == w:
        return frame
    return cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)


def build_background_sequence(bg_path, n_frames, h, w):
    """Return a list of n_frames RGB uint8 background frames matching the target resolution.

    A still image is held for every frame; a video is looped (or trimmed) to length.
    """
    if _is_video_file(bg_path):
        bg_frames, _ = read_frames(bg_path)
        if len(bg_frames) == 0:
            raise ValueError(f"Background video has no frames: {bg_path}")
        out = [resize_to(bg_frames[i % len(bg_frames)], h, w) for i in range(n_frames)]
        return out
    else:
        img = cv2.imread(bg_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Failed to read background image: {bg_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = resize_to(img, h, w)
        return [img] * n_frames


def main(fg_path, alpha_path, bg_path, output_path, fps=None):
    fg_frames, fg_fps = read_frames(fg_path)
    alpha_frames, alpha_fps = read_alpha_frames(alpha_path)

    if len(fg_frames) != len(alpha_frames):
        raise ValueError(
            f"Foreground frame count ({len(fg_frames)}) does not match alpha frame count "
            f"({len(alpha_frames)}). Both must come from the same MatAnyone2 run."
        )

    h, w = fg_frames[0].shape[:2]
    bg_frames = build_background_sequence(bg_path, len(fg_frames), h, w)

    out_fps = fps or fg_fps or alpha_fps or 24
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    composited = []
    for fg, alpha, bg in zip(fg_frames, alpha_frames, bg_frames):
        fg = resize_to(fg, h, w).astype(np.float32)
        bg = bg.astype(np.float32)
        a = cv2.resize(alpha, (w, h), interpolation=cv2.INTER_LINEAR)[..., None]
        blended = fg * a + bg * (1 - a)
        composited.append(np.round(np.clip(blended, 0, 255)).astype(np.uint8))

    imageio.mimwrite(output_path, composited, fps=out_fps, quality=8)
    print(f"Wrote {len(composited)} composited frames to {output_path} ({w}x{h} @ {out_fps}fps)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-f", "--fg", required=True, help="Original foreground video, or a folder of frame images (same source used for inference).")
    parser.add_argument("-a", "--alpha", required=True, help="Alpha matte: the '*_pha.mp4' from inference_matanyone2.py, or a folder of per-frame pha PNGs (--save_image).")
    parser.add_argument("-b", "--bg", required=True, help="AI-generated background plate: a still image (held for the whole clip) or a video (looped/trimmed to match length).")
    parser.add_argument("-o", "--output", required=True, help="Output composited video path (mp4).")
    parser.add_argument("--fps", type=float, default=None, help="Override output fps. Defaults to the foreground video's fps.")
    args = parser.parse_args()

    main(fg_path=args.fg, alpha_path=args.alpha, bg_path=args.bg, output_path=args.output, fps=args.fps)
