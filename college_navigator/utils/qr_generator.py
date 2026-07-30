"""
utils/qr_generator.py
----------------------
Generates a QR code image for a given campus location.

Each QR code encodes a direct URL like:
    https://<your-domain>/navigate/<location_id>?source=qr

When scanned, the phone's camera app opens this URL directly in the
browser -> Flask serves the navigate page -> the page auto-requests
the visitor's live GPS position and draws the shortest route to that
location. No app installation needed.

Requires the `qrcode` and `Pillow` packages:
    pip install qrcode[pil] Pillow
"""

import os


def generate_qr(location_id: int, location_name: str, base_url: str, output_dir: str) -> str:
    """
    Generates and saves a QR code PNG for a location.

    Args:
        location_id: primary key of the location
        location_name: used only to build a readable filename
        base_url: e.g. "http://127.0.0.1:5000" or your production domain
        output_dir: folder to save the PNG into (static/qrcodes)

    Returns:
        The relative file path of the saved PNG.
    """
    # Imported lazily so the rest of the app still runs even before
    # `pip install qrcode[pil]` has been done — only QR generation
    # requires it.
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    os.makedirs(output_dir, exist_ok=True)

    target_url = f"{base_url}/navigate/{location_id}?source=qr"

    qr = qrcode.QRCode(
        version=None,               # auto-size
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    safe_name = "".join(c if c.isalnum() else "_" for c in location_name.lower())
    filename = f"qr_{location_id}_{safe_name}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)

    return filepath, target_url
