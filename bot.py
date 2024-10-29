import datetime
import io
import pytz
from PIL import Image, ImageDraw, ImageFont
from atproto import Client, models
from dotenv import load_dotenv
import os

load_dotenv()
client = Client()
client.login(os.getenv("HANDLE"), os.getenv("PASSWORD"))
BASE = os.path.dirname(os.path.realpath(__file__))


def get_year_progress():
    """Calculates the progress of the current year in GMT as a percentage."""

    # Get the current datetime in GMT timezone
    now_gmt = datetime.datetime.now(pytz.timezone("Etc/GMT"))

    # Get the start and end dates of the current year in GMT
    start_of_year = now_gmt.replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end_of_year = now_gmt.replace(
        month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
    )

    # Calculate the total seconds in the year
    total_seconds_in_year = (end_of_year - start_of_year).total_seconds()

    # Calculate the elapsed seconds since the start of the year
    elapsed_seconds = (now_gmt - start_of_year).total_seconds()

    # Calculate the percentage progress of the year
    year_progress = (elapsed_seconds / total_seconds_in_year) * 100

    return year_progress


def generate_progress_bar_text(progress):
    """Generates a progress bar based on the given progress percentage.

    Args:
        progress: The progress percentage (0-100).

    Returns:
        A string representing the progress bar.
    """

    bar_length = 20
    filled_length = int(bar_length * progress / 100)
    empty_length = bar_length - filled_length

    return "▓" * filled_length + "░" * empty_length + f" {progress:.2f}%"


def generate_progress_bar_image(progress):
    """Generates an image with a progress bar and text.

    Args:
        progress: The progress percentage (0-100).

    Returns:
        A PIL Image object.
    """

    # Image dimensions
    width = 1500
    height = 500

    # Create a new image with a blue background
    image = Image.new("RGB", (width, height), (60, 130, 245))

    # Create a drawing context
    draw = ImageDraw.Draw(image)

    # Font for the progress bar text
    font = ImageFont.truetype(os.path.join(BASE, "pacifico.ttf"), 64)
    bar_width = 1100
    bar_thickness = 15

    # Calculate the filled and empty parts of the progress bar
    filled_width = int(bar_width * progress / 100)

    bar_start_x = (width - bar_width) / 2
    bar_end_x = bar_start_x + filled_width
    bar_start_y = (height - bar_thickness) / 2
    bar_end_y = (height + bar_thickness) / 2

    empty_start_x = bar_end_x
    empty_end_x = (width + bar_width) / 2

    # Draw the progress bar
    draw.rounded_rectangle(
        [(bar_start_x, bar_start_y), (bar_start_x + filled_width, bar_end_y)],
        5,
        corners=(True, False, False, True),
        fill=(255, 255, 255),
    )
    draw.rounded_rectangle(
        [(empty_start_x, bar_start_y), (empty_end_x, bar_end_y)],
        5,
        corners=(False, True, True, False),
        fill=(200, 200, 200),
    )

    # Draw the text below the progress bar
    progress_text = f"{progress:.2f}%"
    _, _, w, _ = draw.textbbox((0, 0), progress_text, font=font)

    draw.text(
        ((width - w) / 2, bar_end_y + 20),
        progress_text,
        fill=(255, 255, 255),
        font=font,
        align="center",
    )

    return image


def post_to_bluesky(progress):
    client.send_post(text=generate_progress_bar_text(progress))


def update_bluesky_banner(image):
    blob = client.com.atproto.repo.upload_blob(image).blob
    current_profile_record = client.app.bsky.actor.profile.get(client.me.did, "self")
    current_profile = current_profile_record.value
    swap_record_cid = current_profile_record.cid
    client.com.atproto.repo.put_record(
        models.ComAtprotoRepoPutRecord.Data(
            collection=models.ids.AppBskyActorProfile,
            repo=client.me.did,
            rkey="self",
            swap_record=swap_record_cid,
            record=models.AppBskyActorProfile.Record(
                avatar=current_profile.avatar,
                banner=blob,
                description=current_profile.description,
                display_name=current_profile.display_name,
            ),
        )
    )


# Example usage:
progress = get_year_progress()
image = generate_progress_bar_image(progress)
img_byte_arr = io.BytesIO()
image.save(img_byte_arr, format="PNG")
img_byte_arr = img_byte_arr.getvalue()
update_bluesky_banner(img_byte_arr)
post_to_bluesky(progress)
