import asyncio
import logging
import os
import re
import subprocess
from urllib.parse import urlparse

import aiofiles
from aiohttp import ClientSession

IMAGES_DIR = 'downloaders/tiktok/tiktok_slideshow/images'
RESULTS_DIR = 'downloaders/tiktok/tiktok_slideshow/results'
TRANSITION_TYPE = 'slideleft'
# FASTER_TRANSITION = 'wipeleft'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, image/avif, image/webp, image/apng, */*; '
              'q=0.8',
    'Accept-Language': 'ru-RU, ru;q=0.7'
}


async def download_slideshow(data: dict) -> str:
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    output_file = data['id'] + '.mp4'
    output_file = os.path.join(RESULTS_DIR, output_file)
    output_file = str(output_file)
    audio = data['play']
    audio_duration = int(data['music_info']['duration'])
    images = data['images']
    if len(images) > 1:
        async with ClientSession(headers=HEADERS) as session:
            tasks = [asyncio.create_task(download_image(image, session)) for image in images]
            download_images = list(await asyncio.gather(*tasks))
        await asyncio.sleep(0.25)
        create_slideshow(download_images, audio, audio_duration, output_file)
        [os.remove(image) for image in download_images]
    else:
        create_video(images[0], audio, output_file)
    return output_file


def create_slideshow(images: list, audio_file: str, audio_duration: int, output_file: str) -> None:
    image_duration = 3
    transition_duration = 0.5
    input_image_count = len(images)
    output_image_count = int(round(audio_duration / image_duration))
    if output_image_count < input_image_count:
        image_duration = audio_duration / input_image_count
    else:
        images = repeat_elements(images, output_image_count)

    max_width, max_height = get_max_dimensions(images)

    result = ['ffmpeg', '-y', '-threads', '1']
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
        '-crf', '18'
    ]
    result += [output_file, '-async', '1']
    execute_command(result)


async def download_image(url: str, session: ClientSession) -> str:
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    filename = urlparse(url).path.strip('/').split('/')[-1]
    filename = re.sub(r'[/:*?"<>|]', '_', filename).strip()
    file_path = os.path.join(IMAGES_DIR, filename)
    async with session.get(url) as response:
        async with aiofiles.open(file_path, 'wb') as f:
            async for chunk, _ in response.content.iter_chunks():
                await f.write(chunk)
    await asyncio.sleep(0.25)
    return file_path


def repeat_elements(input_list: list, n: int) -> list:
    return (input_list * ((n // len(input_list)) + 1))[:n]


def create_video(image: str, audio_file: str, output_file: str) -> None:
    result = [
        'ffmpeg',
        '-y',
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
        output_file,
        '-async', '1'
    ]
    execute_command(result)


def get_max_dimensions(images: list) -> tuple:
    max_width = 0
    max_height = 0
    for image in images:
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of',
                                 'default=noprint_wrappers=1:nokey=1', image],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        width, height = map(int, result.stdout.decode().split())
        if width > max_width:
            max_width = width
        if height > max_height:
            max_height = height
    return max_width, max_height


def execute_command(command: list) -> None:
    try:
        subprocess.run(command)
    except Exception as e:
        logging.error(e)
