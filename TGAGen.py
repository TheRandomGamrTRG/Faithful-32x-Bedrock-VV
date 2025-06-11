import os
from PIL import Image
import numpy as np

FOLDER_16 = "./sprites/16x"
FOLDER_32 = "./sprites/32x"
OUTPUT_FOLDER = "./sprites/output"
LOG_FILE = os.path.join(OUTPUT_FOLDER, "skipped_sprites.txt")

def load_image_colors(image_path):
    img = Image.open(image_path).convert("RGBA")
    return np.array(img), set(img.getdata())

def get_color_mapping(png_array, tga_array):
    mapping = {}
    height, width = png_array.shape[:2]
    for y in range(height):
        for x in range(width):
            color = tuple(png_array[y, x][:3])  # Ignore alpha
            tga_val = tuple(tga_array[y, x])
            mapping[color] = tga_val
    return mapping

skipped = []
created_count = 0
skipped_count = 0

for root, dirs, files in os.walk(FOLDER_16):
    for file in files:
        if not file.endswith(".png"):
            continue

        rel_dir = os.path.relpath(root, FOLDER_16)
        base_name = file[:-4]

        path_png_16 = os.path.join(root, file)
        path_png_32 = os.path.join(FOLDER_32, rel_dir, file)

        if not os.path.exists(path_png_32):
            print(f"Skipping {os.path.join(rel_dir, file)}: 32x PNG not found.")
            skipped_count += 1
            continue

        arr_16, colors_16 = load_image_colors(path_png_16)
        arr_32, colors_32 = load_image_colors(path_png_32)

        colors_16_rgb = set(c[:3] for c in colors_16)
        colors_32_rgb = set(c[:3] for c in colors_32)
        new_colors = colors_32_rgb - colors_16_rgb

        if new_colors:
            print(f"Skipping {os.path.join(rel_dir, file)}: new colors found in 32x PNG.")
            skipped.append((os.path.join(rel_dir, base_name), new_colors))
            skipped_count += 1
            continue

        tga_folder = os.path.join(FOLDER_16, rel_dir)
        tga_variants = [f for f in os.listdir(tga_folder)
                        if f.startswith(base_name) and f.endswith(".tga")]

        if not tga_variants:
            print(f"No TGA files found for {os.path.join(rel_dir, base_name)}.")
            skipped_count += 1
            continue

        for tga_file in tga_variants:
            path_tga_16 = os.path.join(tga_folder, tga_file)
            img_tga_16 = Image.open(path_tga_16).convert("RGBA")
            arr_tga_16 = np.array(img_tga_16)

            if arr_16.shape != arr_tga_16.shape:
                print(f"Warning: size mismatch in {tga_file}, skipping.")
                skipped_count += 1
                continue

            color_to_tga = get_color_mapping(arr_16, arr_tga_16)

            h, w = arr_32.shape[:2]
            output_arr = np.zeros((h, w, 4), dtype=np.uint8)

            for y in range(h):
                for x in range(w):
                    color = tuple(arr_32[y, x][:3])
                    output_arr[y, x] = color_to_tga.get(color, (0, 0, 0, 0))

            out_dir = os.path.join(OUTPUT_FOLDER, rel_dir)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, tga_file)
            Image.fromarray(output_arr, mode="RGBA").save(out_path)
            print(f"Created: {out_path}")
            created_count += 1

# Write skipped log and summary
with open(LOG_FILE, "w") as log:
    log.write(f"Summary:\nTGAs created: {created_count}\nTGAs skipped: {skipped_count}\n\n")
    if skipped:
        log.write("Skipped sprites due to new colors:\n")
        for name, new_colors in skipped:
            log.write(f"{name} introduced {len(new_colors)} new colors:\n")
            for c in sorted(new_colors):
                log.write(f"  - {c}\n")
            log.write("\n")

print(f"\nSummary:\nTGAs created: {created_count}\nTGAs skipped: {skipped_count}")
print(f"Skipped sprites logged in: {LOG_FILE}")
