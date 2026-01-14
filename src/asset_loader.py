from pathlib import Path
import pygame


def load_images_from_folder(folder: str, alpha: bool):
    images = []
    path = Path(folder)

    if not path.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    for file in sorted(path.iterdir()):
        if file.suffix.lower() in (".png", ".jpg", ".jpeg"):
            img = pygame.image.load(file)
            img = img.convert_alpha() if alpha else img.convert()
            images.append(img)

    if not images:
        raise RuntimeError(f"No images found in {folder}")

    return images
