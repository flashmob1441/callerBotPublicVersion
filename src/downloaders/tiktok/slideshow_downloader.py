import os
import uuid
import asyncio
import tempfile
import aiofiles

from aiohttp import ClientSession
from urllib.parse import urlparse

IMAGES_DIR = 'downloaders/tiktok/tiktok_slideshow/images'
RESULTS_DIR = 'downloaders/tiktok/tiktok_slideshow/results'
TRANSITION_TYPE = 'slideleft'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, image/avif, image/webp, image/apng, */*; '
              'q=0.8',
    'Accept-Language': 'ru-RU, ru;q=0.7'
}


async def download_slideshow(data: dict) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    output_file = os.path.join(RESULTS_DIR, f"{data['id']}-{uuid.uuid4().hex[:8]}.mp4")
    audio = data['play']
    audio_duration = int(data['music_info']['duration'])
    images = data['images']
    try:
        if len(images) > 1:
            with tempfile.TemporaryDirectory(dir=IMAGES_DIR) as tmp_dir:
                async with ClientSession(headers=HEADERS) as session:
                    download_images = await asyncio.gather(*(
                        download_image(url, session, os.path.join(tmp_dir, f'{i}{os.path.splitext(urlparse(url).path)[1]}'))
                        for i, url in enumerate(images)
                    ))
                await create_slideshow(list(download_images), audio, audio_duration, output_file)
        else:
            await create_video(images[0], audio, output_file)
    except BaseException:
        if os.path.exists(output_file):
            os.remove(output_file)
        raise
    return output_file


async def create_slideshow(images: list, audio_file: str, audio_duration: int, output_file: str) -> None:
    image_duration = 3
    transition_duration = 0.5
    input_image_count = len(images)
    output_image_count = int(round(audio_duration / image_duration))
    if output_image_count < input_image_count:
        image_duration = audio_duration / input_image_count
    else:
        images = repeat_elements(images, output_image_count)

    max_width, max_height = await get_max_dimensions(images)

    result = ['ffmpeg', '-y', '-loglevel', 'error', '-threads', '1']
    filter_complex_parts = []
    xfade_parts = []

    for i, image in enumerate(images):
        result += ['-loop', '1', '-t', str(image_duration), '-framerate', '1', '-i', image]
        filter_complex_parts.append(
            f"[{i}:v]fps=25,scale={max_width - 1}:{max_height - 1}:force_original_aspect_ratio=decrease,setsar=sar=1/1,"
            f"pad={max_width}:{max_height}:(ow-iw)/2:(oh-ih)/2,format=yuvj420p[image{i}]"
        )

    for i in range(len(images) - 1):
        offset = (i + 1) * (image_duration - transition_duration)
        end_frame = f'[image{i + 1}]'
        if i == len(images) - 2:
            end_frame = ''
        xfade_parts.append(
            f'[image{i}][image{i + 1}]xfade=transition={TRANSITION_TYPE}:duration={transition_duration}:offset={offset}'
            f'{end_frame}'
        )

    filter_complex = "; ".join(filter_complex_parts + xfade_parts)
    result += [
        '-i', audio_file,
        '-filter_complex', f'{filter_complex}',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        '-movflags', 'faststart',
        '-preset', 'ultrafast',
        '-crf', '18',
        output_file
    ]
    await run_command(result)


async def download_image(url: str, session: ClientSession, file_path: str) -> str:
    async with session.get(url) as response:
        response.raise_for_status()
        async with aiofiles.open(file_path, 'wb') as f:
            async for chunk, _ in response.content.iter_chunks():
                await f.write(chunk)
    return file_path


def repeat_elements(input_list: list, n: int) -> list:
    return (input_list * ((n // len(input_list)) + 1))[:n]


async def create_video(image: str, audio_file: str, output_file: str) -> None:
    result = [
        'ffmpeg',
        '-y',
        '-loglevel', 'error',
        '-threads', '1',
        '-framerate', '1',
        '-i', image,
        '-i', audio_file,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        '-movflags', 'faststart',
        '-preset', 'fast',
        '-crf', '18',
        '-r', '25',
        output_file
    ]
    await run_command(result)


async def get_max_dimensions(images: list) -> tuple:
    max_width = 0
    max_height = 0
    for image in images:
        output = await run_command(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of',
                                   'default=noprint_wrappers=1:nokey=1', image])
        width, height = map(int, output.split())
        max_width = max(max_width, width)
        max_height = max(max_height, height)
    return max_width, max_height


async def run_command(command: list) -> str:
    process = await asyncio.create_subprocess_exec(*command,
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.STDOUT)
    output, _ = await process.communicate()
    text = output.decode(errors='replace')
    if process.returncode != 0:
        raise RuntimeError(f'{command[0]} exited with {process.returncode}: {text[-500:]}')
    return text
