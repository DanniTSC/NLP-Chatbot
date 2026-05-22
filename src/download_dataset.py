import kagglehub
import shutil
from pathlib import Path

# download dataset
download_path = kagglehub.dataset_download(
    "thoughtvector/customer-support-on-twitter"
)

print("Downloaded to:", download_path)

# target folder
target_dir = Path("data/raw")
target_dir.mkdir(parents=True, exist_ok=True)

source_path = Path(download_path)

# copy EVERYTHING recursively
for item in source_path.rglob("*"):
    relative_path = item.relative_to(source_path)
    destination = target_dir / relative_path

    if item.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
    else:
        shutil.copy2(item, destination)

print("Dataset copied successfully!")