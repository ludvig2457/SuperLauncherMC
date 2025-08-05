# SuperLauncher

🎮 Lightweight and fast Minecraft launcher with automatic updates to the latest versions.

---

## 🚀 Features

- Supports the latest Minecraft version (at release — 1.21.8)  
- Automatic updates for both launcher and Minecraft when new versions are released by Mojang  
- Ability to create and manage your own local Minecraft servers directly from the launcher  
- Server management panel with EULA settings, online/offline mode, and start/stop controls  
- Add any servers to the list for quick connection  
- Manual download and management of Minecraft versions (in the `versions` folder)  
- Ability to manually download and use Fabric, Forge, and OptiFine mods  
- Does not require Java installation — Minecraft and servers run using the `minecraft-launcher-lib` library  
- Simple and minimalist interface  

---

## 📁 Included

- `super_launcher.exe` — executable launcher file  
- `assets/title.png` — launcher icon/logo  

---

## 🔧 Technologies

- Language: Python 3.x  
- Compiled with: PyInstaller  
- Minecraft and server launching via [`minecraft-launcher-lib`](https://github.com/TechnicPack/MinecraftLauncherLib)  

---

## 📥 How to use

1. Download the `super_launcher.exe` file from the [releases](https://github.com/ludvig2457/SuperLauncher/releases) section  
2. Run the file by double-clicking  
3. The launcher will automatically download the latest Minecraft version and start the game  
4. Use the built-in control panel to create and manage servers  
5. If needed, manually download Minecraft versions and Fabric, Forge, OptiFine mods by placing them in the appropriate folders  
6. Enjoy playing without complicated setup and hassle!

---

## 🆕 What’s new in version 1.4.0.5

- ✅ Integration with Modrinth API for downloading and managing mods directly from the launcher  
- 🎨 Added support for light and dark UI themes  
- ⚙️ New Minecraft launch method option: by default uses `minecraft-launcher-lib`, optionally you can specify a path to installed Java  
- 🐞 Fixed minor bugs and improved stability  

---

## ❌ Limitations

- Automatic support for Fabric, Forge, and OptiFine mods is not yet implemented — they must be downloaded and installed manually  
- Minecraft and servers are launched via `minecraft-launcher-lib`, so external Java installation is not required  

---

## 🌟 Author

**Ludvig2457** — [GitHub profile](https://github.com/ludvig2457)

---

Thank you for using SuperLauncher!  
If you have ideas or find bugs, please create an issue or submit a PR.
