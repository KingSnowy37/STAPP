from pathlib import Path

from PIL import Image, ImageDraw


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "screentime.ico"


def create_icon() -> None:
    canvas_size = 256
    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Warm clock mark designed to remain legible at Windows tray-icon sizes.
    draw.rounded_rectangle(
        (18, 18, 238, 238),
        radius=58,
        fill=(184, 92, 56, 255),
    )
    draw.ellipse((62, 62, 194, 194), fill=(255, 248, 241, 255))
    draw.ellipse((76, 76, 180, 180), outline=(64, 40, 28, 255), width=8)
    draw.line((128, 128, 128, 92), fill=(184, 92, 56, 255), width=12)
    draw.line((128, 128, 158, 146), fill=(184, 92, 56, 255), width=12)
    draw.ellipse((117, 117, 139, 139), fill=(64, 40, 28, 255))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        OUTPUT_PATH,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    create_icon()
