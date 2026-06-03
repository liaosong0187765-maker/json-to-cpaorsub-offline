from __future__ import annotations

from pathlib import Path


LINES_PER_FILE = 100
SUPPORTED_SUFFIXES = {".txt", ".json"}


def normalize_input_path(input_text: str) -> Path:
    input_file = Path(input_text).expanduser()
    if input_file.exists():
        return input_file

    try:
        fixed_text = input_text.encode("gbk").decode("utf-8")
    except UnicodeError:
        return input_file

    fixed_file = Path(fixed_text).expanduser()
    if fixed_file.exists():
        return fixed_file

    return input_file


def split_file(input_file: Path, lines_per_file: int = LINES_PER_FILE) -> Path:
    if lines_per_file <= 0:
        raise ValueError("lines_per_file must be greater than 0")

    input_file = input_file.expanduser().resolve()
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if input_file.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Only {supported} files are supported")

    output_dir = input_file.with_suffix("")
    output_dir.mkdir(exist_ok=True)

    part_index = 1
    line_index = 0
    output_file = None

    try:
        with input_file.open("r", encoding="utf-8-sig", newline="") as source:
            for line in source:
                if line_index % lines_per_file == 0:
                    if output_file is not None:
                        output_file.close()

                    part_path = output_dir / f"{input_file.stem}_{part_index:03d}{input_file.suffix}"
                    output_file = part_path.open("w", encoding="utf-8", newline="")
                    part_index += 1

                output_file.write(line)
                line_index += 1
    finally:
        if output_file is not None:
            output_file.close()

    if line_index == 0:
        part_path = output_dir / f"{input_file.stem}_001{input_file.suffix}"
        part_path.write_text("", encoding="utf-8")

    return output_dir


def main() -> None:
    input_text = input("请输入txt或json文件地址：").strip().strip('"')
    if not input_text:
        print("未输入文件地址，程序结束。")
        return

    try:
        output_dir = split_file(normalize_input_path(input_text))
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return

    print(f"完成。输出文件夹：{output_dir}")


if __name__ == "__main__":
    main()
