# Installation Instructions

## Android

1. Download termux from the fdroid(since play store doesn't support termux fully): https://f-droid.org/en/
2. Open termux and run the following commands:
```bash
pkg install git
git clone https://github.com/SoniCoder/mythic-inventory.git
cd mythic-inventory
pip install -r requirements.txt
python mythic-inv-cli.py
```
3. This should open the CLI in termux and you can starting creating containers and items using n and c respectively. Press h for help and other instructions.

## Linux

The Linux installation is similar to the Android installation except that you don't need to install termux. You can use the terminal to run the commands. Make sure to use apt instead of pkg to install the required packages.

### World Directory

By default the world directory is `./world` inside the directory as the `mythic-inv-cli.py` file. You can change the world directory in the `config.py` file.

### Configuration

- You can change the world directory in the `config.py` file using world_folder config.


### Updates and BugFixes

- You can update the CLI by running the following commands in termux:
```bash
git pull
```

- If you find any bugs or issues, please report them in the issues section of the github repository.
