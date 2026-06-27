# Google Drive File Explorer Telegram Bot

A high-performance Telegram bot that serves as an interactive, deep file explorer for a specific Google Drive directory. It caches your cloud folder structure straight into memory for instant browsing and streams documents directly into Telegram chats, completely bypassing traditional download size ceilings.

---

## 🛠️ How It Works (Behind the Scenes)

Even if you don't understand the code, here is a straightforward explanation of how the system runs:

1. **Cloud Authentication & Connection:** The bot connects securely to Google Drive using a dedicated **Google Service Account Key**. It targets one main root folder (`1-5ocbVU17S13rUgbaxi5kEWOXjAJWTsf`) as its homepage.

2. **Smart In-Memory Caching (Instant Browsing):** When you start the bot, it performs a complete hierarchical scan of your Google Drive folder structure. It saves all folder arrangements, file names, and IDs straight into the server's RAM memory. 
   * **Custom Folder Descriptions:** If a folder contains a text (`.txt`) file, the bot downloads its contents during the scan and uses it as a descriptions banner inside that folder's interface.

3. **Dynamic Interactive Menus:** When a user types `/menu`, the bot generates an interactive panel inside the chat with custom clickable buttons:
   * 📁 **Subfolders:** Navigates deeper into the directory structure.
   * 📄 **Files:** Targets specific documents for immediate download.
   * ⬅️ **Back Button:** Contextually shifts back to the parent folder instantly without resetting the menu.

4. **Advanced Streaming Engine:** When a file button is clicked, the engine pulls the document's media stream chunk-by-chunk directly from the Google Drive API into temporary server memory (`io.BytesIO()`) and sends it natively to the user as a Telegram document. This completely bypasses Telegram's URL download limit, ensuring smooth, automated file delivery.

---

## 📂 Project Architecture & Components

* **`main.py`** – The central nervous system. It initializes the bot application and keeps it constantly listening for new user requests (`Infinity Polling`).
* **`config.py`** – Security guard. Safely fetches your sensitive Telegram connection token (`BOT_TOKEN`) from hidden environment variables.
* **`file_data.py`** – The data brain. Connects to the Google Drive API, constructs the recursive in-memory map on startup, and reads descriptive text files.
* **`menu_handler.py`** – The user interface generator. Builds the nested button structures (Folders, Files, Back buttons) and manages navigation clicks.
* **`start_handler.py`** – The greeting handler. Simple greeting system when a user launches the bot for the first time via `/start`.
* **`utils.py`** – The pipeline delivery system. Handles downloading from Google Drive chunk-by-chunk and uploading it straight to the user's screen.

---

## ⚙️ Requirements & Dependencies

The bot is powered by Python >= 3.11 and leverages several official packages:
* **`pyTelegramBotAPI`:** Powering the core Telegram bot behaviors and menu inputs.
* **`google-api-python-client` & `google-auth`:** Authenticates and interfaces natively with Google Drive cloud storage.
* **`requests`:** Manages network connections.
* **`python-dotenv`:** Safely loads private configuration keys without exposing passwords.

---

## ⚠️ Key Operational Notes (From `Note.txt`)
* **Live Synchronization:** Any additions, updates, deletions, or rearrangements of files should be carried out directly inside your **Google Drive**.
* **Sorting Adjustments:** If you need to rearrange the chronological or alpha sorting structures, update `list_handler.py` first before updating any child click handlers.
