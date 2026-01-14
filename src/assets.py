from pathlib import Path
import subprocess
import sys
import argparse
from typing import Union

"""
assets.py

Create game assets by applying age-appropriate prompt modifiers to template images
and invoking an external image-synthesis CLI:
python examples/image_synthesis/sd_text_to_image_ppd.py --input_image dog.jpg --radius 1 --prompt "A pencil sketch of a dog" --output output.png
"""


# configurable locations
TEMPLATES_DIR = Path("templates")
OUTPUTS_DIR = Path("outputs")
SYNTH_SCRIPT = Path("image_synthesis/sd_text_to_image_ppd.py")


def list_templates(templates_dir: Path = TEMPLATES_DIR):
    templates_dir.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in templates_dir.iterdir() if p.is_file())


def generate_prompt_with_gpt4all(traits: dict, filename: str, model: str | None = None, max_tokens: int = 40, timeout: int = 10):
    """Generate a short image prompt using a local GPT4All model.

    Returns a one-line prompt like: "a pencil sketch of a dog".
    If gpt4all is not available or fails, falls back to `generate_prompt`.
    """
    try:
        from gpt4all import GPT4All
    except Exception:
        # gpt4all not installed — fall back
        raise ImportError("gpt4all package not available")

    try:
        model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf") # downloads / loads a 4.66GB LLM
    except Exception:
        # model not found or cannot be loaded — fall back
        raise RuntimeError(f"Failed to load GPT4All model")
    # Build instruction for concise prompt generation
    system = (
        "You are a brief prompt writer for a video game.\n"
        "Given a filename and simple player traits, produce a short image description that would be used as an asset in the game. Do understand that the object in the image is whatever the filename says so write the prompt accordingly.\n"
        "Output only a prompt that describes the object."
    )
    user = f"Filename: {filename}\n Player Traits: {traits}\nRespond with a short descriptive prompt." 
    prompt = system + "\n" + user
    try:
       with model.chat_session():
            response = model.generate(prompt, max_tokens=1024)
            return response
    except Exception:
        pass

    # Final fallback to local generator
    raise RuntimeError("GPT4All prompt generation failed")


def create_asset(
    template_path: Path,
    prompt_override: str = None,
    traits: dict | None = None,
    gpt_model: str | None = None,
    radius: int = 1,
    output_path: Path = None,
):
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = OUTPUTS_DIR / f"{template_path.stem}.png"
    # Decide prompt source: explicit override -> GPT (if enabled) -> local generator
    if prompt_override is not None:
        prompt = prompt_override
        print("Using overridden prompt:", prompt)
    else:
        prompt = generate_prompt_with_gpt4all(traits or {}, template_path.name, model=gpt_model)
        print("Generated prompt:", prompt)
    cmd = [
        sys.executable,
        str(SYNTH_SCRIPT),
        "--input_image",
        str(template_path),
        "--radius",
        str(radius),
        "--prompt",
        prompt,
        "--output_name",
        str(output_path),
    ]
    # run external synthesis script and stream its output to the terminal
    # (do not capture output so progress bars/logs are visible)
    res = subprocess.run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Image synthesis failed (rc={res.returncode})")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Create game assets from templates.")
    parser.add_argument("--list-templates", action="store_true", help="List available template files.")
    parser.add_argument("--template", type=str, help="Template filename inside templates/ to use.")
    parser.add_argument("--prompt", type=str, help="Override prompt text.")
    parser.add_argument("--radius", type=int, default=1, help="Radius parameter passed to synthesis script.")
    parser.add_argument("--output", type=str, help="Output filename (optional).")
    args = parser.parse_args()

    if args.list_templates:
        for t in list_templates():
            print(t)
        return

    if not args.template:
        parser.error("Missing --template (use --list-templates to see available).")

    template_path = TEMPLATES_DIR / args.template
    output_path = Path(args.output) if args.output else None
    try:
        out = create_asset(template_path, prompt_override=args.prompt, radius=args.radius, output_path=output_path)
        print(f"Created asset: {out}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


def get_template_path(template_name: str) -> Path:
    return TEMPLATES_DIR / template_name



def create_assets_for_all(
    input_folder: Path | str = TEMPLATES_DIR,
    prompt: str | None = None,
    traits: dict | None = None,
    gpt_model: str | None = None,
    radius: int = 1,
    prompt_overrides: dict = None,
    output_dir: Path = None,
):
    """Create assets for all image files in `input_folder`.

    If `prompt` is provided, it will be used for every image. By default
    GPT4All is used to generate prompts (`use_gpt=True`) when available; if
    GPT4All is unavailable the function falls back to the local
    `generate_prompt` behavior.
    """
    input_folder = Path(input_folder)
    if not input_folder.exists() or not input_folder.is_dir():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")
    prompt_overrides = prompt_overrides or {}
    outputs = []
    for file in sorted(p for p in input_folder.iterdir() if p.is_file()):
        # Decide which prompt to use: explicit `prompt` overrides everything;
        # otherwise prefer prompt_overrides[file] if present; then if GPT is
        # requested use the GPT generator with traits; finally fall back to
        # the local generator.
        if prompt is not None:
            per_prompt = prompt
        elif prompt_overrides and file.name in prompt_overrides:
            per_prompt = prompt_overrides[file.name]
        else:
            per_prompt = generate_prompt_with_gpt4all(traits or {}, file.name, model=gpt_model)
        out_path = None
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{file.stem}.png"
        created = create_asset(
            file,
            prompt_override=per_prompt,
            radius=radius,
            output_path=out_path,
        )
        outputs.append(Path(created))
    return outputs



__all__ = [
    "list_templates",
    "get_template_path",
    "generate_prompt",
    "create_asset",
    "create_assets_for_all",
]