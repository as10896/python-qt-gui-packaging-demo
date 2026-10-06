# Python Qt GUI → macOS App & Windows EXE

[![English](https://img.shields.io/badge/English-read-brightgreen)](README.md)
[![繁體中文](https://img.shields.io/badge/%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-read-blue)](README_zh-TW.md)

這個 repo 用最精簡的方式，從頭到尾示範一遍：

1. 用 Python + [PySide6](https://doc.qt.io/qtforpython-6/)（Qt）寫一個有視窗的桌面程式
2. 再用 [PyInstaller](https://pyinstaller.org/) 打包成 **macOS 的 `.app`** 和 **Windows 的 `.exe`**，並透過 GitHub Actions 自動打包

為了有個實際的東西可以打包，範例做了一個叫 **UUID Renamer** 的小工具：把檔案拖進視窗，檔名就會改成隨機的 UUID，例如 `旅遊照片.jpg` 會變成 `3f2b9c1e-8d4a-4e7b-9f61-2c5d8a0b7e14.jpg`。功能刻意做得很簡單，才不會讓程式邏輯蓋過 GUI 和打包這兩個重點。

<p align="center">
  <img src="docs/idle.png" width="300" alt="主視窗，中間是虛線框的拖曳區">
  &nbsp;&nbsp;
  <img src="docs/dragging.png" width="300" alt="把檔案拖到視窗上時的畫面">
</p>

## 範例 App 的功能

- 可以拖檔案，也可以拖整個資料夾。拖資料夾時只會改資料夾第一層的檔案，子資料夾和 `.DS_Store` 這類隱藏檔不會動到。
- 副檔名會保留，例如 `報告.pdf` → `<uuid>.pdf`。
- 檔案拖到視窗上方時，畫面會切換成大大的「放開就改名」提示。
- 改完會跳出系統通知，視窗下方也會留下「舊檔名 → 新檔名」的紀錄，事後還查得到哪個檔案改成了什麼。

> ⚠️ 改了就沒辦法復原，建議先拿複製出來的檔案試試看。

## 為什麼選 PySide6，而不是 PyQt6？

用 Python 寫 Qt 程式時，一定會碰到 **PySide6** 和 **PyQt6** 這兩個套件。它們都是讓 Python 使用 Qt 6 的 binding，底層是同一套 Qt，API 也幾乎一樣。真正的差別在於誰在維護，以及採用的授權：

| | PySide6 | PyQt6 |
|---|---|---|
| 維護者 | Qt 官方（The Qt Company），又叫「Qt for Python」 | 第三方公司 Riverbank Computing |
| 授權 | LGPL（也有商業授權） | GPL（也有商業授權） |
| 寫法 | 用 `Signal`、`Slot`，列舉可以簡寫成 `Qt.AlignCenter` | 用 `pyqtSignal`、`pyqtSlot`，列舉要寫完整名稱，例如 `Qt.AlignmentFlag.AlignCenter` |

這個 repo 選 PySide6，主要有兩個原因：

- **授權比較適合這個 repo 的主題**：這個 repo 講的就是「打包成 App 發給別人用」。如果用 PyQt6（GPL），只要把程式發出去，你自己的程式碼也必須以 GPL 開源，不想開源就得購買商業授權。PySide6 採用 LGPL，一般來說可以用在閉源或商業產品，前提是使用者要能自行替換 Qt 函式庫。PyInstaller 預設會把 Qt 函式庫保留為獨立檔案，符合這個條件。
- **官方維護**：PySide6 由 Qt 官方跟著 Qt 本身一起開發，文件也放在 [qt.io](https://doc.qt.io/qtforpython-6/) 上。

網路上很多教學用的是 PyQt，參考起來沒什麼問題。要把那些程式碼改成 PySide6，通常只要改 import、把 `pyqtSignal` 換成 `Signal`，就差不多了。

> 以上說明不算法律建議。如果要做成商業產品發佈，請自行確認 LGPL 的條款。例如 Windows 用 `--onefile` 打包時，Qt 會被包進單一個 exe 裡，這樣算不算「使用者能自行替換 Qt」，各方解讀不一。

## 專案結構

```
.
├── app.py              # GUI 介面（PySide6）和通知
├── renamer.py          # 改名的核心邏輯，不依賴 GUI，也可以當 CLI 用
├── assets/icon.png     # App 圖示，視窗和通知也會用到
├── docs/               # README 用的截圖
├── requirements.txt
└── .github/workflows/build.yml   # 在 GitHub Actions 上打包 .app 和 .exe
```

刻意把改名邏輯從 GUI 拆出來放在 `renamer.py`，好處是方便測試，也可以單獨在終端機使用：

```bash
python renamer.py photo.jpg some-folder/
```

## 從原始碼執行

需要 Python 3.10 以上。

```bash
python -m venv .venv
source .venv/bin/activate        # Windows 請改用 .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## 打包成 App

PyInstaller 會把你的程式碼、Python 直譯器和所有相依套件包在一起，對方的電腦不用裝 Python，點兩下就能執行。

要特別注意的是：**PyInstaller 沒辦法跨平台打包**。打包出來的程式只能在跟打包環境相同的作業系統和 CPU 架構上執行：Windows 版要在 Windows 上打包，macOS 版要在 Mac 上打包；在 Apple Silicon Mac 上打包出來的 App，也只能在 Apple Silicon Mac 上執行。手邊沒有每一種電腦也沒關係，可以直接看下面的〈[用 GitHub Actions 一次打包所有版本](#用-github-actions-一次打包所有版本)〉。

### macOS

```bash
pyinstaller --noconfirm --windowed \
  --name "UUID Renamer" \
  --icon assets/icon.png \
  --add-data "assets:assets" \
  --collect-all desktop_notifier \
  --osx-bundle-identifier com.example.uuid-renamer \
  app.py
```

完成後會產生 `dist/UUID Renamer.app`。

### Windows

```powershell
pyinstaller --noconfirm --windowed --onefile --name "UUID Renamer" --icon assets/icon.png --add-data "assets:assets" --collect-all desktop_notifier app.py
```

完成後會產生 `dist\UUID Renamer.exe`。

### 各個參數的用途

| 參數 | 說明 |
|---|---|
| `--windowed` | 執行時不要多開一個終端機視窗。在 macOS 上也會因此產生 `.app`。 |
| `--onefile` | （只用在 Windows）把所有東西包成單一個 `.exe`，比較好分享。缺點是每次啟動都要先解壓縮到暫存資料夾，會多等幾秒。macOS 的 `.app` 本來就是一個可以整個拖來拖去的東西，所以不需要這個參數。 |
| `--name` | App 或 exe 的名稱。 |
| `--icon` | App 圖示。PyInstaller 會自動把 PNG 轉成 `.icns` 或 `.ico`，這也是 `requirements.txt` 裡放了 `pillow` 的原因。 |
| `--add-data "assets:assets"` | 把 `assets/` 資料夾一起包進去，因為程式執行時會讀取 `icon.png`。 |
| `--collect-all desktop_notifier` | `desktop-notifier` 有些檔案的載入方式 PyInstaller 偵測不到。少了這個參數，打包出來的 App 一打開就會閃退，錯誤訊息是 `No module named 'desktop_notifier.resources'`。 |
| `--osx-bundle-identifier` | App 在 macOS 上的唯一識別碼，記得把 `com.example` 換成你自己的網域。 |

PyInstaller 執行時也會產生一個 `UUID Renamer.spec` 設定檔。參數一多，可以改成編輯 spec 檔，再用 `pyinstaller "UUID Renamer.spec"` 打包。這個 repo 刻意只用指令參數，所有設定一眼就看得到。

### 用 GitHub Actions 一次打包所有版本

[`.github/workflows/build.yml`](.github/workflows/build.yml) 會同時在 GitHub 的三台機器上打包，你自己不用準備 Windows 電腦、Intel Mac 或 Apple Silicon Mac：

| 打包機器 | 產出的檔案 | 適用於 |
|---|---|---|
| `macos-latest` | `UUID-Renamer-macOS-arm64.zip` | Apple Silicon（M1 以後）的 Mac |
| `macos-15-intel` | `UUID-Renamer-macOS-x86_64.zip` | Intel Mac |
| `windows-latest` | `UUID-Renamer-Windows-x64.exe` | Windows（ARM 架構的 Windows 電腦也能透過模擬執行） |

在 GitHub Release 上，常會看到檔名直接標出架構，就是為了讓使用者一看就知道該下載哪個版本。

> `macos-15-intel` 是 GitHub 最後一個 Intel 版的 macOS 環境，只支援到 2027 年 8 月，之後就沒辦法在 GitHub Actions 上打包 Intel 版了。Apple 本來就在逐步淘汰 Intel Mac，到時候直接停止提供 Intel 版也很合理。

執行方式有兩種：

- **手動執行**：到 repo 的 *Actions* 分頁 → 選 *Build* → 按 *Run workflow*。跑完之後，在該次執行的 *Artifacts* 區塊就能下載打包好的檔案。手動執行不會建立 Release，比較適合在正式發佈前，先確認還能不能打包成功。
- **發佈 Release**：推一個 `v` 開頭的 tag。GitHub 會針對那個 tag 所在的 commit 重新打包，再把檔案自動附加到 GitHub Release。手動執行留下的 Artifacts 不會被拿來用，所以不需要先手動跑一次。

  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```

## 你大概會遇到的問題

### Mac 版要下載哪一個？

點左上角的蘋果選單 →「關於這台 Mac」。如果寫的是「晶片：Apple M…」，就下載 `arm64`；如果寫的是「處理器：Intel…」，就下載 `x86_64`。也可以在終端機輸入 `uname -m`，它會直接告訴你是哪一種。

下載錯的話：Apple Silicon 版在 Intel Mac 上根本打不開；Intel 版在 Apple Silicon Mac 上會透過 Rosetta 轉譯執行，可以用，只是比較慢。

如果想只發佈一個兩種 Mac 都能原生執行的 App，可以研究 PyInstaller 的 `--target-arch universal2`。不過 Python 本身要是 universal2 版本，所有含編譯程式碼的套件也都要提供 universal2 版本，比較容易卡關，所以這個 repo 選擇分開打包。

### 「無法驗證開發者」和 SmartScreen 警告

這裡打包出來的 App 都沒有做程式碼簽章（code signing），所以第一次打開時兩個系統都會擋：

- **macOS**：會顯示「Apple 無法確認 UUID Renamer 是否包含惡意軟體」。到「系統設定 → 隱私權與安全性」，往下捲，按「強制打開」就可以了。也可以在終端機移除隔離標記：

  ```bash
  xattr -dr com.apple.quarantine "UUID Renamer.app"
  ```

- **Windows**：SmartScreen 會跳出「Windows 已保護您的電腦」，按「其他資訊 → 仍要執行」。

自己用或拿來 demo 都沒什麼問題。但如果要正式發給其他人用、不想讓對方看到這些警告，macOS 需要 Apple Developer ID（一年 99 美元）來簽章和公證（notarization），Windows 則要另外買程式碼簽章憑證。

### macOS 上的通知

這個 App 用 [desktop-notifier](https://github.com/samschott/desktop-notifier) 發送原生通知，但 macOS 只允許**有 Apple Developer ID 簽章**的 App 使用通知中心。沒簽章的 App 會被拒絕；直接跑 `python app.py` 也不行，因為那根本不是一個 App bundle。

所以 `app.py` 在 macOS 上會先檢查能不能發原生通知，不行的話就改用 AppleScript（`osascript`）。通知一樣會跳出來，只是圖示會變成「工序指令編寫程式」，而不是這個 App 的圖示。等 App 有了正式簽章，就會自動改用原生通知。Windows 沒有這個限制。

### 其他

- **檔案大小**：macOS 版大約 80 MB，Windows 版也差不多，大部分都是 Qt。這裡裝的是 `PySide6-Essentials` 而不是完整的 `PySide6`，完整版多了 WebEngine、3D、Multimedia 等這個 App 用不到的模組，體積會大上不少。
