import io
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TypeVar

from PIL import Image

# file_extensions: list[str] = ["GIF", "JPEG", "JPG", "PNG", "jpeg", "jpg", "png", "svg"]


class FileExtension(Enum):
    GIF = "gif"
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    SVG = "svg"


SelfFile = TypeVar("SelfFile", bound="File")


@dataclass
class File:
    file_path: Path
    file_size: float
    file_extension: FileExtension
    new_file: SelfFile | None = None


class ProcessFile(ABC):
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def get_file_metadata(self) -> File:
        return File(
            file_path=self.file_path,
            file_size=self.file_path.stat().st_size,
            file_extension=FileExtension(self.file_path.suffix[1:].lower()),
        )

    @abstractmethod
    def compress_file(self) -> File:
        pass

    @abstractmethod
    def save_file(self) -> None:
        pass


class ProcessImage(ProcessFile):
    def compress_file(self) -> File:
        metadata: File = self.get_file_metadata()
        if metadata.file_extension in [FileExtension.SVG, FileExtension.PNG]:
            return metadata
        if metadata.file_size > 20 * 1024:
            with Image.open(self.file_path) as img:
                if img.mode == "P" or img.mode == "RGBA":
                    img = img.convert("RGB")
                for iteration in range(1, 6):
                    output = io.BytesIO()
                    save_format = (
                        "JPEG"
                        if metadata.file_extension == FileExtension.JPG
                        else metadata.file_extension.value.upper()
                    )
                    img.save(
                        output,
                        format=save_format,
                        quality=100 // (1 << iteration),
                        optimize=True,
                    )
                    compressed_size = len(output.getvalue())
                    output.close()
                    if compressed_size < 20 * 1024:
                        break

            compressed_file = File(
                file_path=metadata.file_path,
                file_size=compressed_size,
                file_extension=metadata.file_extension,
            )
            metadata.new_file = compressed_file
        return metadata

    def save_file(self) -> None:
        compressed_file: File = self.compress_file()
        new_size = compressed_file.file_size
        if compressed_file.new_file:
            backup_path = self.file_path.with_suffix(f".backup{self.file_path.suffix}")
            shutil.copy2(self.file_path, backup_path)
            temp_path = self.file_path.with_suffix(f".temp{self.file_path.suffix}")
            with Image.open(self.file_path) as img:
                if not (img.mode == "P" or img.mode == "RGBA"):
                    save_format = (
                        "JPEG"
                        if compressed_file.file_extension == FileExtension.JPG
                        else compressed_file.file_extension.value.upper()
                    )
                    img.save(temp_path, format=save_format, quality=50, optimize=True)
                    shutil.move(temp_path, self.file_path)
                try:
                    shutil.rmtree(backup_path)
                except:
                    pass
                new_size = compressed_file.new_file.file_size
        print(f"Finished {compressed_file.file_size}: {self.file_path} -> {new_size}")


if __name__ == "__main__":
    directory = Path("/home/heneos/brilliant_problems/brioche/uploads/.")
    file_extensions = [e.value for e in FileExtension]
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix[1:].lower() in file_extensions:
            processor = ProcessImage(file_path)
            processor.save_file()
