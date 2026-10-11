# app/services/image_validator.py
from datetime import datetime, date, timedelta
from fastapi import HTTPException, status
from PIL import Image
from PIL.ExifTags import TAGS

def verify_image_metadata(image_path: str) -> None:
    """
    Extracts EXIF metadata from the uploaded image. 
    If DateTimeOriginal exists, ensures it matches today's date.
    """
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return  # Allow images with stripped EXIF (e.g. some web uploads), but log/pass

            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    # EXIF format is typically 'YYYY:MM:DD HH:MM:SS'
                    date_str = value.split(" ")[0].replace(":", "-")
                    photo_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    if photo_date != date.today():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Fraud prevention: This photo was taken on {photo_date}, not today! Please take a fresh live photo."
                        )
    except HTTPException as he:
        raise he
    except Exception:
        # If EXIF parsing fails or format is unrecognized, allow submission to avoid false positives on compressed mobile images
        pass


def check_submission_cooldown(last_submission_time: datetime | None) -> None:
    """Enforces a 60-second cooldown between submissions to prevent spamming the AI engine."""
    if last_submission_time:
        # Ensure timezone-naive comparison or clean UTC delta
        elapsed = datetime.utcnow() - last_submission_time.replace(tzinfo=None)
        if elapsed < timedelta(seconds=60):
            wait_time = int(60 - elapsed.total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait_time} seconds before trying another submission."
            )