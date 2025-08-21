from django.conf import settings
import os
import uuid
import numpy as np
import cv2, base64



def save_fingerprints(fingerprints, order_id):
    """Decode base64 strings and save as PNG files"""
    saved_files = {}
    folder = os.path.join(settings.MEDIA_ROOT, "fingerprints", str(order_id))
    os.makedirs(folder, exist_ok=True)

    for finger, data in fingerprints.items():
        if data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            filename = f"{finger}_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(imgstr))
            saved_files[finger] = f"fingerprints/{order_id}/{filename}"
        else:
            saved_files[finger] = data
    return saved_files

def enhance_fingerprint(base64_str):
    try:
        # 1. Decode base64 → NumPy grayscale
        image_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        # 2. Resize to max 500px (for speed)
        MAX_SIZE = 500
        h, w = img.shape
        if max(h, w) > MAX_SIZE:
            scale = MAX_SIZE / max(h, w)
            img = cv2.resize(img, (int(w*scale), int(h*scale)))

        # 3. Contrast enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        img = clahe.apply(img)

        # 4. Binarization (Otsu threshold)
        _, img_bin = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Ensure ridges are white (255), background black (0)
        img_bin = 255 - img_bin

        # 5. Skeletonization (OpenCV thinning, much faster than skimage)
        skeleton = cv2.ximgproc.thinning(img_bin, thinningType=cv2.ximgproc.THINNING_GUOHALL)

        # 6. Encode back to base64
        _, buffer = cv2.imencode(".png", skeleton)
        return base64.b64encode(buffer).decode("utf-8")

    except Exception as e:
        return base64_str