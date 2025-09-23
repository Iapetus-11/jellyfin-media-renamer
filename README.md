# Jellyfin Media Renamer
*A tool for processing shows and movies downloaded or ripped from disks for Jellyfin*

## What?
| Before  | After `jellyfinrename` |
| ------------- | ------------- |
| `Conan.The.Barbarian.1982.E.1080p.BluRay.x265-RBG/`<br>`├── Conan.The.Barbarian.1982.E.1080p.BluRay.x265-RBG.mp4`<br>`├── Conan.The.Barbarian.1982.E.1080p.BluRay.x265-RBG.srt`<br>`└── junk.txt`  | `Conan The Barbarian (1982)/`<br>`├── Conan The Barbarian (1982).mp4`<br>`└── Conan The Barbarian (1982).srt`  |

## Installation
*(Assumes you have pipx, or similar)*
1. Clone this repository: `git clone https://github.com/Iapetus-11/jellyfin-media-renamer.git`
2. Enter the folder: `cd jellyfin-media-renamer`
3. Install with pipx: `pipx install . --force` (use `--force` if you are upgrading, as I haven't bothered bumping the version)

## Usage
1. Just run `jellyfinrename <target>` and watch (you may be prompted to confirm changes)
2. Due to the nature of these files, this can only handle a subset of the different naming formats people use, please submit a PR or bug report if you encounter one this tool does not support.
