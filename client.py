import tkinter as tk
from tkinter import messagebox
import json
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class Admin:
    """Admin user model for SHECONNECT.

    An Admin can view platform users, including both Entrepreneurs and Customers,
    and can monitor businesses, categories and enquiries.
    """
    def __init__(self, user_data):
        self.user_id = user_data.get("user_id")
        self.name = user_data.get("name", "Admin")
        self.email = user_data.get("email", "")
        self.role = user_data.get("role", "admin")

    def is_admin(self):
        return self.role == "admin"

    def can_view_users(self):
        return self.is_admin()

    def can_view_entrepreneurs(self):
        return self.is_admin()

    def can_view_customers(self):
        return self.is_admin()


class SheConnectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SHECONNECT — Women's Business Hub")
        self.geometry("1250x780")
        self.minsize(1100, 700)
        self.configure(bg="#FFF8FB")

        self.colors = {
            "background": "#FFF8FB", "sidebar": "#FFFFFF", "card": "#FFFFFF",
            "primary": "#C4457F", "primary_dark": "#A93668", "primary_light": "#F8E5EE",
            "pink": "#D85C91", "soft_pink": "#FCEEF4", "dark_pink": "#8F2855",
            "text": "#29242A", "muted": "#777078", "border": "#EADDE4",
            "success": "#4D9872", "warning": "#D59A45", "white": "#FFFFFF", "danger": "#C84A5A"
        }
        self.fonts = {
            "brand": ("Segoe UI", 22, "bold"), "heading": ("Segoe UI", 25, "bold"),
            "page_heading": ("Segoe UI", 23, "bold"), "subheading": ("Segoe UI", 11),
            "body": ("Segoe UI", 10), "body_bold": ("Segoe UI", 10, "bold"),
            "navigation": ("Segoe UI", 10), "button": ("Segoe UI", 10, "bold"),
            "small": ("Segoe UI", 8), "card_number": ("Segoe UI", 22, "bold")
        }
        self.current_user = None
        self.saved_businesses = set()
        self.businesses = []
        self.products = []
        self.sidebar = None
        self.main_area = None
        self.create_login_screen()

    # =========================================================
    # API HELPERS
    # =========================================================
    def api_request(self, endpoint, method="GET", payload=None):
        try:
            url = f"http://127.0.0.1:5000{endpoint}"
            data = None
            headers = {"Content-Type": "application/json"}
            if payload is not None:
                data = json.dumps(payload).encode("utf-8")
            request = Request(url, data=data, headers=headers, method=method)
            with urlopen(request, timeout=5) as response:
                raw = response.read().decode("utf-8")
                return response.status, json.loads(raw) if raw else {}
        except HTTPError as error:
            try:
                raw = error.read().decode("utf-8")
                return error.code, json.loads(raw) if raw else {"error": "Request failed."}
            except Exception:
                return error.code, {"error": "Request failed."}
        except (URLError, TimeoutError, OSError) as error:
            print("API ERROR:", error)
            return None, {"error": "Flask server is not running. Start app.py first."}
        except Exception as error:
            print("API ERROR:", error)
            return None, {"error": "Unable to connect to the SHECONNECT server."}

    def get_api_data(self, endpoint):
        status, data = self.api_request(endpoint)
        if status == 200:
            return data
        return None

    # =========================================================
    # AUTHENTICATION
    # =========================================================
    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _make_entry(self, parent, placeholder="", show=None):
        """Professional input box: placeholder is light, typed text is dark black."""
        outer = tk.Frame(
            parent,
            bg=self.colors["white"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        outer.pack(fill="x", pady=(5, 16))

        # Typed text is intentionally dark for strong visibility.
        normal_text = "#1F1B1E"
        placeholder_text = "#A79BA3"

        entry = tk.Entry(
            outer,
            font=("Segoe UI", 12),
            relief="flat",
            bd=0,
            bg="#FFFCFE",
            fg=normal_text,
            insertbackground=normal_text,
            show=""
        )
        entry.pack(fill="x", padx=15, pady=11, ipady=3)

        is_placeholder = bool(placeholder)

        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg=placeholder_text, insertbackground=normal_text, show="")

        def focus_in(event=None):
            nonlocal is_placeholder
            if is_placeholder:
                entry.delete(0, "end")
                is_placeholder = False
            entry.config(
                fg=normal_text,
                insertbackground=normal_text,
                show=show or ""
            )
            outer.config(
                highlightbackground=self.colors["primary"],
                highlightthickness=2
            )

        def focus_out(event=None):
            nonlocal is_placeholder
            if not entry.get():
                is_placeholder = True
                entry.config(
                    show="",
                    fg=placeholder_text,
                    insertbackground=normal_text
                )
                entry.insert(0, placeholder)
            else:
                is_placeholder = False
                entry.config(
                    fg=normal_text,
                    insertbackground=normal_text,
                    show=show or ""
                )
            outer.config(
                highlightbackground=self.colors["border"],
                highlightthickness=1
            )

        entry.bind("<FocusIn>", focus_in)
        entry.bind("<FocusOut>", focus_out)
        return entry

    def _auth_brand_panel(self, parent, title, subtitle):
        """Premium left-side branding panel for authentication screens."""
        panel = tk.Frame(parent, bg=self.colors["primary"], width=510)
        panel.pack(side="left", fill="y")
        panel.pack_propagate(False)

        # Decorative circles give the screen a polished app-like feel.
        canvas = tk.Canvas(panel, bg=self.colors["primary"], highlightthickness=0)
        canvas.place(relwidth=1, relheight=1)
        canvas.create_oval(-130, -120, 170, 180, fill=self.colors["primary_dark"], outline="")
        canvas.create_oval(320, 575, 570, 825, fill=self.colors["dark_pink"], outline="")
        canvas.create_oval(300, 35, 525, 260, outline="#D86B9A", width=2)

        content = tk.Frame(panel, bg=self.colors["primary"])
        content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.82)

        logo = tk.Frame(content, bg=self.colors["primary"])
        logo.pack(anchor="w", pady=(0, 32))
        tk.Label(logo, text="♀", font=("Segoe UI Symbol", 42, "bold"),
                 fg=self.colors["white"], bg=self.colors["primary"]).pack(side="left")
        brand = tk.Frame(logo, bg=self.colors["primary"])
        brand.pack(side="left", padx=(13, 0))
        tk.Label(brand, text="SHECONNECT", font=("Segoe UI", 26, "bold"),
                 fg=self.colors["white"], bg=self.colors["primary"]).pack(anchor="w")
        tk.Label(brand, text="WOMEN'S BUSINESS HUB", font=("Segoe UI", 9, "bold"),
                 fg="#FCEAF2", bg=self.colors["primary"]).pack(anchor="w", pady=(1, 0))

        tk.Frame(content, bg="#ECA6C4", height=2).pack(fill="x", pady=(0, 28))
        tk.Label(content, text=title, font=("Segoe UI", 26, "bold"),
                 fg=self.colors["white"], bg=self.colors["primary"],
                 justify="left", anchor="w", wraplength=385).pack(anchor="w")
        tk.Label(content, text=subtitle, font=("Segoe UI", 11),
                 fg="#FBEAF2", bg=self.colors["primary"],
                 justify="left", anchor="w", wraplength=380).pack(anchor="w", pady=(12, 28))

        benefits = [
            ("01", "Discover women-led businesses"),
            ("02", "Connect with customers and entrepreneurs"),
            ("03", "Grow your business community")
        ]
        for number, text in benefits:
            row = tk.Frame(content, bg=self.colors["primary"])
            row.pack(fill="x", pady=7)
            tk.Label(row, text=number, font=("Segoe UI", 9, "bold"),
                     fg=self.colors["white"], bg=self.colors["dark_pink"],
                     width=4, pady=4).pack(side="left")
            tk.Label(row, text=text, font=("Segoe UI", 10),
                     fg="#FFF5F9", bg=self.colors["primary"],
                     anchor="w").pack(side="left", padx=12)

        tk.Label(content, text="Connect  •  Discover  •  Grow",
                 font=("Segoe UI", 10, "bold"), fg="#F8DDE8",
                 bg=self.colors["primary"]).pack(anchor="w", pady=(34, 0))
        return panel

    def _auth_button(self, parent, text, command):
        button = tk.Button(
            parent, text=text, command=command,
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["white"], bg=self.colors["primary"],
            activeforeground=self.colors["white"],
            activebackground=self.colors["primary_dark"],
            relief="flat", bd=0, cursor="hand2", pady=13
        )
        button.pack(fill="x", pady=(4, 8))
        button.bind("<Enter>", lambda e: button.config(bg=self.colors["primary_dark"]))
        button.bind("<Leave>", lambda e: button.config(bg=self.colors["primary"]))
        return button

    def _auth_form_card(self, parent, width=560, padding_x=42, padding_y=32):
        """Centered professional authentication card."""
        holder = tk.Frame(parent, bg=self.colors["background"])
        holder.pack(fill="both", expand=True)

        card = tk.Frame(
            holder,
            bg=self.colors["white"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=width)

        inner = tk.Frame(card, bg=self.colors["white"])
        inner.pack(fill="both", padx=padding_x, pady=padding_y)
        return inner

    def _auth_text_link(self, parent, text, command):
        button = tk.Button(
            parent, text=text,
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary"], bg=self.colors["white"],
            activeforeground=self.colors["dark_pink"],
            activebackground=self.colors["white"],
            relief="flat", bd=0, cursor="hand2"
        )
        button.config(command=command)
        button.bind("<Enter>", lambda e: button.config(fg=self.colors["dark_pink"]))
        button.bind("<Leave>", lambda e: button.config(fg=self.colors["primary"]))
        button.pack()
        return button

    def create_login_screen(self):
        self._clear_window()
        self.title("SHECONNECT — Sign In")
        self.geometry("1250x780")
        self.configure(bg=self.colors["background"])

        wrapper = tk.Frame(self, bg=self.colors["background"])
        wrapper.pack(fill="both", expand=True)

        self._auth_brand_panel(
            wrapper,
            "A stronger place to\nbuild your business.",
            "SHECONNECT brings women entrepreneurs and customers together in one professional business community."
        )

        right = tk.Frame(wrapper, bg=self.colors["background"])
        right.pack(side="right", fill="both", expand=True)

        # Small top-right branding mark keeps the screen balanced.
        top = tk.Frame(right, bg=self.colors["background"])
        top.pack(fill="x", padx=48, pady=(26, 0))
        tk.Label(
            top, text="SHECONNECT",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary"], bg=self.colors["background"]
        ).pack(anchor="e")

        form = self._auth_form_card(right, width=560, padding_x=48, padding_y=34)

        tk.Label(
            form, text="Welcome back",
            font=("Segoe UI", 24, "bold"),
            fg=self.colors["text"], bg=self.colors["white"]
        ).pack(anchor="w")

        tk.Label(
            form, text="Sign in to continue to your SHECONNECT account.",
            font=("Segoe UI", 10),
            fg=self.colors["muted"], bg=self.colors["white"]
        ).pack(anchor="w", pady=(7, 27))

        tk.Label(
            form, text="Email address",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"], bg=self.colors["white"]
        ).pack(anchor="w")
        email = self._make_entry(form, "Enter your email")

        tk.Label(
            form, text="Password",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"], bg=self.colors["white"]
        ).pack(anchor="w")
        password = self._make_entry(form, "Enter your password", show="•")

        def submit_login():
            self.login(
                "" if email.get() == "Enter your email" else email.get(),
                "" if password.get() == "Enter your password" else password.get()
            )

        self._auth_button(form, "Sign in to SHECONNECT", submit_login)

        divider = tk.Frame(form, bg=self.colors["border"], height=1)
        divider.pack(fill="x", pady=(22, 18))

        account_row = tk.Frame(form, bg=self.colors["white"])
        account_row.pack()
        tk.Label(
            account_row, text="Don't have an account?",
            font=("Segoe UI", 10),
            fg=self.colors["muted"], bg=self.colors["white"]
        ).pack(side="left", padx=(0, 5))
        self._auth_text_link(account_row, "Create an account", self.show_register)

        tk.Label(
            form, text="Secure access  •  Professional community",
            font=("Segoe UI", 9),
            fg="#9A8E96", bg=self.colors["white"]
        ).pack(pady=(21, 0))

        password.bind("<Return>", lambda event: submit_login())
        email.bind("<Return>", lambda event: password.focus_set())
        email.focus_set()

    def login(self, email, password):
        email = email.strip()
        if not email or not password:
            messagebox.showwarning("Login", "Please enter your email and password.")
            return
        status, data = self.api_request("/api/login", "POST", {"email": email, "password": password})
        if status == 200 and data.get("success"):
            self.current_user = data.get("user")
            self.saved_businesses = set()
            self.admin_user = Admin(self.current_user) if self.current_user.get("role") == "admin" else None
            self.create_layout()
            if self.current_user.get("role") == "admin":
                self.show_admin_dashboard()
            else:
                self.show_dashboard()
        else:
            messagebox.showerror("Login failed", data.get("error", "Invalid email or password."))

    def show_register(self):
        self._clear_window()
        self.title("SHECONNECT — Create Account")
        self.geometry("1250x820")
        self.configure(bg=self.colors["background"])

        wrapper = tk.Frame(self, bg=self.colors["background"])
        wrapper.pack(fill="both", expand=True)

        self._auth_brand_panel(
            wrapper,
            "Create your place\nin the community.",
            "Build your profile, discover opportunities and connect with a growing women-focused business network."
        )

        right = tk.Frame(wrapper, bg=self.colors["background"])
        right.pack(side="right", fill="both", expand=True)

        top = tk.Frame(right, bg=self.colors["background"])
        top.pack(fill="x", padx=48, pady=(26, 0))
        tk.Label(
            top, text="SHECONNECT",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary"], bg=self.colors["background"]
        ).pack(anchor="e")

        form = self._auth_form_card(right, width=625, padding_x=50, padding_y=30)

        tk.Label(
            form, text="Create your account",
            font=("Segoe UI", 24, "bold"),
            fg=self.colors["text"], bg=self.colors["white"]
        ).pack(anchor="w")
        tk.Label(
            form, text="Join SHECONNECT in a few simple steps.",
            font=("Segoe UI", 10),
            fg=self.colors["muted"], bg=self.colors["white"]
        ).pack(anchor="w", pady=(6, 21))

        fields = {}
        field_data = [
            ("Full name", "Enter your full name", None),
            ("Email address", "Enter your email", None),
            ("Password", "Create a password", "•")
        ]
        for label, placeholder, show in field_data:
            tk.Label(
                form, text=label,
                font=("Segoe UI", 10, "bold"),
                fg=self.colors["text"], bg=self.colors["white"]
            ).pack(anchor="w")
            fields[label] = self._make_entry(form, placeholder, show=show)

        tk.Label(
            form, text="Account type",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"], bg=self.colors["white"]
        ).pack(anchor="w", pady=(0, 6))

        role = tk.StringVar(value="customer")
        role_frame = tk.Frame(form, bg=self.colors["white"])
        role_frame.pack(fill="x", pady=(0, 17))

        role_options = [
            ("customer", "Customer", "Send enquiries"),
            ("entrepreneur", "Entrepreneur", "Manage business"),
            ("admin", "Admin", "Manage platform")
        ]

        # Three clearly visible account types: Customer, Entrepreneur and Admin.
        for column, (value, label, description) in enumerate(role_options):
            option = tk.Frame(
                role_frame, bg=self.colors["soft_pink"],
                highlightbackground=self.colors["border"], highlightthickness=1,
                width=175, height=78
            )
            option.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            option.grid_propagate(False)
            role_frame.grid_columnconfigure(column, weight=1)

            tk.Radiobutton(
                option, text=label, variable=role, value=value,
                font=("Segoe UI", 9, "bold"),
                fg=self.colors["text"], bg=self.colors["soft_pink"],
                activebackground=self.colors["soft_pink"],
                selectcolor=self.colors["white"], cursor="hand2"
            ).pack(anchor="w", padx=8, pady=(7, 0))
            tk.Label(
                option, text=description,
                font=("Segoe UI", 8),
                fg=self.colors["muted"], bg=self.colors["soft_pink"]
            ).pack(anchor="w", padx=28, pady=(0, 5))

        def submit_registration():
            name = "" if fields["Full name"].get() == "Enter your full name" else fields["Full name"].get()
            email = "" if fields["Email address"].get() == "Enter your email" else fields["Email address"].get()
            password = "" if fields["Password"].get() == "Create a password" else fields["Password"].get()
            self.register(name, email, password, role.get())

        tk.Label(
            form,
            text="Admin accounts can manage platform data and settings.",
            font=("Segoe UI", 9),
            fg=self.colors["muted"],
            bg=self.colors["white"]
        ).pack(anchor="w", pady=(0, 8))

        self._auth_button(form, "Create SHECONNECT Account", submit_registration)

        back_row = tk.Frame(form, bg=self.colors["white"])
        back_row.pack(pady=(5, 0))
        tk.Label(
            back_row, text="Already have an account?",
            font=("Segoe UI", 10),
            fg=self.colors["muted"], bg=self.colors["white"]
        ).pack(side="left", padx=(0, 5))
        self._auth_text_link(back_row, "Sign in", self.create_login_screen)

        tk.Label(
            form, text="Your account is securely connected to the SHECONNECT platform.",
            font=("Segoe UI", 9),
            fg="#9A8E96", bg=self.colors["white"]
        ).pack(pady=(14, 0))

        fields["Full name"].focus_set()

    def register(self, name, email, password, role):
        if not name.strip() or not email.strip() or not password:
            messagebox.showwarning("Create account", "Please complete all required fields.")
            return
        status, data = self.api_request("/api/register", "POST", {
            "name": name.strip(), "email": email.strip(),
            "password": password, "role": role
        })
        if status == 201 and data.get("success"):
            messagebox.showinfo("Registration", "Account created successfully. You can now log in.")
            self.create_login_screen()
        else:
            messagebox.showerror("Registration failed", data.get("error", "Unable to create account."))

    # =========================================================
    # MAIN LAYOUT / SIDEBAR
    # =========================================================
    def create_layout(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Clean fixed desktop layout — no main-content scrollbar.
        self.sidebar = tk.Frame(self, bg=self.colors["sidebar"], width=290)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Right side: clean scrollable content area.
        # The scrollbar appears only when the page content is taller than the window.
        self.main_shell = tk.Frame(self, bg=self.colors["background"])
        self.main_shell.pack(side="right", fill="both", expand=True)

        self.main_canvas = tk.Canvas(
            self.main_shell,
            bg=self.colors["background"],
            highlightthickness=0,
            bd=0
        )
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.main_scrollbar = tk.Scrollbar(
            self.main_shell,
            orient="vertical",
            command=self.main_canvas.yview,
            width=10,
            relief="flat",
            bd=0,
            bg=self.colors["primary_light"],
            troughcolor=self.colors["background"],
            activebackground=self.colors["primary"]
        )
        # Keep the scrollbar available for long pages. It is visually subtle.
        self.main_scrollbar.pack(side="right", fill="y")

        self.main_area = tk.Frame(
            self.main_canvas,
            bg=self.colors["background"]
        )
        self.main_window = self.main_canvas.create_window(
            (0, 0),
            window=self.main_area,
            anchor="nw"
        )
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_area.bind("<Configure>", self._update_main_scrollregion)
        self.main_canvas.bind("<Configure>", self._resize_main_canvas_window)
        self.main_canvas.bind("<Enter>", self._enable_mousewheel)
        self.main_canvas.bind("<Leave>", self._disable_mousewheel)

        self.create_sidebar()

    def _update_main_scrollregion(self, event=None):
        """Update the scrollable area whenever page content changes."""
        if hasattr(self, "main_canvas") and hasattr(self, "main_area"):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _resize_main_canvas_window(self, event):
        """Keep the content the same width as the visible right panel."""
        if hasattr(self, "main_canvas") and hasattr(self, "main_window"):
            self.main_canvas.itemconfigure(self.main_window, width=event.width)

    def _enable_mousewheel(self, event=None):
        if hasattr(self, "main_canvas"):
            self.main_canvas.bind_all("<MouseWheel>", self._on_main_mousewheel)

    def _disable_mousewheel(self, event=None):
        if hasattr(self, "main_canvas"):
            self.main_canvas.unbind_all("<MouseWheel>")

    def _on_main_mousewheel(self, event):
        if hasattr(self, "main_canvas"):
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_sidebar(self):

        brand = tk.Frame(self.sidebar, bg=self.colors["white"], height=120)
        brand.pack(fill="x")
        brand.pack_propagate(False)
        tk.Label(brand, text="♀", font=("Segoe UI Symbol", 27, "bold"), fg=self.colors["primary"], bg=self.colors["white"]).pack(side="left", padx=(25, 8))
        brand_text = tk.Frame(brand, bg=self.colors["white"])
        brand_text.pack(side="left")
        tk.Label(brand_text, text="SHECONNECT", font=self.fonts["brand"], fg=self.colors["dark_pink"], bg=self.colors["white"]).pack(anchor="w", pady=(22, 0))
        tk.Label(brand_text, text="Women's Business Hub", font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["white"]).pack(anchor="w")

        if self.current_user:
            user_box = tk.Frame(self.sidebar, bg=self.colors["soft_pink"], height=75)
            user_box.pack(fill="x", padx=15, pady=(5, 12))
            user_box.pack_propagate(False)
            name = self.current_user.get("name", "User")
            role = self.current_user.get("role", "customer").capitalize()
            tk.Label(user_box, text=name[:1].upper(), font=("Segoe UI", 14, "bold"), fg=self.colors["white"], bg=self.colors["primary"]).place(x=12, y=15, width=42, height=42)
            tk.Label(user_box, text=name, font=("Segoe UI", 10, "bold"), fg=self.colors["text"], bg=self.colors["soft_pink"]).place(x=65, y=12)
            tk.Label(user_box, text=role, font=("Segoe UI", 9), fg=self.colors["primary"], bg=self.colors["soft_pink"]).place(x=65, y=36)

        if self.current_user and self.current_user.get("role") == "admin":
            nav_items = [
                ("Admin Dashboard", "▦", self.show_admin_dashboard),
                ("User Management", "♙", self.show_admin_users),
                ("Business Management", "⌂", self.show_admin_businesses),
                ("Product Management", "✦", self.show_admin_products),
                ("Category Management", "▤", self.show_admin_categories),
                ("Reports", "▥", self.show_admin_reports),
                ("Enquiries", "✉", self.show_admin_enquiries),
                ("Settings", "⚙", self.show_settings),
                ("Logout", "↪", self.logout),
            ]
        else:
            nav_items = [
                ("Dashboard", "▦", self.show_dashboard),
                ("Discover Businesses", "⌕", self.show_discover),
                ("Products & Services", "▣", self.show_products),
                ("Enquiries", "✉", self.show_enquiries),
                ("Saved Businesses", "♡", self.show_saved),
            ]
            if self.current_user and self.current_user.get("role") == "entrepreneur":
                nav_items += [
                    ("My Businesses", "⌂", self.show_my_businesses),
                    ("My Listings", "✦", self.show_my_listings),
                ]
            nav_items += [("Settings", "⚙", self.show_settings), ("Logout", "↪", self.logout)]
        self.nav_buttons = {}
        nav = tk.Frame(self.sidebar, bg=self.colors["white"])
        nav.pack(fill="both", expand=True, padx=15)
        for text, icon, command in nav_items:
            self.create_nav_button(nav, text, icon, command)

    def create_nav_button(self, parent, text, icon, command):
        button = tk.Button(parent, text=f"  {icon}   {text}", font=self.fonts["navigation"], anchor="w", fg=self.colors["muted"],
                           bg=self.colors["white"], activeforeground=self.colors["primary"], activebackground=self.colors["primary_light"],
                           relief="flat", bd=0, cursor="hand2", padx=14, pady=11, command=command)
        button.pack(fill="x", pady=3)
        self.nav_buttons[text] = button

    def set_active_nav(self, active):
        if not hasattr(self, "nav_buttons"):
            return
        for name, button in self.nav_buttons.items():
            button.configure(bg=self.colors["primary_light"] if name == active else self.colors["white"],
                             fg=self.colors["primary"] if name == active else self.colors["muted"])

    def clear_main(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()
        if hasattr(self, "main_canvas"):
            self.main_canvas.yview_moveto(0)
        self.after_idle(self._update_main_scrollregion)

    def create_page_header(self, title, subtitle):
        header = tk.Frame(self.main_area, bg=self.colors["background"], height=110)
        header.pack(fill="x", padx=40)
        header.pack_propagate(False)
        tk.Label(header, text=title, font=self.fonts["page_heading"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", pady=(28, 2))
        tk.Label(header, text=subtitle, font=self.fonts["subheading"], fg=self.colors["muted"], bg=self.colors["background"]).pack(anchor="w")

    # =========================================================
    # DASHBOARD
    # =========================================================
    def show_dashboard(self):
        self.clear_main(); self.set_active_nav("Dashboard")
        self.create_page_header("Welcome to SHECONNECT", "Discover, connect and grow with women-led businesses.")
        content = tk.Frame(self.main_area, bg=self.colors["background"])
        content.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        hero = tk.Frame(content, bg=self.colors["primary"], height=125)
        hero.pack(fill="x", pady=(0, 18)); hero.pack_propagate(False)
        name = self.current_user.get("name", "there") if self.current_user else "there"
        tk.Label(hero, text=f"Hello, {name} 👋", font=("Segoe UI", 20, "bold"), fg=self.colors["white"], bg=self.colors["primary"]).pack(anchor="w", padx=25, pady=(22, 3))
        tk.Label(hero, text="Your business community is growing. Explore what SHECONNECT has to offer.", font=("Segoe UI", 10), fg="#FCECF3", bg=self.colors["primary"]).pack(anchor="w", padx=25)

        stats = tk.Frame(content, bg=self.colors["background"]); stats.pack(fill="x", pady=(0, 18))
        dashboard_user_id = self.current_user.get("user_id") if self.current_user else None
        dashboard_endpoint = f"/api/dashboard?user_id={dashboard_user_id}" if dashboard_user_id else "/api/dashboard"
        status, data = self.api_request(dashboard_endpoint)
        data = data if status == 200 else {}
        self.create_stat_card(stats, "BUSINESSES", str(data.get("businesses", 0)), "Listed on SHECONNECT")
        self.create_stat_card(stats, "PRODUCTS & SERVICES", str(data.get("products_services", 0)), "Available listings")
        self.create_stat_card(stats, "PENDING ENQUIRIES", str(data.get("pending_enquiries", 0)), "Awaiting response")

        lower = tk.Frame(content, bg=self.colors["background"]); lower.pack(fill="both", expand=True)
        activity = tk.Frame(lower, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1)
        activity.pack(side="left", fill="both", expand=True, padx=(0, 10));
        tk.Label(activity, text="Recent Activity", font=("Segoe UI", 14, "bold"), fg=self.colors["text"], bg=self.colors["card"]).pack(anchor="w", padx=22, pady=(20, 10))
        self.create_activity(activity, "Business discovery", "Explore women-led businesses and services.", "Now")
        self.create_activity(activity, "Customer enquiries", "Keep conversations organized and accessible.", "Now")
        self.create_activity(activity, "MySQL connected", "Your data is loaded from the database.", "Live")

        actions = tk.Frame(lower, bg=self.colors["card"], width=270, highlightbackground=self.colors["border"], highlightthickness=1)
        actions.pack(side="right", fill="y"); actions.pack_propagate(False)
        tk.Label(actions, text="Quick Actions", font=("Segoe UI", 14, "bold"), fg=self.colors["text"], bg=self.colors["card"]).pack(anchor="w", padx=22, pady=(20, 15))
        self.create_action_button(actions, "+  Add Business", self.show_add_business)
        self.create_action_button(actions, "+  Add Product", self.show_add_product)
        self.create_action_button(actions, "✉  View Enquiries", self.show_enquiries)

    def create_stat_card(self, parent, title, number, description):
        card = tk.Frame(parent, bg=self.colors["card"], height=105, highlightbackground=self.colors["border"], highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=5); card.pack_propagate(False)
        tk.Label(card, text=title, font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["card"]).pack(anchor="w", padx=20, pady=(14, 0))
        tk.Label(card, text=number, font=self.fonts["card_number"], fg=self.colors["primary"], bg=self.colors["card"]).pack(anchor="w", padx=20)
        tk.Label(card, text=description, font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["card"]).pack(anchor="w", padx=20)

    def create_activity(self, parent, title, description, time):
        frame = tk.Frame(parent, bg=self.colors["card"]); frame.pack(fill="x", padx=24, pady=7)
        tk.Label(frame, text="●", font=("Segoe UI", 11), fg=self.colors["pink"], bg=self.colors["card"]).pack(side="left", padx=(0, 12))
        tf = tk.Frame(frame, bg=self.colors["card"]); tf.pack(side="left", fill="x", expand=True)
        tk.Label(tf, text=title, font=("Segoe UI", 10, "bold"), fg=self.colors["text"], bg=self.colors["card"]).pack(anchor="w")
        tk.Label(tf, text=description, font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["card"]).pack(anchor="w")
        tk.Label(frame, text=time, font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["card"]).pack(side="right")

    def create_action_button(self, parent, text, command):
        tk.Button(parent, text=text, font=self.fonts["button"], fg=self.colors["primary"], bg=self.colors["primary_light"],
                  activeforeground=self.colors["white"], activebackground=self.colors["primary"], relief="flat", bd=0,
                  anchor="w", padx=18, pady=11, cursor="hand2", command=command).pack(fill="x", padx=18, pady=5)

    # =========================================================
    # SEARCH BOX HELPER
    # =========================================================
    def add_search_placeholder(self, entry, placeholder):
        """Add a clean placeholder that disappears automatically when typing starts."""
        entry.insert(0, placeholder)
        entry.configure(fg=self.colors["muted"])

        def focus_in(event=None):
            if entry.get().strip() == placeholder:
                entry.delete(0, tk.END)
                entry.configure(fg=self.colors["text"])

        def focus_out(event=None):
            if not entry.get().strip():
                entry.insert(0, placeholder)
                entry.configure(fg=self.colors["muted"])

        entry.bind("<FocusIn>", focus_in)
        entry.bind("<FocusOut>", focus_out)
        return entry

    # =========================================================
    # BUSINESSES
    # =========================================================
    def convert_businesses(self, items):
        return [{"id": x.get("business_id"), "owner_id": x.get("user_id"), "name": x.get("business_name") or "Unnamed Business",
                 "category": x.get("category_name") or "Uncategorized", "location": x.get("address") or "Location not provided",
                 "description": x.get("description") or "No description available.", "contact": x.get("contact_number") or "Not provided"} for x in items or []]

    def show_discover(self):
        self.clear_main()
        self.set_active_nav("Discover Businesses")
        self.create_page_header(
            "Discover Businesses",
            "Explore women-led businesses and discover new opportunities."
        )

        content = tk.Frame(self.main_area, bg=self.colors["background"])
        content.pack(fill="both", expand=True, padx=40, pady=(5, 30))

        # Search box
        sf = tk.Frame(
            content,
            bg=self.colors["white"],
            height=55,
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        sf.pack(fill="x", pady=(0, 18))
        sf.pack_propagate(False)

        tk.Label(
            sf, text="⌕", font=("Segoe UI Symbol", 18),
            fg=self.colors["primary"], bg=self.colors["white"]
        ).pack(side="left", padx=(18, 8))

        entry = tk.Entry(
            sf, font=self.fonts["body"], fg=self.colors["text"],
            bg=self.colors["white"], relief="flat", bd=0
        )
        entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.add_search_placeholder(entry, "Search businesses...")

        tk.Button(
            sf, text="Search", font=self.fonts["button"],
            fg=self.colors["white"], bg=self.colors["primary"],
            activebackground=self.colors["primary_dark"],
            relief="flat", bd=0, cursor="hand2", padx=20,
            command=lambda: self.search_businesses(entry.get())
        ).pack(side="right", padx=8)

        # ---------------------------------------------------------
        # CATEGORY STRIP WITH HORIZONTAL SCROLL
        # ---------------------------------------------------------
        tk.Label(
            content, text="Explore by category",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text"], bg=self.colors["background"]
        ).pack(anchor="w", pady=(0, 10))

        category_holder = tk.Frame(content, bg=self.colors["background"])
        category_holder.pack(fill="x", pady=(0, 18))

        category_canvas = tk.Canvas(
            category_holder,
            height=55,
            bg=self.colors["background"],
            highlightthickness=0,
            bd=0
        )
        category_scroll = tk.Scrollbar(
            category_holder,
            orient="horizontal",
            command=category_canvas.xview,
            width=9,
            relief="flat",
            bd=0,
            bg=self.colors["primary_light"],
            troughcolor=self.colors["background"],
            activebackground=self.colors["primary"]
        )
        category_canvas.configure(xscrollcommand=category_scroll.set)
        category_canvas.pack(fill="x")
        category_scroll.pack(fill="x", pady=(3, 0))

        category_inner = tk.Frame(
            category_canvas,
            bg=self.colors["background"]
        )
        category_canvas.create_window(
            (0, 0), window=category_inner, anchor="nw"
        )

        cats = self.get_api_data("/api/categories") or []
        categories = ["All"] + [
            x.get("category_name", "Uncategorized") for x in cats
        ]

        for category in categories:
            tk.Button(
                category_inner,
                text=category,
                font=("Segoe UI", 9, "bold"),
                fg=self.colors["primary"],
                bg=self.colors["primary_light"],
                activeforeground=self.colors["white"],
                activebackground=self.colors["primary"],
                relief="flat", bd=0, cursor="hand2",
                padx=13, pady=8,
                command=lambda c=category: self.filter_businesses(c)
            ).pack(side="left", padx=(0, 7), pady=4)

        def update_category_scroll(event=None):
            category_canvas.configure(
                scrollregion=category_canvas.bbox("all")
            )

        category_inner.bind("<Configure>", update_category_scroll)

        # ---------------------------------------------------------
        # FEATURED BUSINESSES
        # ---------------------------------------------------------
        tk.Label(
            content, text="Featured Businesses",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text"], bg=self.colors["background"]
        ).pack(anchor="w", pady=(0, 10))

        # The business list has its own horizontal scrollbar. The card
        # width is intentionally fixed so the right-side buttons/details
        # never get squeezed or hidden on smaller screens.
        business_holder = tk.Frame(
            content,
            bg=self.colors["background"]
        )
        business_holder.pack(fill="both", expand=True)

        self.business_canvas = tk.Canvas(
            business_holder,
            bg=self.colors["background"],
            highlightthickness=0,
            bd=0,
            height=145
        )
        self.business_scrollbar = tk.Scrollbar(
            business_holder,
            orient="horizontal",
            command=self.business_canvas.xview,
            width=9,
            relief="flat",
            bd=0,
            bg=self.colors["primary_light"],
            troughcolor=self.colors["background"],
            activebackground=self.colors["primary"]
        )
        self.business_canvas.configure(
            xscrollcommand=self.business_scrollbar.set
        )

        self.business_canvas.pack(fill="both", expand=True)
        self.business_scrollbar.pack(fill="x", pady=(4, 0))

        self.business_area = tk.Frame(
            self.business_canvas,
            bg=self.colors["background"],
            width=1150
        )
        self.business_window = self.business_canvas.create_window(
            (0, 0),
            window=self.business_area,
            anchor="nw",
            width=1150
        )

        def update_business_scroll(event=None):
            self.business_canvas.configure(
                scrollregion=self.business_canvas.bbox("all")
            )
            card_count = len(self.business_area.winfo_children())
            required_height = max(145, card_count * 130 + 12)
            self.business_canvas.configure(height=required_height)

        self.business_area.bind("<Configure>", update_business_scroll)

        api_businesses = self.get_api_data("/api/businesses") or []
        self.businesses = self.convert_businesses(api_businesses)
        self.display_businesses(self.businesses)

    def display_businesses(self, businesses):
        for widget in self.business_area.winfo_children():
            widget.destroy()

        if not businesses:
            tk.Label(
                self.business_area,
                text="No businesses found.",
                font=("Segoe UI", 11),
                fg=self.colors["muted"],
                bg=self.colors["background"]
            ).pack(pady=40)
        else:
            for business in businesses:
                self.create_business_card(self.business_area, business)

        # Refresh the horizontal scroll area after filtering/searching.
        if hasattr(self, "business_canvas"):
            self.after_idle(lambda: self.business_canvas.configure(
                scrollregion=self.business_canvas.bbox("all")
            ))

    def create_business_card(self, parent, business):
        card = tk.Frame(parent, bg=self.colors["white"], height=118, highlightbackground=self.colors["border"], highlightthickness=1)
        card.pack(fill="x", pady=6); card.pack_propagate(False)
        tk.Label(card, text="♀", font=("Segoe UI Symbol", 24, "bold"), fg=self.colors["primary"], bg=self.colors["primary_light"]).place(x=18, y=18, width=62, height=62)
        tk.Label(card, text=business["name"], font=("Segoe UI", 12, "bold"), fg=self.colors["text"], bg=self.colors["white"]).place(x=98, y=12)
        tk.Label(card, text=business["category"], font=("Segoe UI", 9, "bold"), fg=self.colors["primary"], bg=self.colors["white"]).place(x=98, y=36)
        tk.Label(card, text=f"⌖  {business['location']}", font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["white"]).place(x=98, y=57)
        tk.Label(card, text=f"☎  {business['contact']}", font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["white"]).place(x=98, y=78)
        tk.Label(card, text=business["description"][:70], font=("Segoe UI", 8), fg=self.colors["muted"], bg=self.colors["white"]).place(x=98, y=96)

        actions = tk.Frame(card, bg=self.colors["white"]); actions.place(relx=0.985, rely=0.5, anchor="e")
        saved = business["id"] in self.saved_businesses
        self.small_action_button(actions, "♥ Saved" if saved else "♡ Save", lambda b=business: self.toggle_saved(b), filled=False).pack(pady=2)
        self.small_action_button(actions, "View", lambda b=business: self.view_business(b), filled=True).pack(pady=2)
        if self.current_user and self.current_user.get("role") == "entrepreneur" and int(business.get("owner_id", -1)) == int(self.current_user.get("user_id", -2)):
            self.small_action_button(actions, "Edit", lambda b=business: self.edit_business(b), filled=False).pack(pady=2)
            self.small_action_button(actions, "Delete", lambda b=business: self.delete_business(b), filled=False, danger=True).pack(pady=2)

    def small_action_button(self, parent, text, command, filled=False, danger=False):
        fg = self.colors["white"] if filled else (self.colors["danger"] if danger else self.colors["primary"])
        bg = self.colors["primary"] if filled else self.colors["primary_light"]
        btn = tk.Button(parent, text=text, command=command, font=("Segoe UI", 8, "bold"), fg=fg, bg=bg, activeforeground=self.colors["white"], activebackground=self.colors["danger"] if danger else self.colors["primary"], relief="flat", bd=0, cursor="hand2", padx=10, pady=4)
        return btn

    def search_businesses(self, text):
        text = text.strip()
        if text.lower() == "search businesses..." or not text:
            self.show_discover(); return
        data = self.get_api_data("/api/businesses/search?q=" + quote(text)) or []
        self.display_businesses(self.convert_businesses(data))

    def filter_businesses(self, category):
        results = self.businesses if category == "All" else [b for b in self.businesses if category.lower() in b["category"].lower()]
        self.display_businesses(results)

    def view_business(self, business):
        products = self.get_api_data(f"/api/businesses/{business['id']}/products") or []
        win = tk.Toplevel(self); win.title(f"{business['name']} — Business Details"); win.geometry("650x560"); win.configure(bg=self.colors["background"]); win.transient(self)
        tk.Label(win,text=business["name"],font=("Segoe UI",21,"bold"),fg=self.colors["text"],bg=self.colors["background"]).pack(anchor="w",padx=35,pady=(28,4))
        tk.Label(win,text=business["category"],font=("Segoe UI",10,"bold"),fg=self.colors["primary"],bg=self.colors["background"]).pack(anchor="w",padx=35)
        info=tk.Frame(win,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1);info.pack(fill="x",padx=35,pady=20)
        tk.Label(info,text=f"⌖  {business['location']}",font=("Segoe UI",10),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=18,pady=(14,6))
        tk.Label(info,text=f"☎  {business['contact']}",font=("Segoe UI",10),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=18,pady=(0,14))
        tk.Label(win,text="About the business",font=("Segoe UI",12,"bold"),fg=self.colors["text"],bg=self.colors["background"]).pack(anchor="w",padx=35)
        tk.Label(win,text=business["description"],font=("Segoe UI",10),fg=self.colors["muted"],bg=self.colors["background"],wraplength=575,justify="left").pack(anchor="w",padx=35,pady=(6,15))
        tk.Label(win,text="Products & Services",font=("Segoe UI",12,"bold"),fg=self.colors["text"],bg=self.colors["background"]).pack(anchor="w",padx=35)
        listing_text="\n".join(f"• {p.get('product_name')} — {('Contact for price' if p.get('price') is None else '₹'+format(float(p.get('price')), ',.2f'))}" for p in products) or "No products or services listed yet."
        tk.Label(win,text=listing_text,font=("Segoe UI",9),fg=self.colors["muted"],bg=self.colors["background"],justify="left",wraplength=575).pack(anchor="w",padx=35,pady=(6,20))
        if self.current_user and self.current_user.get("role")=="customer":
            tk.Button(win,text="Send Enquiry",font=self.fonts["button"],fg=self.colors["white"],bg=self.colors["primary"],activebackground=self.colors["primary_dark"],relief="flat",bd=0,cursor="hand2",padx=18,pady=9,command=lambda:self.enquiry_window(business["id"],business["name"])).pack(anchor="e",padx=35)

    def toggle_saved(self, business):
        business_id = business["id"]
        if business_id in self.saved_businesses:
            self.saved_businesses.remove(business_id); messagebox.showinfo("Saved Businesses", f"{business["name"]} removed from saved businesses.")
        else:
            self.saved_businesses.add(business_id); messagebox.showinfo("Saved Businesses", f"{business["name"]} saved successfully.")
        self.show_discover()

    # =========================================================
    # ENTREPRENEUR MANAGEMENT
    # =========================================================
    def show_my_businesses(self):
        self.clear_main(); self.set_active_nav("My Businesses")
        self.create_page_header("My Businesses", "Manage your business information, contact details and listings.")
        content = tk.Frame(self.main_area, bg=self.colors["background"]); content.pack(fill="both", expand=True, padx=40, pady=(5, 30))
        top = tk.Frame(content, bg=self.colors["background"]); top.pack(fill="x", pady=(0, 15))
        tk.Button(top, text="+ Add Business", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, cursor="hand2", padx=16, pady=8, command=self.show_add_business).pack(side="right")
        area = tk.Frame(content, bg=self.colors["background"]); area.pack(fill="both", expand=True)
        businesses = self.convert_businesses(self.get_api_data(f"/api/users/{self.current_user['user_id']}/businesses/full") or [])
        if not businesses:
            tk.Label(area, text="You have not added a business yet.", font=("Segoe UI", 12), fg=self.colors["muted"], bg=self.colors["background"]).pack(pady=50)
        else:
            for b in businesses: self.create_business_card(area, b)

    def show_my_listings(self):
        self.clear_main(); self.set_active_nav("My Listings")
        self.create_page_header("My Listings", "Edit or remove your products and services whenever you need.")
        content = tk.Frame(self.main_area, bg=self.colors["background"]); content.pack(fill="both", expand=True, padx=40, pady=(5, 30))
        tk.Button(content, text="+ Add Product / Service", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, cursor="hand2", padx=16, pady=8, command=self.show_add_product).pack(anchor="e", pady=(0, 15))
        area = tk.Frame(content, bg=self.colors["background"]); area.pack(fill="both", expand=True)
        rows = self.get_api_data(f"/api/users/{self.current_user['user_id']}/products") or []
        if not rows:
            tk.Label(area, text="No products or services added yet.", font=("Segoe UI", 12), fg=self.colors["muted"], bg=self.colors["background"]).pack(pady=50)
        else:
            for p in rows: self.create_manage_product_card(area, p)

    def create_manage_product_card(self, parent, p):
        card = tk.Frame(parent, bg=self.colors["white"], height=105, highlightbackground=self.colors["border"], highlightthickness=1); card.pack(fill="x", pady=5); card.pack_propagate(False)
        tk.Label(card, text="✦", font=("Segoe UI Symbol", 22, "bold"), fg=self.colors["primary"], bg=self.colors["primary_light"]).place(x=18, y=18, width=60, height=60)
        tk.Label(card, text=p.get("product_name", "Listing"), font=("Segoe UI", 12, "bold"), fg=self.colors["text"], bg=self.colors["white"]).place(x=95, y=16)
        tk.Label(card, text=f"{p.get('business_name','Business')}  •  {str(p.get('product_type','service')).capitalize()}", font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["white"]).place(x=95, y=42)
        price = "Contact for price" if p.get("price") is None else f"₹{float(p['price']):,.2f}"
        tk.Label(card, text=price, font=("Segoe UI", 12, "bold"), fg=self.colors["primary"], bg=self.colors["white"]).place(x=95, y=68)
        actions = tk.Frame(card, bg=self.colors["white"]); actions.place(relx=0.97, rely=0.5, anchor="e")
        self.small_action_button(actions, "Edit", lambda item=p: self.edit_product(item), filled=True).pack(side="left", padx=3)
        self.small_action_button(actions, "Delete", lambda item=p: self.delete_product(item), danger=True).pack(side="left", padx=3)

    def edit_business(self, business):
        cats = self.get_api_data("/api/categories") or []
        win = tk.Toplevel(self); win.title("Edit Business"); win.geometry("560x570"); win.configure(bg=self.colors["background"]); win.transient(self); win.grab_set()
        tk.Label(win, text="Edit Business", font=("Segoe UI", 20, "bold"), fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(25, 18))
        fields = {}; values = [("Business name", business["name"]), ("Description", business["description"]), ("Contact number", business["contact"]), ("Address", business["location"])]
        for label, value in values:
            tk.Label(win, text=label, font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
            e=tk.Entry(win, font=("Segoe UI",10), relief="flat", bd=0, highlightbackground=self.colors["border"], highlightthickness=1); e.pack(fill="x", padx=35, pady=(5,10), ipady=8); e.insert(0,value); fields[label]=e
        tk.Label(win, text="Category", font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
        catvar=tk.StringVar(value=business["category"]); tk.OptionMenu(win, catvar, *[c["category_name"] for c in cats]).pack(fill="x", padx=35, pady=(5,18))
        def save():
            cat=next((c for c in cats if c["category_name"]==catvar.get()),None)
            payload={"user_id":self.current_user["user_id"],"business_name":fields["Business name"].get().strip(),"description":fields["Description"].get().strip(),"contact_number":fields["Contact number"].get().strip(),"address":fields["Address"].get().strip(),"category_id":cat["category_id"]}
            status,data=self.api_request(f"/api/businesses/{business['id']}","PUT",payload)
            if status==200: win.destroy(); messagebox.showinfo("Business", "Business updated successfully."); self.show_my_businesses()
            else: messagebox.showerror("Update failed", data.get("error","Unable to update business."))
        tk.Button(win,text="Save Changes",font=self.fonts["button"],fg=self.colors["white"],bg=self.colors["primary"],activebackground=self.colors["primary_dark"],relief="flat",bd=0,cursor="hand2",pady=10,command=save).pack(fill="x",padx=35)

    def delete_business(self, business):
        if not messagebox.askyesno("Delete Business", f"Delete '{business['name']}'? Its products/services will also be removed."): return
        status,data=self.api_request(f"/api/businesses/{business['id']}","DELETE",{"user_id":self.current_user["user_id"]})
        if status==200: messagebox.showinfo("Business", "Business deleted successfully."); self.show_my_businesses()
        else: messagebox.showerror("Delete failed", data.get("error","Unable to delete business."))

    def edit_product(self, p):
        win=tk.Toplevel(self); win.title("Edit Product / Service"); win.geometry("540x520"); win.configure(bg=self.colors["background"]); win.transient(self); win.grab_set()
        tk.Label(win,text="Edit Product / Service",font=("Segoe UI",20,"bold"),fg=self.colors["text"],bg=self.colors["background"]).pack(anchor="w",padx=35,pady=(25,18))
        entries={}
        for label,value in [("Product / service name",p.get("product_name","")),("Description",p.get("description") or ""),("Price", "" if p.get("price") is None else str(p.get("price")))]:
            tk.Label(win,text=label,font=self.fonts["body_bold"],fg=self.colors["text"],bg=self.colors["background"]).pack(anchor="w",padx=35)
            e=tk.Entry(win,font=("Segoe UI",10),relief="flat",bd=0,highlightbackground=self.colors["border"],highlightthickness=1);e.pack(fill="x",padx=35,pady=(5,12),ipady=8);e.insert(0,value);entries[label]=e
        tk.Label(win,text="Type",font=self.fonts["body_bold"],fg=self.colors["text"],bg=self.colors["background"]).pack(anchor="w",padx=35)
        typ=tk.StringVar(value=str(p.get("product_type","service")));tk.OptionMenu(win,typ,"product","service").pack(fill="x",padx=35,pady=(5,18))
        def save():
            payload={"user_id":self.current_user["user_id"],"product_name":entries["Product / service name"].get().strip(),"description":entries["Description"].get().strip(),"price":entries["Price"].get().strip() or None,"product_type":typ.get()}
            status,data=self.api_request(f"/api/products/{p['product_id']}","PUT",payload)
            if status==200: win.destroy();messagebox.showinfo("Listing","Listing updated successfully.");self.show_my_listings()
            else: messagebox.showerror("Update failed",data.get("error","Unable to update listing."))
        tk.Button(win,text="Save Changes",font=self.fonts["button"],fg=self.colors["white"],bg=self.colors["primary"],activebackground=self.colors["primary_dark"],relief="flat",bd=0,cursor="hand2",pady=10,command=save).pack(fill="x",padx=35)

    def delete_product(self,p):
        if not messagebox.askyesno("Delete Listing",f"Delete '{p.get('product_name','this listing')}'?"): return
        status,data=self.api_request(f"/api/products/{p['product_id']}","DELETE",{"user_id":self.current_user["user_id"]})
        if status==200: messagebox.showinfo("Listing","Listing deleted successfully.");self.show_my_listings()
        else: messagebox.showerror("Delete failed",data.get("error","Unable to delete listing."))

    # =========================================================
    # PRODUCTS
    # =========================================================
    def convert_products(self, items):
        result = []
        for x in items or []:
            price = x.get("price")
            price_text = "Contact for price" if price is None else f"₹{price:,.2f}"
            result.append({"id": x.get("product_id"), "name": x.get("product_name") or "Unnamed Listing", "business": x.get("business_name") or "Unknown Business", "type": str(x.get("product_type") or "product").capitalize(), "price": price_text, "business_id": x.get("business_id")})
        return result

    def show_products(self):
        self.clear_main(); self.set_active_nav("Products & Services")
        self.create_page_header("Products & Services", "Explore products and services offered by women-led businesses.")
        content = tk.Frame(self.main_area, bg=self.colors["background"]); content.pack(fill="both", expand=True, padx=40, pady=(5, 30))
        sf = tk.Frame(content, bg=self.colors["white"], height=55, highlightbackground=self.colors["border"], highlightthickness=1); sf.pack(fill="x", pady=(0, 20)); sf.pack_propagate(False)
        tk.Label(sf, text="⌕", font=("Segoe UI Symbol", 18), fg=self.colors["primary"], bg=self.colors["white"]).pack(side="left", padx=(18, 8))
        entry = tk.Entry(sf, font=self.fonts["body"], fg=self.colors["text"], bg=self.colors["white"], relief="flat", bd=0); entry.pack(side="left", fill="x", expand=True, ipady=8); self.add_search_placeholder(entry, "Search products or services...")
        tk.Button(sf, text="Search", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, cursor="hand2", padx=18, command=lambda: self.search_products(entry.get())).pack(side="right", padx=8)
        tk.Label(content, text="Available Listings", font=("Segoe UI", 14, "bold"), fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", pady=(0, 10))
        self.product_area = tk.Frame(content, bg=self.colors["background"]); self.product_area.pack(fill="both", expand=True)
        self.products = self.convert_products(self.get_api_data("/api/products") or [])
        self.display_products(self.products)

    def display_products(self, products):
        for widget in self.product_area.winfo_children(): widget.destroy()
        if not products:
            tk.Label(self.product_area, text="No products or services found.", font=("Segoe UI", 11), fg=self.colors["muted"], bg=self.colors["background"]).pack(pady=40); return
        for product in products: self.create_product_card(self.product_area, product)

    def create_product_card(self, parent, product):
        card = tk.Frame(parent, bg=self.colors["white"], height=105, highlightbackground=self.colors["border"], highlightthickness=1); card.pack(fill="x", pady=5); card.pack_propagate(False)
        tk.Label(card, text="▣", font=("Segoe UI Symbol", 23, "bold"), fg=self.colors["primary"], bg=self.colors["primary_light"]).place(x=18, y=18, width=62, height=62)
        tk.Label(card, text=product["name"], font=("Segoe UI", 12, "bold"), fg=self.colors["text"], bg=self.colors["white"]).place(x=98, y=17)
        tk.Label(card, text=product["business"], font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["white"]).place(x=98, y=43)
        tk.Label(card, text=product["type"], font=("Segoe UI", 8, "bold"), fg=self.colors["primary"], bg=self.colors["primary_light"], padx=8).place(x=98, y=68)
        tk.Label(card, text=product["price"], font=("Segoe UI", 13, "bold"), fg=self.colors["primary"], bg=self.colors["white"]).place(relx=0.80, rely=0.38, anchor="center")
        tk.Button(card, text="Make Enquiry", font=("Segoe UI", 9, "bold"), fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, cursor="hand2", padx=12, pady=6, command=lambda p=product: self.open_enquiry_form(p)).place(relx=0.90, rely=0.70, anchor="center")

    def search_products(self, text):
        text = text.strip()
        if text.lower() == "search products or services..." or not text:
            self.show_products(); return
        data = self.get_api_data("/api/products/search?q=" + quote(text)) or []
        self.display_products(self.convert_products(data))

    # =========================================================
    # ENQUIRIES
    # =========================================================
    def show_enquiries(self):
        self.clear_main()
        self.set_active_nav("Enquiries")
        self.create_page_header(
            "Enquiries",
            "Manage customer enquiries and keep conversations organized."
        )

        content = tk.Frame(self.main_area, bg=self.colors["background"])
        content.pack(fill="both", expand=True, padx=40, pady=(5, 30))

        # Load REAL enquiries from Flask/MySQL.
        user_id = self.current_user.get("user_id") if self.current_user else None
        enquiries = []
        if user_id:
            enquiries = self.get_api_data(
                f"/api/enquiries?user_id={user_id}"
            ) or []

        # Summary cards
        summary = tk.Frame(content, bg=self.colors["background"])
        summary.pack(fill="x", pady=(0, 20))

        for title in ["Pending", "Replied", "Closed"]:
            count = sum(
                1 for e in enquiries
                if str(e.get("status", "")).lower() == title.lower()
            )
            self.create_small_summary(summary, title, str(count))

        # Main enquiry card
        box = tk.Frame(
            content,
            bg=self.colors["white"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        box.pack(fill="both", expand=True)

        tk.Label(
            box,
            text="Recent Enquiries",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text"],
            bg=self.colors["white"]
        ).pack(anchor="w", padx=25, pady=(20, 15))

        if not enquiries:
            tk.Label(
                box,
                text="No enquiries found.",
                font=("Segoe UI", 10),
                fg=self.colors["muted"],
                bg=self.colors["white"]
            ).pack(pady=35)
        else:
            for enquiry in enquiries:
                self.create_enquiry(box, enquiry)

    def create_small_summary(self, parent, title, number):
        card = tk.Frame(
            parent,
            bg=self.colors["white"],
            height=85,
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        card.pack(side="left", fill="both", expand=True, padx=5)
        card.pack_propagate(False)

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 9),
            fg=self.colors["muted"],
            bg=self.colors["white"]
        ).pack(anchor="w", padx=18, pady=(12, 0))

        tk.Label(
            card,
            text=number,
            font=("Segoe UI", 20, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["white"]
        ).pack(anchor="w", padx=18)

    def create_enquiry(self, parent, enquiry):
        name = enquiry.get("customer_name") or "Unknown Customer"
        subject = enquiry.get("subject") or "No subject"
        business = enquiry.get("business_name") or "Unknown Business"
        status = str(enquiry.get("status") or "pending").capitalize()
        reply = str(enquiry.get("reply_message") or "").strip()

        frame = tk.Frame(
            parent,
            bg=self.colors["white"],
            height=112,
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        frame.pack(fill="x", padx=22, pady=5)
        frame.pack_propagate(False)

        # Customer avatar
        tk.Label(
            frame,
            text=name[:1].upper(),
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"]
        ).place(x=12, y=20, width=42, height=42)

        tk.Label(
            frame,
            text=name,
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"],
            bg=self.colors["white"]
        ).place(x=68, y=10)

        tk.Label(
            frame,
            text=subject[:55],
            font=("Segoe UI", 9),
            fg=self.colors["muted"],
            bg=self.colors["white"]
        ).place(x=68, y=34)

        tk.Label(
            frame,
            text=business,
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["white"]
        ).place(x=68, y=57)

        # Show a short reply preview when a reply exists.
        if reply:
            preview = "Response: " + reply.replace("\n", " ")
            tk.Label(
                frame,
                text=preview[:75],
                font=("Segoe UI", 8),
                fg=self.colors["success"],
                bg=self.colors["white"]
            ).place(x=68, y=78)

        status_lower = status.lower()
        if status_lower == "pending":
            status_color = self.colors["warning"]
        elif status_lower == "replied":
            status_color = self.colors["success"]
        else:
            status_color = self.colors["muted"]

        tk.Label(
            frame,
            text=status,
            font=("Segoe UI", 8, "bold"),
            fg=status_color,
            bg=self.colors["white"]
        ).place(relx=0.68, y=18, anchor="center")

        # Entrepreneur gets View + Reply + Close.
        if self.current_user and self.current_user.get("role") == "entrepreneur":
            actions = tk.Frame(frame, bg=self.colors["white"])
            actions.place(relx=0.99, rely=0.72, anchor="e")

            self.small_action_button(
                actions,
                "View",
                lambda e=enquiry: self.view_enquiry(e),
                filled=False
            ).pack(side="left", padx=2)

            self.small_action_button(
                actions,
                "Reply",
                lambda e=enquiry: self.reply_to_enquiry(e),
                filled=True
            ).pack(side="left", padx=2)

            self.small_action_button(
                actions,
                "Close",
                lambda eid=enquiry.get("enquiry_id"): self.update_enquiry_status(eid, "closed"),
                danger=True
            ).pack(side="left", padx=2)

            self.small_action_button(
                actions,
                "Delete",
                lambda eid=enquiry.get("enquiry_id"): self.delete_enquiry(eid),
                danger=True
            ).pack(side="left", padx=2)
        else:
            # Customer can view, edit and delete their own enquiry.
            actions = tk.Frame(frame, bg=self.colors["white"])
            actions.place(relx=0.99, rely=0.72, anchor="e")

            self.small_action_button(
                actions,
                "View",
                lambda e=enquiry: self.view_enquiry(e),
                filled=False
            ).pack(side="left", padx=2)

            self.small_action_button(
                actions,
                "Edit",
                lambda e=enquiry: self.edit_enquiry(e),
                filled=True
            ).pack(side="left", padx=2)

            self.small_action_button(
                actions,
                "Delete",
                lambda eid=enquiry.get("enquiry_id"): self.delete_enquiry(eid),
                danger=True
            ).pack(side="left", padx=2)

    def view_enquiry(self, enquiry):
        business = enquiry.get("business_name", "")
        subject = enquiry.get("subject", "")
        message = enquiry.get("message", "")
        status = str(enquiry.get("status", "pending")).capitalize()
        reply = str(enquiry.get("reply_message") or "").strip()
        replied_at = enquiry.get("replied_at") or ""

        details = (
            f"Business: {business}\n\n"
            f"Subject: {subject}\n\n"
            f"Your Enquiry:\n{message}\n\n"
            f"Status: {status}"
        )

        if reply:
            details += f"\n\nEntrepreneur Response:\n{reply}"
            if replied_at:
                details += f"\n\nReplied at: {replied_at}"
        else:
            details += "\n\nEntrepreneur Response:\nNo response yet."

        messagebox.showinfo("Enquiry Details", details)

    def reply_to_enquiry(self, enquiry):
        """Open a real reply window and save the reply in MySQL through Flask."""
        if not self.current_user or self.current_user.get("role") != "entrepreneur":
            messagebox.showwarning(
                "Reply",
                "Only an entrepreneur can reply to customer enquiries."
            )
            return

        enquiry_id = enquiry.get("enquiry_id")
        customer_name = enquiry.get("customer_name") or "Customer"
        business_name = enquiry.get("business_name") or "Your Business"
        subject = enquiry.get("subject") or "Enquiry"
        old_reply = str(enquiry.get("reply_message") or "")

        win = tk.Toplevel(self)
        win.title("Reply to Customer")
        win.geometry("620x560")
        win.minsize(560, 500)
        win.configure(bg=self.colors["background"])
        win.transient(self)
        win.grab_set()

        header = tk.Frame(win, bg=self.colors["primary"], height=105)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Reply to Customer",
            font=("Segoe UI", 19, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"]
        ).pack(anchor="w", padx=28, pady=(18, 2))

        tk.Label(
            header,
            text=f"To: {customer_name}  •  {business_name}",
            font=("Segoe UI", 10),
            fg="#FCEAF2",
            bg=self.colors["primary"]
        ).pack(anchor="w", padx=28)

        body = tk.Frame(win, bg=self.colors["background"])
        body.pack(fill="both", expand=True, padx=28, pady=20)

        tk.Label(
            body,
            text="Customer enquiry",
            font=self.fonts["body_bold"],
            fg=self.colors["text"],
            bg=self.colors["background"]
        ).pack(anchor="w")

        tk.Label(
            body,
            text=subject,
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["background"]
        ).pack(anchor="w", pady=(3, 5))

        enquiry_message = tk.Text(
            body,
            height=5,
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            bg="#FFFCFE",
            fg=self.colors["muted"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            wrap="word"
        )
        enquiry_message.pack(fill="x", pady=(0, 16))
        enquiry_message.insert("1.0", enquiry.get("message", ""))
        enquiry_message.config(state="disabled")

        tk.Label(
            body,
            text="Your response",
            font=self.fonts["body_bold"],
            fg=self.colors["text"],
            bg=self.colors["background"]
        ).pack(anchor="w")

        reply_box = tk.Text(
            body,
            height=9,
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            bg=self.colors["white"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            wrap="word"
        )
        reply_box.pack(fill="both", expand=True, pady=(6, 14))

        if old_reply:
            reply_box.insert("1.0", old_reply)

        buttons = tk.Frame(body, bg=self.colors["background"])
        buttons.pack(fill="x")

        tk.Button(
            buttons,
            text="Cancel",
            font=self.fonts["button"],
            fg=self.colors["text"],
            bg=self.colors["white"],
            activebackground=self.colors["primary_light"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=9,
            command=win.destroy
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            buttons,
            text="Send Reply",
            font=self.fonts["button"],
            fg=self.colors["white"],
            bg=self.colors["primary"],
            activebackground=self.colors["primary_dark"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=9,
            command=lambda: self.send_enquiry_reply(
                win,
                enquiry_id,
                reply_box.get("1.0", "end").strip()
            )
        ).pack(side="right")

        reply_box.focus_set()

    def send_enquiry_reply(self, win, enquiry_id, reply_message):
        reply_message = reply_message.strip()

        if not reply_message:
            messagebox.showwarning(
                "Reply",
                "Please type a response before sending."
            )
            return

        payload = {
            "user_id": self.current_user.get("user_id"),
            "status": "replied",
            "reply_message": reply_message
        }

        api_status, data = self.api_request(
            f"/api/enquiries/{enquiry_id}",
            "PUT",
            payload
        )

        if api_status == 200 and data.get("success"):
            win.destroy()
            messagebox.showinfo(
                "Reply Sent",
                "Your response has been sent to the customer successfully."
            )
            self.show_enquiries()
        else:
            messagebox.showerror(
                "Reply Failed",
                data.get("error", "Unable to send the response.")
            )

    def edit_enquiry(self, enquiry):
        """Allow a customer to edit their enquiry."""
        if not self.current_user or self.current_user.get("role") != "customer":
            messagebox.showwarning(
                "Edit Enquiry",
                "Only customers can edit enquiries they have sent."
            )
            return

        enquiry_id = enquiry.get("enquiry_id")
        subject = str(enquiry.get("subject") or "").strip()
        message = str(enquiry.get("message") or "").strip()
        status = str(enquiry.get("status") or "pending").lower()
        old_reply = str(enquiry.get("reply_message") or "").strip()

        warning = ""
        if old_reply or status in ("replied", "closed"):
            warning = (
                "\n\nThis enquiry already has a response or is closed. "
                "Editing it will clear the old response and send it back to Pending. "
            )

        win = tk.Toplevel(self)
        win.title("Edit Enquiry")
        win.geometry("620x500")
        win.minsize(560, 450)
        win.configure(bg=self.colors["background"])
        win.transient(self)
        win.grab_set()

        header = tk.Frame(win, bg=self.colors["primary"], height=95)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Edit Enquiry",
            font=("Segoe UI", 19, "bold"),
            fg=self.colors["white"],
            bg=self.colors["primary"]
        ).pack(anchor="w", padx=28, pady=(18, 2))

        tk.Label(
            header,
            text=enquiry.get("business_name") or "Business",
            font=("Segoe UI", 10),
            fg="#FCEAF2",
            bg=self.colors["primary"]
        ).pack(anchor="w", padx=28)

        body = tk.Frame(win, bg=self.colors["background"])
        body.pack(fill="both", expand=True, padx=28, pady=18)

        tk.Label(
            body, text="Subject", font=self.fonts["body_bold"],
            fg=self.colors["text"], bg=self.colors["background"]
        ).pack(anchor="w")

        subject_box = tk.Entry(
            body, font=("Segoe UI", 10), relief="flat", bd=0,
            bg=self.colors["white"], fg=self.colors["text"],
            insertbackground=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        subject_box.pack(fill="x", ipady=9, pady=(5, 14))
        subject_box.insert(0, subject)

        tk.Label(
            body, text="Message", font=self.fonts["body_bold"],
            fg=self.colors["text"], bg=self.colors["background"]
        ).pack(anchor="w")

        message_box = tk.Text(
            body, height=9, font=("Segoe UI", 10), relief="flat", bd=0,
            bg=self.colors["white"], fg=self.colors["text"],
            insertbackground=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1, wrap="word"
        )
        message_box.pack(fill="both", expand=True, pady=(5, 8))
        message_box.insert("1.0", message)

        if warning:
            tk.Label(
                body, text=warning.strip(), justify="left", wraplength=540,
                font=("Segoe UI", 8), fg=self.colors["warning"],
                bg=self.colors["background"]
            ).pack(anchor="w", pady=(0, 8))

        buttons = tk.Frame(body, bg=self.colors["background"])
        buttons.pack(fill="x")

        tk.Button(
            buttons, text="Cancel", font=self.fonts["button"],
            fg=self.colors["text"], bg=self.colors["white"],
            activebackground=self.colors["primary_light"], relief="flat", bd=0,
            cursor="hand2", padx=18, pady=9, command=win.destroy
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            buttons, text="Save Changes", font=self.fonts["button"],
            fg=self.colors["white"], bg=self.colors["primary"],
            activebackground=self.colors["primary_dark"], relief="flat", bd=0,
            cursor="hand2", padx=20, pady=9,
            command=lambda: self.save_enquiry_edit(
                win, enquiry_id, subject_box.get().strip(),
                message_box.get("1.0", "end").strip(),
                bool(old_reply or status in ("replied", "closed"))
            )
        ).pack(side="right")

        subject_box.focus_set()

    def save_enquiry_edit(self, win, enquiry_id, subject, message, resets_reply=False):
        if not subject or not message:
            messagebox.showwarning(
                "Edit Enquiry",
                "Please enter both a subject and message."
            )
            return

        if resets_reply:
            confirm = messagebox.askyesno(
                "Edit Enquiry",
                "This enquiry already has a response or is closed.\n\n"
                "Saving changes will clear the old response and return the enquiry to Pending.\n\n"
                "Do you want to continue?"
            )
            if not confirm:
                return

        payload = {
            "user_id": self.current_user.get("user_id"),
            "action": "edit",
            "subject": subject,
            "message": message
        }

        api_status, data = self.api_request(
            f"/api/enquiries/{enquiry_id}", "PUT", payload
        )

        if api_status == 200 and data.get("success"):
            win.destroy()
            messagebox.showinfo(
                "Enquiry Updated",
                data.get("message", "Enquiry updated successfully.")
            )
            self.show_enquiries()
        else:
            messagebox.showerror(
                "Edit Failed",
                data.get("error", "Unable to update the enquiry.")
            )

    def delete_enquiry(self, enquiry_id):
        if not enquiry_id:
            messagebox.showerror("Delete Enquiry", "Invalid enquiry ID.")
            return

        confirm = messagebox.askyesno(
            "Delete Enquiry",
            "Are you sure you want to permanently delete this enquiry?\n\n"
            "This action cannot be undone."
        )
        if not confirm:
            return

        user_id = self.current_user.get("user_id")
        api_status, data = self.api_request(
            f"/api/enquiries/{enquiry_id}?user_id={user_id}",
            "DELETE"
        )

        if api_status == 200 and data.get("success"):
            messagebox.showinfo(
                "Enquiry Deleted",
                data.get("message", "Enquiry deleted successfully.")
            )
            self.show_enquiries()
        else:
            server_error = data.get("error", "Unable to delete the enquiry.")
            if api_status is not None:
                server_error = f"{server_error}\n\nServer status: {api_status}"
            messagebox.showerror(
                "Delete Failed",
                server_error
            )

    def update_enquiry_status(self, enquiry_id, status):
        if not enquiry_id:
            messagebox.showerror("Enquiry", "Invalid enquiry ID.")
            return

        if status == "closed":
            confirm = messagebox.askyesno(
                "Close Enquiry",
                "Are you sure you want to close this enquiry?"
            )
            if not confirm:
                return

        payload = {
            "user_id": self.current_user.get("user_id"),
            "status": status
        }

        api_status, data = self.api_request(
            f"/api/enquiries/{enquiry_id}",
            "PUT",
            payload
        )

        if api_status == 200:
            messagebox.showinfo(
                "Enquiry",
                data.get("message", "Enquiry updated.")
            )
            self.show_enquiries()
        else:
            messagebox.showerror(
                "Enquiry",
                data.get("error", "Unable to update enquiry.")
            )

    def open_enquiry_form(self, product):
        if not self.current_user or self.current_user.get("role") != "customer":
            messagebox.showwarning(
                "Customer enquiry",
                "Please log in with a customer account to send an enquiry."
            )
            return

        self.enquiry_window(
            product.get("business_id"),
            product.get("business"),
            product.get("name")
        )

    def enquiry_window(self, business_id, business_name, product_name=""):
        win = tk.Toplevel(self)
        win.title("Make Enquiry")
        win.geometry("500x470")
        win.configure(bg=self.colors["background"])
        win.transient(self)
        win.grab_set()

        tk.Label(
            win,
            text="Make an Enquiry",
            font=("Segoe UI", 19, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"]
        ).pack(anchor="w", padx=35, pady=(30, 3))

        tk.Label(
            win,
            text=f"To: {business_name}",
            font=self.fonts["subheading"],
            fg=self.colors["primary"],
            bg=self.colors["background"]
        ).pack(anchor="w", padx=35, pady=(0, 20))

        tk.Label(
            win,
            text="Subject",
            font=self.fonts["body_bold"],
            fg=self.colors["text"],
            bg=self.colors["background"]
        ).pack(anchor="w", padx=35)

        subject = tk.Entry(
            win,
            font=self.fonts["body"],
            relief="flat",
            bd=0,
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        subject.pack(fill="x", padx=35, pady=(6, 15), ipady=9)
        subject.insert(
            0,
            f"Enquiry about {product_name}" if product_name else "Business enquiry"
        )

        tk.Label(
            win,
            text="Message",
            font=self.fonts["body_bold"],
            fg=self.colors["text"],
            bg=self.colors["background"]
        ).pack(anchor="w", padx=35)

        msg = tk.Text(
            win,
            font=self.fonts["body"],
            height=9,
            relief="flat",
            bd=0,
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        msg.pack(fill="both", expand=True, padx=35, pady=(6, 20))

        tk.Button(
            win,
            text="Send Enquiry",
            font=self.fonts["button"],
            fg=self.colors["white"],
            bg=self.colors["primary"],
            activebackground=self.colors["primary_dark"],
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10,
            command=lambda: self.submit_enquiry(
                win,
                business_id,
                subject.get(),
                msg.get("1.0", "end").strip()
            )
        ).pack(fill="x", padx=35, pady=(0, 25))

    def submit_enquiry(self, win, business_id, subject, message):
        subject = subject.strip()
        message = message.strip()

        if not subject or not message:
            messagebox.showwarning(
                "Enquiry",
                "Please enter both subject and message."
            )
            return

        payload = {
            "customer_id": self.current_user.get("user_id"),
            "business_id": business_id,
            "subject": subject,
            "message": message
        }

        status, data = self.api_request(
            "/api/enquiries",
            "POST",
            payload
        )

        if status == 201:
            win.destroy()
            messagebox.showinfo(
                "Enquiry",
                "Your enquiry was sent successfully."
            )
            self.show_enquiries()
        else:
            messagebox.showerror(
                "Enquiry failed",
                data.get("error", "Unable to send enquiry.")
            )

    # =========================================================
    # SAVED / SETTINGS
    # =========================================================
    def show_saved(self):
        self.clear_main(); self.set_active_nav("Saved Businesses")
        self.create_page_header("Saved Businesses", "Quickly access the businesses you are interested in.")
        content = tk.Frame(self.main_area, bg=self.colors["background"]); content.pack(fill="both", expand=True, padx=40, pady=(5, 30))
        saved = [b for b in self.businesses if b["id"] in self.saved_businesses]
        if not saved:
            empty = tk.Frame(content, bg=self.colors["white"], highlightbackground=self.colors["border"], highlightthickness=1); empty.pack(fill="both", expand=True)
            tk.Label(empty, text="♡", font=("Segoe UI Symbol", 38), fg=self.colors["primary"], bg=self.colors["white"]).pack(pady=(100, 10))
            tk.Label(empty, text="No saved businesses yet", font=("Segoe UI", 16, "bold"), fg=self.colors["text"], bg=self.colors["white"]).pack()
            tk.Label(empty, text="Visit Discover Businesses and save businesses you like.", font=("Segoe UI", 10), fg=self.colors["muted"], bg=self.colors["white"]).pack(pady=8)
            tk.Button(empty, text="Discover Businesses", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, cursor="hand2", padx=18, pady=9, command=self.show_discover).pack(pady=15)
        else:
            for b in saved: self.create_business_card(content, b)

    def show_settings(self):
        self.clear_main(); self.set_active_nav("Settings")
        self.create_page_header("Settings", "Manage your SHECONNECT account and application preferences.")
        content = tk.Frame(self.main_area, bg=self.colors["background"]); content.pack(fill="both", expand=True, padx=40, pady=(5, 30))
        self.create_setting_card(content, "Account Information", f"{self.current_user.get('name')} • {self.current_user.get('email')}")
        self.create_setting_card(content, "Account Type", self.current_user.get("role", "customer").capitalize())
        self.create_setting_card(content, "Privacy & Security", "Change your password and keep your account secure.")
        self.create_setting_card(content, "Application Preferences", "SHECONNECT desktop application settings.")

    def create_setting_card(self, parent, title, description):
        card = tk.Frame(parent, bg=self.colors["white"], height=82, highlightbackground=self.colors["border"], highlightthickness=1)
        card.pack(fill="x", pady=6)
        card.pack_propagate(False)
        tk.Label(card, text="⚙", font=("Segoe UI Symbol", 17), fg=self.colors["primary"], bg=self.colors["primary_light"]).place(x=18, y=17, width=48, height=48)
        tk.Label(card, text=title, font=("Segoe UI", 11, "bold"), fg=self.colors["text"], bg=self.colors["white"]).place(x=85, y=15)
        tk.Label(card, text=description, font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["white"]).place(x=85, y=41)
        tk.Button(card, text="Manage", font=("Segoe UI", 9, "bold"), fg=self.colors["primary"], bg=self.colors["primary_light"], activeforeground=self.colors["white"], activebackground=self.colors["primary"], relief="flat", bd=0, cursor="hand2", padx=13, pady=6, command=lambda t=title: self.open_setting_option(t)).place(relx=0.91, rely=0.5, anchor="center")

    def open_setting_option(self, title):
        if title == "Account Information":
            self.edit_account_information()
        elif title == "Account Type":
            messagebox.showinfo("Account Type", f"Your SHECONNECT account type is: {self.current_user.get('role', 'customer').capitalize()}\n\nAccount type is controlled by the system and cannot be changed here.")
        elif title == "Privacy & Security":
            self.change_password()
        elif title == "Application Preferences":
            messagebox.showinfo("Application Preferences", "Your professional SHECONNECT theme and desktop preferences are currently active.")

    def edit_account_information(self):
        win = tk.Toplevel(self)
        win.title("Edit Account Information")
        win.geometry("520x420")
        win.configure(bg=self.colors["background"])
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Edit Account Information", font=("Segoe UI", 20, "bold"), fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(28, 6))
        tk.Label(win, text="Update your name or email address.", font=self.fonts["body"], fg=self.colors["muted"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(0, 22))

        fields = {}
        for label, value in [("Name", self.current_user.get("name", "")), ("Email", self.current_user.get("email", ""))]:
            tk.Label(win, text=label, font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
            entry = tk.Entry(win, font=self.fonts["body"], relief="flat", bd=0, highlightbackground=self.colors["border"], highlightthickness=1)
            entry.pack(fill="x", padx=35, pady=(5, 14), ipady=8)
            entry.insert(0, value)
            fields[label] = entry

        tk.Button(win, text="Save Changes", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, cursor="hand2", pady=10, command=lambda: self.save_account_information(win, fields)).pack(fill="x", padx=35, pady=(4, 10))
        tk.Button(win, text="Cancel", font=self.fonts["button"], fg=self.colors["primary"], bg=self.colors["primary_light"], activebackground=self.colors["soft_pink"], relief="flat", bd=0, cursor="hand2", pady=9, command=win.destroy).pack(fill="x", padx=35)

    def save_account_information(self, win, fields):
        name = fields["Name"].get().strip()
        email = fields["Email"].get().strip().lower()
        if not name or not email or "@" not in email:
            messagebox.showwarning("Update Account", "Please enter a valid name and email address.", parent=win)
            return

        payload = {
            "request_user_id": self.current_user["user_id"],
            "name": name,
            "email": email
        }
        status, data = self.api_request(f"/api/users/{self.current_user['user_id']}", "PUT", payload)
        if status == 200 and data.get("success"):
            self.current_user = data.get("user", self.current_user)
            win.destroy()
            messagebox.showinfo("Account Updated", "Your account information has been updated successfully.")
            self.show_settings()
        else:
            messagebox.showerror("Update Account", data.get("error", "Unable to update your account."), parent=win)

    def change_password(self):
        win = tk.Toplevel(self)
        win.title("Change Password")
        win.geometry("520x430")
        win.configure(bg=self.colors["background"])
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Change Password", font=("Segoe UI", 20, "bold"), fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(28, 6))
        tk.Label(win, text="Enter your current password before choosing a new one.", font=self.fonts["body"], fg=self.colors["muted"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(0, 22))

        entries = {}
        for label in ["Current Password", "New Password", "Confirm New Password"]:
            tk.Label(win, text=label, font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
            entry = tk.Entry(win, font=self.fonts["body"], show="•", relief="flat", bd=0, highlightbackground=self.colors["border"], highlightthickness=1)
            entry.pack(fill="x", padx=35, pady=(5, 12), ipady=8)
            entries[label] = entry

        tk.Button(win, text="Update Password", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, cursor="hand2", pady=10, command=lambda: self.save_new_password(win, entries)).pack(fill="x", padx=35, pady=(6, 10))
        tk.Button(win, text="Cancel", font=self.fonts["button"], fg=self.colors["primary"], bg=self.colors["primary_light"], activebackground=self.colors["soft_pink"], relief="flat", bd=0, cursor="hand2", pady=9, command=win.destroy).pack(fill="x", padx=35)

    def save_new_password(self, win, entries):
        current_password = entries["Current Password"].get()
        new_password = entries["New Password"].get()
        confirm_password = entries["Confirm New Password"].get()
        if not current_password or not new_password or not confirm_password:
            messagebox.showwarning("Change Password", "Please fill in all password fields.", parent=win)
            return
        if len(new_password) < 6:
            messagebox.showwarning("Change Password", "New password must be at least 6 characters.", parent=win)
            return
        if new_password != confirm_password:
            messagebox.showwarning("Change Password", "New passwords do not match.", parent=win)
            return

        payload = {
            "request_user_id": self.current_user["user_id"],
            "name": self.current_user.get("name", ""),
            "email": self.current_user.get("email", ""),
            "current_password": current_password,
            "new_password": new_password
        }
        status, data = self.api_request(f"/api/users/{self.current_user['user_id']}", "PUT", payload)
        if status == 200 and data.get("success"):
            self.current_user = data.get("user", self.current_user)
            win.destroy()
            messagebox.showinfo("Password Updated", "Your password has been changed successfully.")
        else:
            messagebox.showerror("Change Password", data.get("error", "Unable to change your password."), parent=win)

    # =========================================================
    # ENTREPRENEUR FORMS
    # =========================================================
    def show_add_business(self):
        if self.current_user.get("role") != "entrepreneur":
            messagebox.showwarning("Add Business", "Only entrepreneur accounts can add a business.")
            return
        cats = self.get_api_data("/api/categories") or []
        if not cats:
            messagebox.showwarning("Add Business", "No categories are available yet. Add a category in MySQL first."); return
        win = tk.Toplevel(self); win.title("Add Business"); win.geometry("540x620"); win.configure(bg=self.colors["background"]); win.transient(self); win.grab_set()
        tk.Label(win, text="Add Business", font=("Segoe UI", 20, "bold"), fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(25, 18))
        entries = {}
        for label in ["Business name", "Description", "Contact number", "Address"]:
            tk.Label(win, text=label, font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
            e = tk.Entry(win, font=self.fonts["body"], relief="flat", bd=0, highlightbackground=self.colors["border"], highlightthickness=1); e.pack(fill="x", padx=35, pady=(5, 10), ipady=8); entries[label] = e
        tk.Label(win, text="Category", font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
        category = tk.StringVar(value=cats[0]["category_name"]); menu = tk.OptionMenu(win, category, *[c["category_name"] for c in cats]); menu.configure(font=self.fonts["body"], bg=self.colors["white"], relief="flat"); menu.pack(fill="x", padx=35, pady=(5, 18))
        tk.Button(win, text="Save Business", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, pady=10, cursor="hand2", command=lambda: self.submit_business(win, entries, category.get(), cats)).pack(fill="x", padx=35)

    def submit_business(self, win, entries, category_name, cats):
        cat = next((c for c in cats if c["category_name"] == category_name), None)
        payload = {"user_id": self.current_user["user_id"], "category_id": cat["category_id"], "business_name": entries["Business name"].get(), "description": entries["Description"].get(), "contact_number": entries["Contact number"].get(), "address": entries["Address"].get()}
        status, data = self.api_request("/api/businesses", "POST", payload)
        if status == 201:
            win.destroy(); messagebox.showinfo("Add Business", "Business added successfully."); self.show_discover()
        else: messagebox.showerror("Add Business", data.get("error", "Unable to add business."))

    def show_add_product(self):
        if self.current_user.get("role") != "entrepreneur":
            messagebox.showwarning("Add Product", "Only entrepreneur accounts can add products or services."); return
        businesses = self.get_api_data(f"/api/users/{self.current_user['user_id']}/businesses") or []
        if not businesses:
            messagebox.showwarning("Add Product", "Create a business profile first."); return
        win = tk.Toplevel(self); win.title("Add Product / Service"); win.geometry("540x520"); win.configure(bg=self.colors["background"]); win.transient(self); win.grab_set()
        tk.Label(win, text="Add Product / Service", font=("Segoe UI", 20, "bold"), fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(25, 18))
        labels = ["Product / service name", "Description", "Price"]
        entries = {}
        for label in labels:
            tk.Label(win, text=label, font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
            e = tk.Entry(win, font=self.fonts["body"], relief="flat", bd=0, highlightbackground=self.colors["border"], highlightthickness=1); e.pack(fill="x", padx=35, pady=(5, 12), ipady=8); entries[label] = e
        tk.Label(win, text="Business", font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
        business = tk.StringVar(value=businesses[0]["business_name"]); tk.OptionMenu(win, business, *[b["business_name"] for b in businesses]).pack(fill="x", padx=35, pady=(5, 12))
        tk.Label(win, text="Type", font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
        ptype = tk.StringVar(value="service"); tk.OptionMenu(win, ptype, "product", "service").pack(fill="x", padx=35, pady=(5, 18))
        tk.Button(win, text="Save Listing", font=self.fonts["button"], fg=self.colors["white"], bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0, pady=10, cursor="hand2", command=lambda: self.submit_product(win, entries, business.get(), ptype.get(), businesses)).pack(fill="x", padx=35)

    def submit_product(self, win, entries, business_name, ptype, businesses):
        business = next((b for b in businesses if b["business_name"] == business_name), None)
        price = entries["Price"].get().strip()
        payload = {"business_id": business["business_id"], "product_name": entries["Product / service name"].get(), "description": entries["Description"].get(), "price": price if price else None, "product_type": ptype}
        status, data = self.api_request("/api/products", "POST", payload)
        if status == 201:
            win.destroy(); messagebox.showinfo("Add Product", "Product/service added successfully."); self.show_products()
        else: messagebox.showerror("Add Product", data.get("error", "Unable to add listing."))

    # =========================================================
    # LOGOUT
    # =========================================================
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.current_user = None
            self.saved_businesses = set()
            self.create_login_screen()



    # =========================================================
    # ADMIN PRODUCT MANAGEMENT (LIVE MYSQL DATA)
    # =========================================================
    def show_admin_products(self):
        if not self._admin_guard():
            return
        self.clear_main()
        self.set_active_nav("Product Management")
        self.create_page_header("Product Management", "View, edit and delete every product or service on SHECONNECT.")
        self._admin_back_bar()

        status, rows = self.api_request(f"/api/admin/products?user_id={self._admin_id()}")
        if status != 200 or not isinstance(rows, list):
            messagebox.showerror("Product Management", rows.get("error", "Unable to load products.") if isinstance(rows, dict) else "Unable to load products.")
            return

        content = tk.Frame(self.main_area, bg=self.colors["background"])
        content.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        top = tk.Frame(content, bg=self.colors["background"])
        top.pack(fill="x", pady=(0, 12))
        tk.Label(top, text=f"All Products & Services ({len(rows)})", font=("Segoe UI", 14, "bold"),
                 fg=self.colors["text"], bg=self.colors["background"]).pack(side="left")
        tk.Button(top, text="↻ Refresh", command=self.show_admin_products, font=self.fonts["button"],
                  fg=self.colors["primary"], bg=self.colors["primary_light"], relief="flat", bd=0,
                  cursor="hand2", padx=14, pady=7).pack(side="right")

        if not rows:
            empty = tk.Frame(content, bg=self.colors["white"], highlightbackground=self.colors["border"], highlightthickness=1)
            empty.pack(fill="both", expand=True)
            tk.Label(empty, text="No products or services found.", font=("Segoe UI", 12),
                     fg=self.colors["muted"], bg=self.colors["white"]).pack(pady=50)
            return

        for product in rows:
            self._admin_product_card(content, product)

    def _admin_product_card(self, parent, product):
        card = tk.Frame(parent, bg=self.colors["white"], highlightbackground=self.colors["border"], highlightthickness=1)
        card.pack(fill="x", pady=6)

        icon = tk.Label(card, text="✦", font=("Segoe UI Symbol", 22, "bold"),
                        fg=self.colors["primary"], bg=self.colors["primary_light"])
        icon.pack(side="left", padx=(14, 12), pady=14, ipadx=12, ipady=8)

        info = tk.Frame(card, bg=self.colors["white"])
        info.pack(side="left", fill="x", expand=True, pady=12)

        name = product.get("product_name") or "Unnamed Listing"
        business = product.get("business_name") or "Unknown Business"
        owner = product.get("owner_name") or "Unknown Owner"
        ptype = str(product.get("product_type") or "service").capitalize()
        price = product.get("price")
        price_text = "Contact for price" if price is None else f"₹{float(price):,.2f}"

        tk.Label(info, text=name, font=("Segoe UI", 11, "bold"), fg=self.colors["text"], bg=self.colors["white"]).pack(anchor="w")
        tk.Label(info, text=f"Business: {business}  •  Owner: {owner}", font=("Segoe UI", 9),
                 fg=self.colors["muted"], bg=self.colors["white"]).pack(anchor="w", pady=(3, 0))
        tk.Label(info, text=f"Type: {ptype}  •  Price: {price_text}", font=("Segoe UI", 9, "bold"),
                 fg=self.colors["primary"], bg=self.colors["white"]).pack(anchor="w", pady=(3, 0))
        description = str(product.get("description") or "No description")
        tk.Label(info, text=description[:100], font=("Segoe UI", 8), fg=self.colors["muted"],
                 bg=self.colors["white"]).pack(anchor="w", pady=(3, 0))

        actions = tk.Frame(card, bg=self.colors["white"])
        actions.pack(side="right", padx=14, pady=12)
        self.small_action_button(actions, "View", lambda p=product: self._admin_view_product(p), filled=False).pack(pady=2)
        self.small_action_button(actions, "Edit", lambda p=product: self._admin_edit_product(p), filled=True).pack(pady=2)
        self.small_action_button(actions, "Delete", lambda p=product: self._admin_delete_product(p), danger=True).pack(pady=2)

    def _admin_view_product(self, product):
        price = product.get("price")
        price_text = "Contact for price" if price is None else f"₹{float(price):,.2f}"
        details = (
            f"Product / Service: {product.get('product_name', '')}\n\n"
            f"Business: {product.get('business_name', '')}\n"
            f"Owner: {product.get('owner_name', '')}\n"
            f"Type: {str(product.get('product_type', 'service')).capitalize()}\n"
            f"Price: {price_text}\n\n"
            f"Description:\n{product.get('description') or 'No description provided.'}"
        )
        messagebox.showinfo("Product / Service Details", details)

    def _admin_edit_product(self, product):
        win = tk.Toplevel(self)
        win.title("Edit Product / Service")
        win.geometry("560x560")
        win.configure(bg=self.colors["background"])
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Edit Product / Service", font=("Segoe UI", 20, "bold"),
                 fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(25, 5))
        tk.Label(win, text=f"Business: {product.get('business_name', 'Unknown Business')}",
                 font=("Segoe UI", 9), fg=self.colors["primary"], bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(0, 18))

        fields = {}
        for label, value in [
            ("Product / service name", product.get("product_name", "")),
            ("Description", product.get("description") or ""),
            ("Price", "" if product.get("price") is None else str(product.get("price")))
        ]:
            tk.Label(win, text=label, font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
            e = tk.Entry(win, font=self.fonts["body"], relief="flat", bd=0, bg=self.colors["white"],
                         fg=self.colors["text"], highlightbackground=self.colors["border"], highlightthickness=1)
            e.pack(fill="x", padx=35, pady=(5, 12), ipady=8)
            e.insert(0, value)
            fields[label] = e

        tk.Label(win, text="Type", font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
        ptype = tk.StringVar(value=str(product.get("product_type") or "service"))
        tk.OptionMenu(win, ptype, "product", "service").pack(fill="x", padx=35, pady=(5, 20))

        def save():
            price = fields["Price"].get().strip()
            if price:
                try:
                    float(price)
                except ValueError:
                    messagebox.showwarning("Edit Product", "Price must be a valid number.", parent=win)
                    return
            payload = {
                "user_id": self._admin_id(),
                "product_name": fields["Product / service name"].get().strip(),
                "description": fields["Description"].get().strip(),
                "price": price or None,
                "product_type": ptype.get()
            }
            if not payload["product_name"]:
                messagebox.showwarning("Edit Product", "Product/service name is required.", parent=win)
                return
            status, data = self.api_request(f"/api/admin/products/{product.get('product_id')}", "PUT", payload)
            if status == 200:
                win.destroy()
                messagebox.showinfo("Product Management", "Product/service updated successfully.")
                self.show_admin_products()
            else:
                messagebox.showerror("Product Management", data.get("error", "Unable to update product."), parent=win)

        tk.Button(win, text="Save Changes", command=save, font=self.fonts["button"], fg=self.colors["white"],
                  bg=self.colors["primary"], activebackground=self.colors["primary_dark"], relief="flat", bd=0,
                  cursor="hand2", pady=10).pack(fill="x", padx=35, pady=(0, 8))
        tk.Button(win, text="Cancel", command=win.destroy, font=self.fonts["button"], fg=self.colors["primary"],
                  bg=self.colors["primary_light"], relief="flat", bd=0, cursor="hand2", pady=9).pack(fill="x", padx=35)

    def _admin_delete_product(self, product):
        name = product.get("product_name") or "this product/service"
        if not messagebox.askyesno("Delete Product / Service", f"Delete '{name}'?\n\nThis cannot be undone."):
            return
        status, data = self.api_request(
            f"/api/admin/products/{product.get('product_id')}",
            "DELETE",
            {"user_id": self._admin_id()}
        )
        if status == 200:
            messagebox.showinfo("Product Management", "Product/service deleted successfully.")
            self.show_admin_products()
        else:
            messagebox.showerror("Product Management", data.get("error", "Unable to delete product."))

    # =========================================================
    # ADMIN USER EDIT / DELETE
    # =========================================================
    def _admin_edit_user(self, user):
        win = tk.Toplevel(self)
        win.title("Edit User")
        win.geometry("520x470")
        win.configure(bg=self.colors["background"])
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Edit User", font=("Segoe UI", 20, "bold"), fg=self.colors["text"],
                 bg=self.colors["background"]).pack(anchor="w", padx=35, pady=(25, 18))
        fields = {}
        for label, value in [("Name", user.get("name", "")), ("Email", user.get("email", ""))]:
            tk.Label(win, text=label, font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
            e = tk.Entry(win, font=self.fonts["body"], relief="flat", bd=0, bg=self.colors["white"],
                         fg=self.colors["text"], highlightbackground=self.colors["border"], highlightthickness=1)
            e.pack(fill="x", padx=35, pady=(5, 14), ipady=8)
            e.insert(0, value)
            fields[label] = e

        tk.Label(win, text="Role", font=self.fonts["body_bold"], fg=self.colors["text"], bg=self.colors["background"]).pack(anchor="w", padx=35)
        role = tk.StringVar(value=user.get("role", "customer"))
        tk.OptionMenu(win, role, "customer", "entrepreneur", "admin").pack(fill="x", padx=35, pady=(5, 20))

        def save():
            name = fields["Name"].get().strip()
            email = fields["Email"].get().strip().lower()
            if not name or "@" not in email:
                messagebox.showwarning("Edit User", "Enter a valid name and email.", parent=win)
                return
            payload = {"user_id": self._admin_id(), "name": name, "email": email, "role": role.get()}
            status, data = self.api_request(f"/api/admin/users/{user.get('user_id')}", "PUT", payload)
            if status == 200:
                win.destroy()
                messagebox.showinfo("User Management", "User updated successfully.")
                self.show_admin_users()
            else:
                messagebox.showerror("User Management", data.get("error", "Unable to update user."), parent=win)

        tk.Button(win, text="Save Changes", command=save, font=self.fonts["button"], fg=self.colors["white"],
                  bg=self.colors["primary"], relief="flat", bd=0, cursor="hand2", pady=10).pack(fill="x", padx=35, pady=(0, 8))
        tk.Button(win, text="Cancel", command=win.destroy, font=self.fonts["button"], fg=self.colors["primary"],
                  bg=self.colors["primary_light"], relief="flat", bd=0, cursor="hand2", pady=9).pack(fill="x", padx=35)

    # =========================================================
    # ADMIN MANAGEMENT
    # =========================================================
    def _admin_id(self):
        return self.admin_user.user_id if getattr(self, "admin_user", None) and self.admin_user.is_admin() else (self.current_user.get("user_id") if self.current_user else None)

    def _admin_guard(self):
        if not self.current_user or self.current_user.get("role") != "admin":
            messagebox.showerror("Access denied", "This section is available only to administrators.")
            return False
        return True

    def _admin_back_bar(self):
        """Always-visible return control for Admin management screens."""
        bar=tk.Frame(self.main_area,bg=self.colors["background"])
        bar.pack(fill="x",padx=40,pady=(0,10))
        tk.Button(bar,text="←  Back to Admin Dashboard",command=self.show_admin_dashboard,
                  font=("Segoe UI",9,"bold"),fg=self.colors["primary"],bg=self.colors["primary_light"],
                  activeforeground=self.colors["white"],activebackground=self.colors["primary"],
                  relief="flat",bd=0,cursor="hand2",padx=14,pady=8).pack(side="left")

    def show_admin_dashboard(self):
        if not self._admin_guard(): return
        self.clear_main(); self.set_active_nav("Admin Dashboard")
        self.create_page_header("Admin Dashboard", "Manage users, businesses, categories and reports.")
        content=tk.Frame(self.main_area,bg=self.colors["background"]); content.pack(fill="both",expand=True,padx=40,pady=(5,30))
        status,data=self.api_request(f"/api/admin/stats?user_id={self._admin_id()}")
        if status!=200:
            messagebox.showerror("Admin Dashboard",data.get("error","Unable to load statistics.")); return
        row=tk.Frame(content,bg=self.colors["background"]); row.pack(fill="x",pady=(0,18))
        cards=[("Total Users",data.get("total_users",0)),("Entrepreneurs",data.get("entrepreneurs",0)),("Customers",data.get("customers",0)),("Businesses",data.get("businesses",0))]
        for title,num in cards: self.create_stat_card(row,title,str(num),"Platform records")
        row2=tk.Frame(content,bg=self.colors["background"]); row2.pack(fill="x",pady=(0,24))
        cards2=[("Products / Services",data.get("products_services",0)),("Total Enquiries",data.get("enquiries",0)),("Pending Enquiries",data.get("pending_enquiries",0))]
        for title,num in cards2: self.create_stat_card(row2,title,str(num),"Platform activity")
        actions=tk.Frame(content,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); actions.pack(fill="x")
        tk.Label(actions,text="Administration",font=("Segoe UI",14,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=22,pady=(18,12))
        buttons=[("User Management",self.show_admin_users),("Business Management",self.show_admin_businesses),("Category Management",self.show_admin_categories),("Reports",self.show_admin_reports)]
        line=tk.Frame(actions,bg=self.colors["white"]); line.pack(fill="x",padx=22,pady=(0,20))
        for text,cmd in buttons:
            tk.Button(line,text=text,command=cmd,font=self.fonts["button"],fg=self.colors["white"],bg=self.colors["primary"],activebackground=self.colors["primary_dark"],relief="flat",bd=0,padx=18,pady=10,cursor="hand2").pack(side="left",padx=(0,10))

    def show_admin_users(self):
        if not self._admin_guard():
            return

        self.clear_main()
        self.set_active_nav("User Management")
        self.create_page_header(
            "User Management",
            "Manage users, businesses, categories and reports."
        )
        self._admin_back_bar()

        status, data = self.api_request(
            f"/api/admin/users?user_id={self._admin_id()}"
        )

        if status != 200 or not isinstance(data, list):
            messagebox.showerror(
                "User Management",
                data.get("error", "Unable to load users.")
                if isinstance(data, dict) else "Unable to load users."
            )
            return

        # Show users in ascending ID order: 1, 2, 3, ...
        data.sort(key=lambda user: int(user.get("user_id", 0) or 0))

        content = tk.Frame(
            self.main_area,
            bg=self.colors["background"]
        )
        content.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=(0, 30)
        )

        # Small summary row
        summary = tk.Frame(
            content,
            bg=self.colors["background"]
        )
        summary.pack(fill="x", pady=(0, 16))

        total = len(data)
        entrepreneurs = sum(1 for u in data if u.get("role") == "entrepreneur")
        customers = sum(1 for u in data if u.get("role") == "customer")
        admins = sum(1 for u in data if u.get("role") == "admin")

        summary_items = [
            ("Total Users", total),
            ("Entrepreneurs", entrepreneurs),
            ("Customers", customers),
            ("Administrators", admins)
        ]

        for title, number in summary_items:
            card = tk.Frame(
                summary,
                bg=self.colors["white"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                height=76
            )
            card.pack(side="left", fill="x", expand=True, padx=(0, 10))
            card.pack_propagate(False)

            tk.Label(
                card,
                text=title,
                font=("Segoe UI", 9),
                fg=self.colors["muted"],
                bg=self.colors["white"]
            ).pack(anchor="w", padx=15, pady=(11, 0))

            tk.Label(
                card,
                text=str(number),
                font=("Segoe UI", 17, "bold"),
                fg=self.colors["primary"],
                bg=self.colors["white"]
            ).pack(anchor="w", padx=15)

        # Main table — fixed, clean and aligned. No scrollbar.
        table_box = tk.Frame(
            content,
            bg=self.colors["white"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        table_box.pack(fill="x")

        top = tk.Frame(table_box, bg=self.colors["white"])
        top.pack(fill="x", padx=20, pady=(16, 12))

        tk.Label(
            top,
            text=f"All Users ({len(data)})",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text"],
            bg=self.colors["white"]
        ).pack(side="left")

        tk.Button(
            top,
            text="↻ Refresh",
            command=self.show_admin_users,
            font=self.fonts["button"],
            fg=self.colors["primary"],
            bg=self.colors["primary_light"],
            activeforeground=self.colors["white"],
            activebackground=self.colors["primary"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=7
        ).pack(side="right")

        table = tk.Frame(table_box, bg=self.colors["white"])
        table.pack(fill="x", padx=20, pady=(0, 20))

        columns = [
            ("ID", 0.07),
            ("Name", 0.20),
            ("Email", 0.30),
            ("Role", 0.15),
            ("Created", 0.18),
            ("Actions", 0.10)
        ]

        for col, (heading, weight) in enumerate(columns):
            table.grid_columnconfigure(col, weight=1)

            tk.Label(
                table,
                text=heading,
                font=("Segoe UI", 9, "bold"),
                fg=self.colors["dark_pink"],
                bg=self.colors["primary_light"],
                anchor="w",
                padx=10,
                pady=10
            ).grid(
                row=0,
                column=col,
                sticky="ew",
                padx=(0 if col == 0 else 1, 0)
            )

        if not data:
            tk.Label(
                table,
                text="No users found.",
                font=("Segoe UI", 10),
                fg=self.colors["muted"],
                bg=self.colors["white"],
                pady=25
            ).grid(row=1, column=0, columnspan=6, sticky="ew")
            return

        for row_index, user in enumerate(data, start=1):
            row_bg = self.colors["white"] if row_index % 2 else "#FFF9FC"

            user_id = user.get("user_id", "")
            name = user.get("name", "") or "—"
            email = user.get("email", "") or "—"
            role = str(user.get("role", "")).capitalize()
            created = str(user.get("created_at", "") or "—")

            values = [user_id, name, email, role, created]

            for col, value in enumerate(values):
                tk.Label(
                    table,
                    text=str(value),
                    font=("Segoe UI", 9),
                    fg=self.colors["text"],
                    bg=row_bg,
                    anchor="w",
                    padx=10,
                    pady=11
                ).grid(
                    row=row_index,
                    column=col,
                    sticky="ew",
                    padx=(0 if col == 0 else 1, 0)
                )

            action_frame = tk.Frame(table, bg=row_bg)
            action_frame.grid(
                row=row_index,
                column=5,
                sticky="ew",
                padx=5,
                pady=5
            )

            self.small_action_button(
                action_frame,
                "Edit",
                lambda u=user: self._admin_edit_user(u),
                filled=True
            ).pack(side="left", padx=(0, 4))

            if user_id != self._admin_id():
                self.small_action_button(
                    action_frame,
                    "Delete",
                    lambda uid=user_id, n=name: self._admin_delete_user(uid, n),
                    danger=True
                ).pack(side="left")

    def _admin_delete_user(self,user_id,name):
        if not messagebox.askyesno("Delete User",f"Delete user '{name}'?\nTheir related data may also be removed."): return
        status,data=self.api_request(f"/api/admin/users/{user_id}?user_id={self._admin_id()}","DELETE")
        if status==200: messagebox.showinfo("User Management","User deleted successfully."); self.show_admin_users()
        else: messagebox.showerror("User Management",data.get("error","Unable to delete user."))

    def show_admin_businesses(self):
        if not self._admin_guard(): return
        self.clear_main(); self.set_active_nav("Business Management")
        self.create_page_header("Business Management", "Review and manage business listings on SHECONNECT.")
        self._admin_back_bar()
        status,rows=self.api_request(f"/api/admin/businesses?user_id={self._admin_id()}")
        if status!=200: messagebox.showerror("Business Management",rows.get("error","Unable to load businesses.")); return
        box=tk.Frame(self.main_area,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); box.pack(fill="both",expand=True,padx=40,pady=(0,30))
        tk.Label(box,text=f"Business Listings ({len(rows)})",font=("Segoe UI",14,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=22,pady=(18,12))
        for b in rows:
            card=tk.Frame(box,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); card.pack(fill="x",padx=22,pady=6)
            info=tk.Frame(card,bg=self.colors["white"]); info.pack(side="left",fill="x",expand=True,padx=14,pady=12)
            tk.Label(info,text=b.get("business_name",""),font=("Segoe UI",11,"bold"),fg=self.colors["dark_pink"],bg=self.colors["white"]).pack(anchor="w")
            tk.Label(info,text=f"Owner: {b.get('owner_name','')}   |   Category: {b.get('category_name','')}",font=("Segoe UI",9),fg=self.colors["muted"],bg=self.colors["white"]).pack(anchor="w",pady=(3,0))
            tk.Label(info,text=b.get("address","") or "No address",font=("Segoe UI",9),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",pady=(3,0))
            actions = tk.Frame(card, bg=self.colors["white"])
            actions.pack(side="right", padx=14, pady=12)

            self.small_action_button(
                actions, "View",
                lambda item=b: self._admin_view_business(item),
                filled=False
            ).pack(side="left", padx=3)

            self.small_action_button(
                actions, "Edit",
                lambda item=b: self._admin_edit_business(item),
                filled=True
            ).pack(side="left", padx=3)

            self.small_action_button(
                actions, "Delete",
                lambda bid=b.get("business_id"), name=b.get("business_name",""):
                    self._admin_delete_business(bid, name),
                danger=True
            ).pack(side="left", padx=3)
        if not rows: tk.Label(box,text="No business listings found.",font=("Segoe UI",10),fg=self.colors["muted"],bg=self.colors["white"]).pack(pady=30)

    def _admin_delete_business(self,business_id,name):
        if not messagebox.askyesno("Delete Business",f"Delete business listing '{name}'?\nIts related products and enquiries may also be removed."): return
        status,data=self.api_request(f"/api/admin/businesses/{business_id}","DELETE",{"user_id":self._admin_id()})
        if status==200: messagebox.showinfo("Business Management","Business deleted successfully."); self.show_admin_businesses()
        else: messagebox.showerror("Business Management",data.get("error","Unable to delete business."))

    def show_admin_categories(self):
        if not self._admin_guard(): return
        self.clear_main(); self.set_active_nav("Category Management"); self.create_page_header("Category Management", "Add and remove categories used for business listings.")
        self._admin_back_bar()
        status,cats=self.api_request("/api/categories")
        content=tk.Frame(self.main_area,bg=self.colors["background"]); content.pack(fill="both",expand=True,padx=40,pady=(0,30))
        form=tk.Frame(content,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); form.pack(fill="x",pady=(0,16))
        tk.Label(form,text="Add New Category",font=("Segoe UI",13,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=22,pady=(16,8))
        row=tk.Frame(form,bg=self.colors["white"]); row.pack(fill="x",padx=22,pady=(0,18))
        name=tk.Entry(row,font=("Segoe UI",10),relief="solid",bd=1); name.pack(side="left",fill="x",expand=True,padx=(0,10),ipady=8)
        desc=tk.Entry(row,font=("Segoe UI",10),relief="solid",bd=1); desc.pack(side="left",fill="x",expand=True,padx=(0,10),ipady=8)
        def add():
            n=name.get().strip(); d=desc.get().strip()
            if not n: messagebox.showwarning("Category","Enter a category name."); return
            st,data=self.api_request("/api/admin/categories","POST",{"user_id":self._admin_id(),"category_name":n,"description":d})
            if st==201: messagebox.showinfo("Category Management","Category added successfully."); self.show_admin_categories()
            else: messagebox.showerror("Category Management",data.get("error","Unable to add category."))
        tk.Button(row,text="Add Category",command=add,font=self.fonts["button"],fg=self.colors["white"],bg=self.colors["primary"],activebackground=self.colors["primary_dark"],relief="flat",bd=0,padx=18,pady=10,cursor="hand2").pack(side="right")
        listbox=tk.Frame(content,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); listbox.pack(fill="both",expand=True)
        tk.Label(listbox,text=f"Existing Categories ({len(cats) if isinstance(cats,list) else 0})",font=("Segoe UI",13,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=22,pady=(16,10))
        for cat in (cats if isinstance(cats,list) else []):
            r=tk.Frame(listbox,bg=self.colors["white"]); r.pack(fill="x",padx=22,pady=5)
            text=tk.Frame(r,bg=self.colors["white"]); text.pack(side="left",fill="x",expand=True)
            tk.Label(text,text=cat.get("category_name",""),font=("Segoe UI",10,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w")
            tk.Label(text,text=cat.get("description","") or "No description",font=("Segoe UI",8),fg=self.colors["muted"],bg=self.colors["white"]).pack(anchor="w")
            actions = tk.Frame(r, bg=self.colors["white"])
            actions.pack(side="right", padx=(10, 0))

            self.small_action_button(
                actions, "Edit",
                lambda item=cat: self._admin_edit_category(item),
                filled=True
            ).pack(side="left", padx=3)

            self.small_action_button(
                actions, "Delete",
                lambda cid=cat.get("category_id"), name=cat.get("category_name",""):
                    self._admin_delete_category(cid, name),
                danger=True
            ).pack(side="left", padx=3)

    def _admin_delete_category(self,category_id,name):
        if not messagebox.askyesno("Delete Category",f"Delete category '{name}'?"): return
        status,data=self.api_request("/api/admin/categories","DELETE",{"user_id":self._admin_id(),"category_id":category_id})
        if status==200: messagebox.showinfo("Category Management","Category deleted successfully."); self.show_admin_categories()
        else: messagebox.showerror("Category Management",data.get("error","Unable to delete category."))

    def show_admin_enquiries(self):
        if not self._admin_guard(): return
        self.clear_main(); self.set_active_nav("Enquiries"); self.create_page_header("Enquiry Monitoring", "Monitor customer enquiries across the platform.")
        status,rows=self.api_request(f"/api/admin/enquiries?user_id={self._admin_id()}")
        if status!=200: messagebox.showerror("Enquiries",rows.get("error","Unable to load enquiries.")); return
        box=tk.Frame(self.main_area,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); box.pack(fill="both",expand=True,padx=40,pady=(0,30))
        tk.Label(box,text=f"All Enquiries ({len(rows)})",font=("Segoe UI",14,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=22,pady=(18,12))
        for e in rows:
            card=tk.Frame(box,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); card.pack(fill="x",padx=22,pady=5)
            tk.Label(card,text=e.get("subject","") or "Untitled enquiry",font=("Segoe UI",10,"bold"),fg=self.colors["dark_pink"],bg=self.colors["white"]).pack(anchor="w",padx=14,pady=(10,2))
            tk.Label(card,text=f"Customer: {e.get('customer_name','')}  |  Business: {e.get('business_name','')}  |  Status: {e.get('status','')}",font=("Segoe UI",9),fg=self.colors["muted"],bg=self.colors["white"]).pack(anchor="w",padx=14,pady=(0,10))
        if not rows: tk.Label(box,text="No enquiries found.",font=("Segoe UI",10),fg=self.colors["muted"],bg=self.colors["white"]).pack(pady=30)

    def show_admin_reports(self):
        if not self._admin_guard(): return
        self.clear_main(); self.set_active_nav("Reports"); self.create_page_header("Reports", "Administrative reports for users, businesses, products and enquiries.")
        self._admin_back_bar()
        status,data=self.api_request(f"/api/admin/reports?user_id={self._admin_id()}")
        if status!=200: messagebox.showerror("Reports",data.get("error","Unable to load reports.")); return
        content=tk.Frame(self.main_area,bg=self.colors["background"]); content.pack(fill="both",expand=True,padx=40,pady=(0,30))
        self._report_section(content,"Users by Role",data.get("users_by_role",[]),"role")
        self._report_section(content,"Enquiries by Status",data.get("enquiries_by_status",[]),"status")
        self._report_section(content,"Businesses by Category",data.get("businesses_by_category",[]),"category_name")
        summary=tk.Frame(content,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); summary.pack(fill="x",pady=6)
        tk.Label(summary,text="Products / Services",font=("Segoe UI",10,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(side="left",padx=18,pady=14)
        tk.Label(summary,text=str(data.get("products_services",0)),font=("Segoe UI",14,"bold"),fg=self.colors["dark_pink"],bg=self.colors["white"]).pack(side="right",padx=18,pady=10)

    def _report_section(self,parent,title,rows,label_key):
        box=tk.Frame(parent,bg=self.colors["white"],highlightbackground=self.colors["border"],highlightthickness=1); box.pack(fill="x",pady=6)
        tk.Label(box,text=title,font=("Segoe UI",11,"bold"),fg=self.colors["text"],bg=self.colors["white"]).pack(anchor="w",padx=18,pady=(12,7))
        for row in rows:
            tk.Label(box,text=f"{row.get(label_key,'Unknown')}: {row.get('total',0)}",font=("Segoe UI",9),fg=self.colors["muted"],bg=self.colors["white"]).pack(anchor="w",padx=18,pady=3)
        tk.Frame(box,height=8,bg=self.colors["white"]).pack()


if __name__ == "__main__":
    app = SheConnectApp()
    app.mainloop()