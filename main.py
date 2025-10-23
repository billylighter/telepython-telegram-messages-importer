import asyncio
import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from PIL import Image, ImageTk, ImageDraw, ImageFont

SESSIONS_DIR = "sessions"
IMAGES_DIR = os.path.join("images", "profiles")
META_FILE = os.path.join(SESSIONS_DIR, "meta.json")

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

AVATAR_SIZE = 50


def load_meta():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_meta(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


class TelegramLoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Login")
        self.root.geometry("400x500")

        self.api_id = tk.StringVar()
        self.api_hash = tk.StringVar()
        self.phone = tk.StringVar()
        self.code = tk.StringVar()

        self.phone_code_hash = None
        self.client = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.temp_session_path = os.path.join(SESSIONS_DIR, "temp")
        self.show_session_selector()

    # -------------------- Helpers --------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def disconnect_client(self):
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None

    def make_rounded_avatar(self, img):
        img = img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS).convert("RGBA")
        mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
        img.putalpha(mask)
        return img

    def get_account_image(self, session_name, display_name):
        meta = load_meta()
        info = meta.get(session_name + ".session", {})
        avatar_path = info.get("avatar")
        if avatar_path and os.path.exists(avatar_path):
            img = Image.open(avatar_path)
            return ImageTk.PhotoImage(self.make_rounded_avatar(img))
        else:
            # generate first letter avatar
            letter = display_name[0].upper() if display_name else "?"
            img = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), color=(100, 100, 200))
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            w, h = draw.textbbox((0, 0), letter, font=font)[2:]
            draw.text(((AVATAR_SIZE - w) / 2, (AVATAR_SIZE - h) / 2), letter, fill="white", font=font)
            return ImageTk.PhotoImage(self.make_rounded_avatar(img))

    # -------------------- Session Selector --------------------
    def show_session_selector(self):
        self.clear_window()
        tk.Label(self.root, text="Choose Telegram Account", font=("Arial", 12, "bold")).pack(pady=10)

        meta = load_meta()
        sessions = [f[:-8] for f in os.listdir(SESSIONS_DIR) if f.endswith(".session") and f != "temp.session"]

        if sessions:
            for s in sessions:
                info = meta.get(s + ".session", {})
                display_name = info.get("display_name", s)
                img = self.get_account_image(s, display_name)

                frame = tk.Frame(self.root)
                frame.pack(pady=5, fill=tk.X, padx=10)

                if img:
                    lbl_img = tk.Label(frame, image=img)
                    lbl_img.image = img
                    lbl_img.pack(side=tk.LEFT, padx=5)

                tk.Button(frame, text=display_name, width=15,
                          command=lambda name=s: self.login_with_existing(name)).pack(side=tk.LEFT)
                tk.Button(frame, text="Remove", fg="red", command=lambda name=s: self.remove_account(name)).pack(
                    side=tk.LEFT, padx=5)
        else:
            tk.Label(self.root, text="No saved accounts found.").pack(pady=10)

        tk.Button(self.root, text="+ Add New Account", command=self.create_api_form).pack(pady=20)

    def remove_account(self, session_name):
        if messagebox.askyesno("Confirm", f"Remove account '{session_name}'?"):
            if self.client:
                client_path = self.client.session.filename
                if client_path.endswith(session_name + ".session"):
                    self.disconnect_client()

            session_path = os.path.join(SESSIONS_DIR, session_name + ".session")
            if os.path.exists(session_path):
                os.remove(session_path)

            meta = load_meta()
            info = meta.get(session_name + ".session")
            if info:
                avatar_path = info.get("avatar")
                if avatar_path and os.path.exists(avatar_path):
                    os.remove(avatar_path)
                meta.pop(session_name + ".session")
                save_meta(meta)

            messagebox.showinfo("Removed", f"Account '{session_name}' removed.")
            self.show_session_selector()

    # -------------------- Existing Account Login --------------------
    def login_with_existing(self, session_name):
        meta = load_meta()
        info = meta.get(session_name + ".session")
        if not info:
            messagebox.showerror("Error", "API credentials for this account are missing.")
            return
        try:
            self.disconnect_client()
            self.client = TelegramClient(os.path.join(SESSIONS_DIR, session_name), info["api_id"], info["api_hash"])
            self.loop.run_until_complete(self.client.connect())

            if self.loop.run_until_complete(self.client.is_user_authorized()):
                self.check_and_update_avatar(session_name)
                self.show_success()
            else:
                messagebox.showerror("Error", "Session not authorized. Please log in again.")
                self.create_api_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------- API Login --------------------
    def create_api_form(self):
        self.clear_window()
        tk.Label(self.root, text="Enter Telegram API Credentials", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(self.root, text="API ID:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.api_id).pack(pady=5)

        tk.Label(self.root, text="API Hash:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.api_hash).pack(pady=5)

        tk.Button(self.root, text="Next", command=self.start_login).pack(pady=15)

    def start_login(self):
        try:
            api_id = int(self.api_id.get())
            api_hash = self.api_hash.get().strip()
        except ValueError:
            messagebox.showerror("Error", "API ID must be a number.")
            return

        self.client = TelegramClient(self.temp_session_path, api_id, api_hash)
        self.loop.run_until_complete(self.client.connect())

        if not self.loop.run_until_complete(self.client.is_user_authorized()):
            messagebox.showinfo("Success", "API credentials accepted!")
            self.create_phone_form()
        else:
            self.rename_session_after_login()
            self.show_success()

    # -------------------- Phone Verification --------------------
    def create_phone_form(self):
        self.clear_window()
        tk.Label(self.root, text="Phone number (+country code):").pack(pady=5)
        tk.Entry(self.root, textvariable=self.phone).pack(pady=5)
        tk.Button(self.root, text="Send Code", command=self.send_code).pack(pady=15)

    def send_code(self):
        phone = self.phone.get().strip()
        if not phone:
            messagebox.showerror("Error", "Please enter your phone number.")
            return
        try:
            result = self.loop.run_until_complete(self.client.send_code_request(phone))
            self.phone_code_hash = result.phone_code_hash  # Store for later
            messagebox.showinfo("Code Sent", "Check your Telegram for the login code.")
            self.create_code_form()
        except Exception as e:
            messagebox.showerror("Send Code Error", str(e))

    def create_code_form(self):
        self.clear_window()
        tk.Label(self.root, text="Enter the code you received in Telegram:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.code).pack(pady=5)
        tk.Button(self.root, text="Verify Code", command=self.verify_code).pack(pady=15)

    def verify_code(self):
        phone = self.phone.get().strip()
        code = self.code.get().strip()
        try:
            self.loop.run_until_complete(
                self.client.sign_in(phone=phone, code=code, phone_code_hash=self.phone_code_hash)
            )
            self.rename_session_after_login()
            self.show_success()
        except SessionPasswordNeededError:
            pw = simpledialog.askstring("2FA Password", "Enter your two-step password:", show="*")
            self.loop.run_until_complete(self.client.sign_in(password=pw))
            self.rename_session_after_login()
            self.show_success()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Login Error", str(e))

    # -------------------- Session Rename & Avatar Handling --------------------
    def rename_session_after_login(self):
        me = self.loop.run_until_complete(self.client.get_me())
        name = me.username or me.first_name or str(me.phone)
        safe_name = name.replace(" ", "_").replace("@", "")
        new_path = os.path.join(SESSIONS_DIR, f"{safe_name}.session")

        temp_path = self.temp_session_path + ".session"
        if os.path.exists(temp_path):
            self.disconnect_client()
            os.rename(temp_path, new_path)

        # Save API credentials and avatar
        meta = load_meta()
        meta[safe_name + ".session"] = {
            "api_id": int(self.api_id.get()),
            "api_hash": self.api_hash.get(),
            "display_name": me.first_name or safe_name
        }
        save_meta(meta)

        self.disconnect_client()
        self.client = TelegramClient(new_path, int(self.api_id.get()), self.api_hash.get())
        self.loop.run_until_complete(self.client.connect())
        self.check_and_update_avatar(safe_name)

    def check_and_update_avatar(self, session_name):
        me = self.loop.run_until_complete(self.client.get_me())
        safe_name = session_name
        photo_path = None
        try:
            if me.photo:
                file = self.loop.run_until_complete(self.client.download_profile_photo(me))
                if file:
                    filename = f"{safe_name}.png"
                    photo_path = os.path.join(IMAGES_DIR, filename)
                    os.replace(file, photo_path)
            else:
                meta = load_meta()
                info = meta.get(safe_name + ".session")
                if info:
                    old_photo = info.get("avatar")
                    if old_photo and os.path.exists(old_photo):
                        os.remove(old_photo)
        except:
            pass

        meta = load_meta()
        info = meta.get(safe_name + ".session", {})
        info["avatar"] = photo_path
        meta[safe_name + ".session"] = info
        save_meta(meta)

    def send_test_message(self):
        if self.client:
            self.loop.run_until_complete(
                self.client.send_message("me", "Hello from Tkinter GUI!")
            )
            messagebox.showinfo("Message Sent", "Message sent to Saved Messages.")

    # -------------------- Logged In --------------------
    def show_success(self):
        self.clear_window()
        me = self.loop.run_until_complete(self.client.get_me())
        messagebox.showinfo("Login Success", f"Logged in as {me.first_name}")

        meta = load_meta()
        session_name = me.username or me.first_name or str(me.phone)
        safe_name = session_name.replace(" ", "_").replace("@", "")
        avatar_path = meta.get(safe_name + ".session", {}).get("avatar")

        if avatar_path and os.path.exists(avatar_path):
            img = Image.open(avatar_path)
            img = self.make_rounded_avatar(img)
            photo = ImageTk.PhotoImage(img)
            lbl_img = tk.Label(self.root, image=photo)
            lbl_img.image = photo
            lbl_img.pack(pady=10)
        else:
            letter = me.first_name[0].upper() if me.first_name else "?"
            img = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), color=(100, 100, 200))
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            w, h = draw.textbbox((0, 0), letter, font=font)[2:]
            draw.text(((AVATAR_SIZE - w) / 2, (AVATAR_SIZE - h) / 2), letter, fill="white", font=font)
            img = self.make_rounded_avatar(img)
            photo = ImageTk.PhotoImage(img)
            lbl_img = tk.Label(self.root, image=photo)
            lbl_img.image = photo
            lbl_img.pack(pady=10)

        tk.Label(self.root, text=f"Logged in as {me.first_name}", font=("Arial", 12, "bold")).pack(pady=5)
        if me.username:
            tk.Label(self.root, text=f"@{me.username}").pack(pady=5)
        tk.Label(self.root, text=f"Phone: {me.phone}").pack(pady=5)

        tk.Button(self.root, text="Send Test Message", command=self.send_test_message).pack(pady=15)
        tk.Button(self.root, text="Back to Account List", command=self.show_session_selector).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramLoginApp(root)
    root.mainloop()
