from assets import create_asset
from pathlib import Path

# Example usage:
# outs_all = create_assets_for_all(prompt_overrides={"all:": "A pencil sketch of a dog"}, radius=4)
# outs_all_old = create_asset_old(input_image="templates/dog_1.jpg", prompt="A pencil sketch of a dog", radius=10)
# print("Created assets old:", outs_all_old)
# outs_all = create_asset(template_path=Path("templates/dog_1.jpg"), traits={"age":"23", "likes":"golden retrievers", "dislikes":"black dogs"}, output_path=Path("outputs/gpt_test2.jpg"), radius=15)
# outs_all = create_asset(template_path=Path("templates/test1.jpg"), prompt_override="A high quality scene from a movie captured by a professional camera. A very beautiful woman stands in a rugged cave-like environment with stone walls and patches of snow. She has an adventurous appearance, wearing a sleeveless top, shorts, gloves, and a utility belt, exuding a determined and alert expression as if ready to explore or face a challenge", output_path=Path("outputs/gpt_test2.jpg"), radius=100)
outs_all = create_asset(template_path=Path("templates/256_Dirt Cracked 01.png"), prompt_override="a 2D Pixel Art game asset representing sand texture from bird's eye view", output_path=Path("outputs/sand_test_2.jpg"), radius=10)

print("Created assets:", outs_all)
