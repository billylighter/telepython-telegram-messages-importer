import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from telethon.errors import SessionPasswordNeededError

from app.utils.constants import AVATAR_SIZE, SESSIONS_DIR, IMAGES_DIR
from app.utils.file_utils import load_meta, save_meta
from app.utils.image_utils import make_rounded_avatar, generate_letter_avatar
from app.telegram_client.client_manager import TelegramClientManager
from app.services.session_service import remove_session


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
        self.client_manager = TelegramClientManager()
        self.client = None

        self.temp_session_path = os.path.join(SESSIONS_DIR, "temp")
        self.show_session_selector()

    # -------------------- Helpers --------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def disconnect_client(self):
        if self.client_manager:
            self.client_manager.disconnect()

    def get_account_image(self, session_name, display_name):
        meta = load_meta()
        info = meta.get(session_name + ".session", {})
        avatar_path = info.get("avatar")

        if avatar_path and os.path.exists(avatar_path):
            img = Image.open(avatar_path)
            return ImageTk.PhotoImage(make_rounded_avatar(img))
        else:
            img = generate_letter_avatar(display_name[0] if display_name else "?")
            return ImageTk.PhotoImage(img)

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
                tk.Button(frame, text="Remove", fg="red",
                          command=lambda name=s: self.remove_account(name)).pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(self.root, text="No saved accounts found.").pack(pady=10)

        tk.Button(self.root, text="+ Add New Account", command=self.create_api_form).pack(pady=20)

    def remove_account(self, session_name):
        if messagebox.askyesno("Confirm", f"Remove account '{session_name}'?"):
            self.disconnect_client()
            remove_session(session_name)
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
            self.client = self.client_manager.connect(session_name, info["api_id"], info["api_hash"])

            if self.client_manager.is_authorized():
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

        # Frame для кнопок
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)  # отступ сверху/снизу всего блока кнопок

        tk.Button(button_frame, text="Back to Account List", command=self.show_session_selector).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Next", command=self.start_login).pack(side=tk.LEFT, padx=5)


    def start_login(self):
        try:
            api_id = int(self.api_id.get())
            api_hash = self.api_hash.get().strip()
        except ValueError:
            messagebox.showerror("Error", "API ID must be a number.")
            return

        self.client = self.client_manager.connect("temp", api_id, api_hash)

        if not self.client_manager.is_authorized():
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

        # Frame для кнопок
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)

        # Кнопка Back слева
        tk.Button(button_frame, text="Back", command=self.create_api_form).pack(side=tk.LEFT, padx=5)
        # Кнопка Send Code справа
        tk.Button(button_frame, text="Send Code", command=self.send_code).pack(side=tk.LEFT, padx=5)

    def send_code(self):
        phone = self.phone.get().strip()
        if not phone:
            messagebox.showerror("Error", "Please enter your phone number.")
            return
        try:
            result = self.client_manager.send_code(phone)
            self.phone_code_hash = result.phone_code_hash
            messagebox.showinfo("Code Sent", "Check your Telegram for the login code.")
            self.create_code_form()
        except Exception as e:
            messagebox.showerror("Send Code Error", str(e))

    def create_code_form(self):
        self.clear_window()

        tk.Label(self.root, text="Enter the code you received in Telegram:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.code).pack(pady=5)

        # Frame для кнопок
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)

        # Кнопка Back слева
        tk.Button(button_frame, text="Back", command=self.create_phone_form).pack(side=tk.LEFT, padx=5)
        # Кнопка Verify Code справа
        tk.Button(button_frame, text="Verify Code", command=self.verify_code).pack(side=tk.LEFT, padx=5)

    def verify_code(self):
        phone = self.phone.get().strip()
        code = self.code.get().strip()
        try:
            self.client_manager.sign_in(phone, code, self.phone_code_hash)
            self.rename_session_after_login()
            self.show_success()
        except SessionPasswordNeededError:
            pw = simpledialog.askstring("2FA Password", "Enter your two-step password:", show="*")
            self.client_manager.sign_in_2fa(pw)
            self.rename_session_after_login()
            self.show_success()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Login Error", str(e))

    # -------------------- Session Rename & Avatar Handling --------------------
    def rename_session_after_login(self):
        me = self.client_manager.get_me()
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
        self.client = self.client_manager.connect(safe_name, int(self.api_id.get()), self.api_hash.get())
        self.check_and_update_avatar(safe_name)

    def check_and_update_avatar(self, session_name):
        me = self.client_manager.get_me()
        safe_name = session_name
        photo_path = None

        try:
            if me.photo:
                filename = f"{safe_name}.png"
                photo_path = self.client_manager.download_avatar(me, filename)
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
            self.client_manager.send_message("me", "Hello from Tkinter GUI!")
            messagebox.showinfo("Message Sent", "Message sent to Saved Messages.")

    # -------------------- Logged In --------------------
    def show_success(self):
        self.clear_window()
        me = self.client_manager.get_me()
        # messagebox.showinfo("Login Success", f"Logged in as {me.first_name}")

        meta = load_meta()
        session_name = me.username or me.first_name or str(me.phone)
        safe_name = session_name.replace(" ", "_").replace("@", "")
        avatar_path = meta.get(safe_name + ".session", {}).get("avatar")

        if avatar_path and os.path.exists(avatar_path):
            img = Image.open(avatar_path)
            photo = ImageTk.PhotoImage(make_rounded_avatar(img))
        else:
            img = generate_letter_avatar(me.first_name or "?")
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
