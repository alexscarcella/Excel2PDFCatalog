import random
from PIL import Image, ImageDraw
from pathlib import Path
from app.logger import logger


def generate_image(size=400, num_shapes=10, file_name="xxx"):
    # Crea immagine bianca
    logger.info(f"Build image {file_name} - {size}x{size}")
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    for _ in range(num_shapes):
        img2 = disegna_blob(size)
        img.paste(img2.convert("RGB"), mask=img2)

    img.save(f"{file_name}")

def disegna_blob(size):
    img = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(img, "RGBA")
    # fisso il centro del bloc e mi tengo lontano dal bordo di 100px
    base_x, base_y = random.randint(100, size-100), random.randint(100, size-100) 
    color = (
        random.randint(50, 255),
        random.randint(50, 255),
        random.randint(50, 255),
        125 # Alpha 
    )
    # credo una serie di ellissi sovrapposte
    for _ in range(random.randint(5, 15)):
        dx, dy = random.randint(-50, 50), random.randint(-50, 50)
        r = random.randint(20, 50) # rotazione dell'ellisse
        # fisso il centro delle ellissi con base_@, poi lo sposto r+d@
        draw.ellipse([base_x+dx-r, base_y+dy-r, base_x+dx+r, base_y+dy+r], fill=color, outline=None)
    
    return img

def resize_image(img, size_x, size_y):
    new_img = img.resize((size_x, size_y), Image.LANCZOS)
    return new_img


def load_image_path(image_base_path):
    """
    Carica un'immagine cercando prima .png, poi .jpg, poi .jpeg
    
    Args:
        percorso_base: path senza estensione, es. "immagini/foto"
    
    Returns:
        Image path se trovato, None altrimenti
    """
    path_base = Path(image_base_path)
    for ext in ['.png', '.jpg', '.jpeg']:
        complete_path = path_base.with_suffix(ext)
        if complete_path.exists():
            return complete_path
    return None