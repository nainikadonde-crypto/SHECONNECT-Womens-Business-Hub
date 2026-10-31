import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

from nicegui import Client, app, ui

API_BASE = 'http://127.0.0.1:5000'

PINK = '#C4457F'
DARK_PINK = '#A93668'
DEEP_PINK = '#8F2855'
LIGHT_PINK = '#F8E5EE'
SOFT_PINK = '#FCEEF4'
BG = '#FFF8FB'
TEXT = '#29242A'
MUTED = '#777078'
BORDER = '#EADDE4'
SUCCESS = '#4D9872'
WARNING = '#D59A45'
DANGER = '#C84A5A'


# =====================================================================
# SESSION (per browser, so two people can be logged in at once)
# =====================================================================

def store():
    return app.storage.user


def logged_in():
    return bool(store().get('user'))


def current_user():
    return store().get('user') or {}


def user_id():
    return current_user().get('user_id')


def current_role():
    return str(current_user().get('role', '')).lower()


def is_admin():
    return current_role() == 'admin'


def current_page():
    return store().get('page', 'Dashboard')


def set_page(name):
    store()['page'] = name


def saved_ids():
    data = app.storage.general.get('saved', {})
    return set(data.get(str(user_id()), []))


def set_saved(ids):
    data = dict(app.storage.general.get('saved', {}))
    data[str(user_id())] = sorted(ids)
    app.storage.general['saved'] = data


# =====================================================================
# API HELPERS
# =====================================================================

def api_request(endpoint, method='GET', payload=None):
    """Send a request to the Flask backend. Returns (status, data)."""
    method = str(method).upper()
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = Request(
        API_BASE + endpoint,
        data=body,
        headers={'Content-Type': 'application/json'},
        method=method,
    )
    try:
        with urlopen(req, timeout=8) as response:
            raw = response.read().decode('utf-8')
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {'message': raw}
            return response.status, data
    except HTTPError as error:
        raw = error.read().decode('utf-8')
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {'error': f'Server returned HTTP {error.code}.'}
        return error.code, data
    except (URLError, TimeoutError, OSError):
        return 0, {'error': 'Cannot connect to Flask API. Start app.py on port 5000.'}


def get_error_message(data, fallback='Unable to complete the request.'):
    if isinstance(data, dict):
        return str(data.get('error') or data.get('message') or fallback)
    return fallback


def notify_error(data, fallback='Unable to complete the request.'):
    ui.notify(get_error_message(data, fallback), type='negative', position='top')


def notify_success(message):
    ui.notify(message, type='positive', position='top')


def notify_warning(message):
    ui.notify(message, type='warning', position='top')


def get_data(endpoint):
    status, data = api_request(endpoint)
    if status == 200:
        return data
    if status == 0:
        notify_error(data)
    return []


def api_action(endpoint, method, payload=None, success_message=None):
    status, data = api_request(endpoint, method, payload)
    if 200 <= status < 300 and (not isinstance(data, dict) or data.get('success', True)):
        if success_message:
            notify_success(success_message)
        return True
    notify_error(data)
    return False


def money(value):
    if value in (None, ''):
        return 'Contact for price'
    try:
        return f'₹{float(value):,.2f}'
    except (TypeError, ValueError):
        return f'₹{value}'


def user_query():
    return f'?user_id={quote(str(user_id()))}'


def load_categories():
    data = get_data('/api/categories')
    return data if isinstance(data, list) else []


def get_businesses(search=''):
    endpoint = f'/api/businesses/search?q={quote(search)}' if search else '/api/businesses'
    data = get_data(endpoint)
    return data if isinstance(data, list) else []


def get_products(search=''):
    endpoint = f'/api/products/search?q={quote(search)}' if search else '/api/products'
    data = get_data(endpoint)
    return data if isinstance(data, list) else []


# =====================================================================
# THEME (all pink)
# =====================================================================

ui.add_head_html('''
<style>
:root {
    --q-primary: #C4457F;
    --q-secondary: #A93668;
    --q-accent: #D85C91;
    --q-positive: #4D9872;
    --q-negative: #C84A5A;
    --q-info: #C4457F;
    --q-warning: #D59A45;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    background: #FFF8FB;
    color: #29242A;
    font-family: 'Segoe UI', Arial, sans-serif;
}
.nicegui-content { padding: 0 !important; gap: 0 !important; }
.nicegui-row.no-wrap { flex-wrap: nowrap !important; }
.q-separator { background: #EADDE4 !important; }

/* ---------- layout ---------- */
.sc-sidebar {
    background: #FFFFFF;
    border-right: 1px solid #EADDE4;
    width: 278px; min-width: 278px; height: 100vh;
    position: fixed; left: 0; top: 0;
    padding: 22px 16px; overflow-y: auto; z-index: 20;
    align-items: stretch !important;
}
.sc-main {
    margin-left: 278px;
    padding: 30px 38px;
    min-height: 100vh;
    width: calc(100% - 278px);
    align-items: stretch !important;
}
.sc-brand-icon {
    width: 46px; height: 46px; min-width: 46px;
    background: #C4457F; color: #fff;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 27px; font-weight: bold;
}
.sc-icon-soft {
    background: #F8E5EE; color: #C4457F;
    width: 58px; height: 58px; min-width: 58px; border-radius: 14px;
}
.sc-brand { color: #8F2855; font-size: 21px; font-weight: 800; letter-spacing: 1px; }
.sc-userbox {
    background: #FCEEF4; border: 1px solid #EADDE4;
    border-radius: 13px; padding: 10px 12px;
}
.sc-avatar {
    background: #C4457F; color: #fff;
    border-radius: 50%; width: 42px; height: 42px; min-width: 42px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800;
}
.sc-pill {
    background: #F8E5EE; color: #A93668;
    border-radius: 20px; padding: 3px 11px;
    font-size: 12px; font-weight: 700;
}

/* ---------- cards ---------- */
.sc-card {
    background: #fff !important;
    border: 1px solid #EADDE4 !important;
    border-radius: 16px !important;
    padding: 20px 22px !important;
    box-shadow: 0 5px 18px rgba(143, 40, 85, .04) !important;
}
.sc-hero {
    background: linear-gradient(120deg, #C4457F, #8F2855);
    color: #fff; border-radius: 20px; padding: 28px 30px; width: 100%;
}
.sc-heading { font-size: 26px; line-height: 1.3; font-weight: 750; color: #29242A; }
.sc-muted { color: #777078; }
.sc-stat {
    background: #fff; border: 1px solid #EADDE4; border-radius: 16px;
    padding: 18px 20px; min-height: 110px; flex: 1; min-width: 190px;
}
.sc-stat-number { font-size: 27px; font-weight: 800; color: #C4457F; }
.sc-searchbar {
    background: #fff; border: 1px solid #EADDE4; border-radius: 12px;
    padding: 6px 8px 6px 16px;
}
.sc-chips { overflow-x: auto; padding-bottom: 6px; }

/* ---------- buttons (pink only) ---------- */
.q-btn.sc-primary {
    background: #C4457F !important; color: #fff !important;
    border-radius: 9px !important; font-weight: 650 !important; padding: 8px 18px;
}
.q-btn.sc-primary:hover { background: #A93668 !important; }
.q-btn.sc-outline {
    background: #F8E5EE !important; color: #A93668 !important;
    border-radius: 9px !important; font-weight: 650 !important; padding: 8px 16px;
}
.q-btn.sc-outline:hover { background: #C4457F !important; color: #fff !important; }
.q-btn.sc-danger {
    background: #F8E5EE !important; color: #C84A5A !important;
    border-radius: 9px !important; font-weight: 650 !important; padding: 8px 16px;
}
.q-btn.sc-danger:hover { background: #C84A5A !important; color: #fff !important; }
.q-btn.sc-danger-solid {
    background: #C84A5A !important; color: #fff !important;
    border-radius: 9px !important; font-weight: 650 !important; padding: 8px 18px;
}
.q-btn.sc-small { padding: 4px 12px !important; font-size: 12px; min-height: 30px; }
.q-btn.sc-nav {
    width: 100%; border-radius: 10px; padding: 9px 13px;
    font-size: 13px; color: #777078 !important; background: transparent !important;
}
.q-btn.sc-nav .q-btn__content { justify-content: flex-start; }
.q-btn.sc-nav:hover { background: #FCEEF4 !important; color: #A93668 !important; }
.q-btn.sc-nav-active {
    background: #F8E5EE !important; color: #A93668 !important; font-weight: 700;
}
.q-btn.sc-chip {
    background: #F8E5EE !important; color: #C4457F !important;
    border-radius: 20px !important; font-weight: 700 !important;
    padding: 4px 16px; white-space: nowrap;
}
.q-btn.sc-chip:hover { background: #F2CFE0 !important; }
.q-btn.sc-chip-active { background: #C4457F !important; color: #fff !important; }

/* ---------- login / register ---------- */
.sc-auth-wrap { background: #FFF8FB; }
.sc-auth-left {
    position: relative; overflow: hidden;
    background: #C4457F; color: #fff;
    width: 510px; min-width: 510px; min-height: 100vh;
    padding: 60px 52px; justify-content: center; align-items: flex-start !important;
}
.sc-auth-left::before {
    content: ''; position: absolute; width: 300px; height: 300px;
    border-radius: 50%; background: #A93668; top: -130px; left: -130px;
}
.sc-auth-left::after {
    content: ''; position: absolute; width: 250px; height: 250px;
    border-radius: 50%; background: #8F2855; bottom: -110px; right: -60px;
}
.sc-auth-left > * { position: relative; z-index: 2; }
.sc-auth-right { flex: 1; min-height: 100vh; padding: 24px; }
.sc-auth-card {
    width: 100%; max-width: 560px; background: #fff;
    border: 1px solid #EADDE4; border-radius: 22px; padding: 40px 46px;
    box-shadow: 0 15px 45px rgba(143, 40, 85, .09);
}
.sc-benefit-no {
    background: #8F2855; color: #fff; font-weight: 700; font-size: 12px;
    padding: 5px 10px; min-width: 38px; text-align: center;
}

/* ---------- admin tables ---------- */
.sc-table-scroll { overflow-x: auto; width: 100%; }
.sc-grid { display: grid; align-items: center; min-width: 880px; width: 100%; }
.sc-grid-head { background: #F8E5EE; color: #8F2855; font-weight: 700; font-size: 13px; }
.sc-cell { padding: 11px 10px; font-size: 13px; word-break: break-word; }
.sc-grid-row:nth-child(even) { background: #FFF9FC; }

.sc-dialog { border-radius: 18px !important; }
.q-field--focused .q-field__label { color: #C4457F !important; }

@media (max-width: 900px) {
    .sc-sidebar { position: relative; width: 100%; height: auto; min-width: 0; }
    .sc-main { margin-left: 0; width: 100%; padding: 20px; }
    .sc-auth-left { display: none; }
}
</style>
''', shared=True)


def setup_page():
    ui.colors(
        primary=PINK, secondary=DARK_PINK, accent='#D85C91',
        positive=SUCCESS, negative=DANGER, info=PINK, warning=WARNING,
    )


# =====================================================================
# SMALL UI COMPONENTS
# =====================================================================

VIEWS = {}


def refresh_view():
    """Re-render the logged-in layout for the current browser tab only."""
    render = VIEWS.get(ui.context.client.id)
    if render:
        render()


def page_heading(title, subtitle=''):
    with ui.column().classes('w-full gap-1'):
        ui.label(title).classes('sc-heading')
        if subtitle:
            ui.label(subtitle).classes('text-sm sc-muted')


def card_title(title, subtitle=None):
    ui.label(title).classes('text-lg font-bold')
    if subtitle:
        ui.label(subtitle).classes('text-sm sc-muted')


def primary_button(label, callback, icon=None):
    return ui.button(label, on_click=callback, icon=icon).props('unelevated no-caps').classes('sc-primary')


def secondary_button(label, callback, icon=None):
    return ui.button(label, on_click=callback, icon=icon).props('unelevated no-caps').classes('sc-outline')


def danger_button(label, callback, icon=None):
    return ui.button(label, on_click=callback, icon=icon).props('unelevated no-caps').classes('sc-danger')


def solid_danger_button(label, callback, icon=None):
    return ui.button(label, on_click=callback, icon=icon).props('unelevated no-caps').classes('sc-danger-solid')


def small_button(label, callback, icon=None, kind='outline'):
    cls = {'outline': 'sc-outline', 'primary': 'sc-primary', 'danger': 'sc-danger'}[kind]
    return ui.button(label, on_click=callback, icon=icon).props('unelevated no-caps dense').classes(f'{cls} sc-small')


def stat_card(label, value, icon, description=''):
    with ui.column().classes('sc-stat gap-1'):
        with ui.row().classes('items-center justify-between w-full no-wrap'):
            ui.label(str(label).upper()).classes('text-xs font-bold tracking-wide sc-muted')
            ui.icon(icon).classes('text-xl').style(f'color:{PINK}')
        ui.label(str(value)).classes('sc-stat-number')
        if description:
            ui.label(description).classes('text-xs sc-muted')


def empty_state(message, icon='inbox'):
    with ui.column().classes('w-full items-center justify-center py-10 gap-2'):
        ui.icon(icon).classes('text-5xl').style(f'color:{PINK}')
        ui.label(message).classes('sc-muted')


def info_line(icon, text):
    with ui.row().classes('items-center gap-2 no-wrap'):
        ui.icon(icon).classes('text-base').style(f'color:{PINK}')
        ui.label(text).classes('text-sm sc-muted')


def status_pill(status):
    status = str(status or 'pending').lower()
    color = {'pending': WARNING, 'replied': SUCCESS, 'closed': MUTED}.get(status, MUTED)
    ui.label(status.title()).classes('text-xs font-bold').style(
        f'background:{color}22;color:{color};padding:3px 12px;border-radius:20px;'
    )


def search_bar(placeholder, on_search):
    with ui.row().classes('sc-searchbar w-full items-center no-wrap gap-2'):
        ui.icon('search').classes('text-2xl').style(f'color:{PINK}')
        field = ui.input(placeholder=placeholder).props('borderless dense').classes('flex-1')
        primary_button('Search', on_search)
    field.on('keydown.enter', on_search)
    return field


def make_dialog(width=620):
    dialog = ui.dialog()
    with dialog:
        card = ui.card().classes('sc-dialog gap-3').style(
            f'width:{width}px;max-width:94vw !important;padding:28px;'
        )
    return dialog, card


def confirm_dialog(title, message, confirm_label, action, after, note=None):
    dialog, card = make_dialog(440)
    with card:
        ui.label(title).classes('text-xl font-bold')
        ui.label(message)
        if note:
            ui.label(note).classes('text-sm sc-muted')

        def go():
            if action():
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            secondary_button('Cancel', dialog.close)
            solid_danger_button(confirm_label, go, 'delete')
    dialog.open()


def back_bar():
    secondary_button('Back to Admin Dashboard', lambda: navigate_page('Dashboard'), 'arrow_back')


# =====================================================================
# LOGIN / REGISTER
# =====================================================================

def render_auth(register=False):
    if register:
        left_title = 'Create your place\nin the community.'
        left_text = ('Build your profile, discover opportunities and connect with a '
                     'growing women-focused business network.')
    else:
        left_title = 'A stronger place to\nbuild your business.'
        left_text = ('SHECONNECT brings women entrepreneurs and customers together in '
                     'one professional business community.')

    with ui.row().classes('sc-auth-wrap w-full min-h-screen no-wrap gap-0'):
        # ---------------- left brand panel ----------------
        with ui.column().classes('sc-auth-left gap-0'):
            with ui.row().classes('items-center gap-3 no-wrap mb-8'):
                ui.label('♀').classes('text-6xl font-bold')
                with ui.column().classes('gap-0'):
                    ui.label('SHECONNECT').classes('text-3xl font-extrabold')
                    ui.label("WOMEN'S BUSINESS HUB").classes('text-xs font-bold tracking-widest').style('opacity:.9')
            ui.separator().style('background:#ECA6C4 !important;width:100%;height:2px;')
            ui.label(left_title).classes('text-4xl font-bold leading-tight mt-6').style('white-space:pre-line;')
            ui.label(left_text).classes('text-base leading-7 mt-3').style('max-width:400px;opacity:.93;')
            with ui.column().classes('gap-3 mt-6'):
                for number, text in [
                    ('01', 'Discover women-led businesses'),
                    ('02', 'Connect with customers and entrepreneurs'),
                    ('03', 'Grow your business community'),
                ]:
                    with ui.row().classes('items-center gap-3 no-wrap'):
                        ui.label(number).classes('sc-benefit-no')
                        ui.label(text).classes('text-sm')
            ui.label('Connect  •  Discover  •  Grow').classes('text-sm font-bold mt-8').style('opacity:.9')

        # ---------------- right form ----------------
        with ui.column().classes('sc-auth-right items-center justify-center'):
            with ui.column().classes('sc-auth-card gap-0'):
                with ui.row().classes('items-center gap-2 mb-4').style(
                    'background:#FCEEF4;border-radius:20px;padding:6px 14px;'
                ):
                    ui.icon('favorite').style(f'color:{DARK_PINK};font-size:15px;')
                    ui.label('YOUR BUSINESS COMMUNITY').classes('text-xs font-bold tracking-wide').style(f'color:{DEEP_PINK};')

                ui.label('Create your account' if register else 'Welcome back').classes('text-3xl font-extrabold')
                ui.label(
                    'Join SHECONNECT in a few simple steps.' if register
                    else 'Sign in to continue to your SHECONNECT account.'
                ).classes('text-sm mt-1 mb-5 sc-muted')

                name = None
                if register:
                    ui.label('Full name').classes('text-sm font-bold mb-1')
                    name = ui.input(placeholder='Enter your full name').classes('w-full mb-3').props('outlined dense')

                ui.label('Email address').classes('text-sm font-bold mb-1')
                email = ui.input(placeholder='you@example.com').classes('w-full mb-3').props('outlined dense')

                ui.label('Password').classes('text-sm font-bold mb-1')
                password = ui.input(
                    placeholder='Create a password' if register else 'Enter your password',
                    password=True, password_toggle_button=True,
                ).classes('w-full mb-3').props('outlined dense')

                role = None
                if register:
                    ui.label('Account type').classes('text-sm font-bold mb-1')
                    role = ui.toggle(
                        {'customer': 'Customer', 'entrepreneur': 'Entrepreneur', 'admin': 'Admin'},
                        value='customer',
                    ).props('no-caps unelevated toggle-color=primary color=white text-color=primary')
                    descriptions = {
                        'customer': 'Customer accounts can discover businesses and send enquiries.',
                        'entrepreneur': 'Entrepreneur accounts can manage businesses and listings.',
                        'admin': 'Admin accounts can manage platform data and settings.',
                    }
                    hint = ui.label(descriptions['customer']).classes('text-xs sc-muted mt-2 mb-2')
                    role.on_value_change(lambda e: hint.set_text(descriptions.get(e.value, '')))

                def submit(_=None):
                    em = (email.value or '').strip().lower()
                    pw = password.value or ''
                    if not em or not pw:
                        notify_warning('Please enter your email and password.')
                        return
                    if '@' not in em or '.' not in em.split('@')[-1]:
                        notify_warning('Please enter a valid email address.')
                        return

                    if register:
                        nm = (name.value or '').strip()
                        if not nm:
                            notify_warning('Please enter your full name.')
                            return
                        if len(pw) < 6:
                            notify_warning('Password must be at least 6 characters.')
                            return
                        status, data = api_request('/api/register', 'POST', {
                            'name': nm, 'email': em, 'password': pw, 'role': role.value,
                        })
                        if status in (200, 201) and isinstance(data, dict) and data.get('success'):
                            notify_success('Account created successfully. Please sign in.')
                            ui.navigate.to('/')
                        else:
                            notify_error(data, 'Registration failed.')
                    else:
                        status, data = api_request('/api/login', 'POST', {'email': em, 'password': pw})
                        if status == 200 and isinstance(data, dict) and data.get('success'):
                            store()['user'] = data.get('user', {})
                            store()['page'] = 'Dashboard'
                            ui.navigate.to('/home')
                        else:
                            notify_error(data, 'Login failed.')

                password.on('keydown.enter', submit)
                if name is not None:
                    name.on('keydown.enter', submit)

                primary_button(
                    'Create SHECONNECT Account' if register else 'Sign in to SHECONNECT',
                    submit, 'person_add' if register else 'login',
                ).classes('w-full mt-3').style('min-height:46px;font-size:14px;')

                ui.separator().classes('my-4')

                with ui.row().classes('w-full justify-center items-center gap-1'):
                    ui.label('Already have an account?' if register else "Don't have an account?").classes('text-sm sc-muted')
                    ui.link('Sign in' if register else 'Create an account',
                            '/' if register else '/register').classes('font-bold').style(
                        f'color:{PINK};text-decoration:none;')

                ui.label('Secure access  •  Professional community').classes('text-xs text-center w-full mt-4 sc-muted')


@ui.page('/')
def login_page():
    setup_page()
    if logged_in():
        ui.navigate.to('/home')
        return
    render_auth(False)


@ui.page('/register')
def register_page():
    setup_page()
    if logged_in():
        ui.navigate.to('/home')
        return
    render_auth(True)


# =====================================================================
# LAYOUT / NAVIGATION
# =====================================================================

def logout():
    def do_logout():
        store().pop('user', None)
        store()['page'] = 'Dashboard'
        return True

    dialog, card = make_dialog(420)
    with card:
        ui.label('Logout').classes('text-xl font-bold')
        ui.label('Are you sure you want to logout?')

        def confirm():
            do_logout()
            dialog.close()
            ui.navigate.to('/')

        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Logout', confirm, 'logout')
    dialog.open()


def navigate_page(page):
    set_page(page)
    refresh_view()


def sidebar_pages():
    if is_admin():
        return [
            ('Dashboard', 'Admin Dashboard', 'dashboard'),
            ('User Management', 'User Management', 'group'),
            ('Business Management', 'Business Management', 'storefront'),
            ('Product Management', 'Product Management', 'inventory_2'),
            ('Category Management', 'Category Management', 'category'),
            ('Reports', 'Reports', 'bar_chart'),
            ('Enquiries', 'Enquiries', 'mail'),
            ('Settings', 'Settings', 'settings'),
        ]
    pages = [
        ('Dashboard', 'Dashboard', 'dashboard'),
        ('Discover Businesses', 'Discover Businesses', 'search'),
        ('Products & Services', 'Products & Services', 'inventory_2'),
        ('Enquiries', 'Enquiries', 'mail'),
        ('Saved Businesses', 'Saved Businesses', 'favorite_border'),
    ]
    if current_role() == 'entrepreneur':
        pages += [
            ('My Businesses', 'My Businesses', 'business'),
            ('My Listings', 'My Listings', 'sell'),
        ]
    pages.append(('Settings', 'Settings', 'settings'))
    return pages


def render_sidebar():
    user = current_user()
    role = current_role()

    with ui.column().classes('sc-sidebar gap-3 no-wrap'):
        with ui.row().classes('items-center gap-3 px-2 no-wrap'):
            ui.label('♀').classes('sc-brand-icon')
            with ui.column().classes('gap-0'):
                ui.label('SHECONNECT').classes('sc-brand')
                ui.label("Women's Business Hub").classes('text-xs sc-muted')

        ui.separator()

        with ui.row().classes('sc-userbox items-center gap-3 w-full no-wrap'):
            ui.label((user.get('name') or 'U')[:1].upper()).classes('sc-avatar')
            with ui.column().classes('gap-0').style('min-width:0;'):
                ui.label(user.get('name', 'User')).classes('font-bold text-sm truncate').style('max-width:150px;')
                ui.label(role.title() if role else 'Member').classes('text-xs').style(f'color:{PINK};')

        ui.label('WORKSPACE').classes('text-xs font-bold tracking-widest sc-muted px-3 mt-1')

        for key, label, icon in sidebar_pages():
            button = ui.button(
                label, icon=icon, on_click=lambda k=key: navigate_page(k),
            ).props('flat no-caps align=left').classes('sc-nav')
            if current_page() == key:
                button.classes('sc-nav-active')

        ui.space()
        ui.separator()
        ui.button('Logout', icon='logout', on_click=logout).props('flat no-caps align=left').classes('sc-nav')


@ui.page('/home')
def home_page():
    setup_page()
    if not logged_in():
        ui.navigate.to('/')
        return

    client = ui.context.client
    for cid in list(VIEWS):
        if cid not in getattr(Client, 'instances', {}):
            VIEWS.pop(cid, None)

    shell = ui.element('div').classes('w-full')

    def render():
        if not logged_in():
            ui.navigate.to('/')
            return
        shell.clear()
        with shell:
            with ui.row().classes('w-full min-h-screen gap-0 no-wrap'):
                render_sidebar()
                with ui.column().classes('sc-main gap-4'):
                    render_current_page()

    VIEWS[client.id] = render
    render()


def render_current_page():
    page = current_page()
    admin_only = {
        'User Management': admin_users_page,
        'Business Management': admin_businesses_page,
        'Product Management': admin_products_page,
        'Category Management': admin_categories_page,
        'Reports': admin_reports_page,
    }
    common = {
        'Dashboard': admin_dashboard_page if is_admin() else dashboard_page,
        'Enquiries': enquiries_page,
        'Settings': settings_page,
    }
    member_pages = {
        'Discover Businesses': businesses_page,
        'Products & Services': products_page,
        'Saved Businesses': saved_page,
    }
    entrepreneur_pages = {
        'My Businesses': my_businesses_page,
        'My Listings': my_listings_page,
    }

    func = common.get(page)
    if func is None and is_admin():
        func = admin_only.get(page)
    if func is None and not is_admin():
        func = member_pages.get(page)
        if func is None and current_role() == 'entrepreneur':
            func = entrepreneur_pages.get(page)

    if func:
        func()
    else:
        page_heading('Page unavailable', 'Choose an option from the sidebar.')
        secondary_button('Return to Dashboard', lambda: navigate_page('Dashboard'))


# =====================================================================
# DASHBOARDS
# =====================================================================

def activity_item(title, description, tag):
    with ui.row().classes('w-full items-start no-wrap gap-3 mt-2'):
        ui.label('●').style(f'color:{PINK};font-size:14px;')
        with ui.column().classes('gap-0 flex-1'):
            ui.label(title).classes('font-bold text-sm')
            ui.label(description).classes('text-sm sc-muted')
        ui.label(tag).classes('text-xs sc-muted')


def dashboard_page():
    user = current_user()
    page_heading('Welcome to SHECONNECT', 'Discover, connect and grow with women-led businesses.')

    with ui.row().classes('sc-hero items-center justify-between no-wrap'):
        with ui.column().classes('gap-2').style('max-width:700px;'):
            ui.label(f"Hello, {user.get('name', 'there')} 👋").classes('text-3xl font-bold')
            ui.label('Your business community is growing. Explore what SHECONNECT has to offer.').classes('text-sm leading-6')
        ui.icon('auto_awesome').classes('text-6xl').style('color:#fff;opacity:.8;')

    status, stats = api_request('/api/dashboard' + user_query())
    if status != 200 or not isinstance(stats, dict):
        notify_error(stats)
        stats = {}

    with ui.row().classes('w-full gap-4'):
        stat_card('Businesses', stats.get('businesses', 0), 'storefront', 'Listed on SHECONNECT')
        stat_card('Products & services', stats.get('products_services', 0), 'inventory_2', 'Available listings')
        stat_card('Pending enquiries', stats.get('pending_enquiries', 0), 'mail', 'Awaiting response')

    with ui.row().classes('w-full items-start gap-4'):
        with ui.card().classes('sc-card flex-1').style('min-width:300px;'):
            card_title('Recent Activity')
            activity_item('Business discovery', 'Explore women-led businesses and services.', 'Now')
            activity_item('Customer enquiries', 'Keep conversations organized and accessible.', 'Now')
            activity_item('MySQL connected', 'Your data is loaded from the database.', 'Live')

        with ui.card().classes('sc-card').style('min-width:270px;'):
            card_title('Quick Actions')
            if current_role() == 'entrepreneur':
                primary_button('Add Business', lambda: open_business_form(on_saved=refresh_view), 'add_business').classes('w-full mt-2')
                secondary_button('Add Product / Service', lambda: open_product_form(on_saved=refresh_view), 'add').classes('w-full mt-2')
            else:
                primary_button('Discover Businesses', lambda: navigate_page('Discover Businesses'), 'search').classes('w-full mt-2')
                secondary_button('Browse Products', lambda: navigate_page('Products & Services'), 'inventory_2').classes('w-full mt-2')
            secondary_button('View Enquiries', lambda: navigate_page('Enquiries'), 'mail').classes('w-full mt-2')


def admin_dashboard_page():
    page_heading('Admin Dashboard', 'Manage users, businesses, categories and reports.')

    status, stats = api_request('/api/admin/stats' + user_query())
    if status != 200 or not isinstance(stats, dict):
        notify_error(stats)
        stats = {}

    with ui.row().classes('w-full gap-4'):
        stat_card('Total Users', stats.get('total_users', 0), 'group', 'Platform records')
        stat_card('Entrepreneurs', stats.get('entrepreneurs', 0), 'business', 'Platform records')
        stat_card('Customers', stats.get('customers', 0), 'people', 'Platform records')
        stat_card('Businesses', stats.get('businesses', 0), 'storefront', 'Platform records')

    with ui.row().classes('w-full gap-4'):
        stat_card('Products / Services', stats.get('products_services', 0), 'inventory_2', 'Platform activity')
        stat_card('Total Enquiries', stats.get('enquiries', 0), 'mail', 'Platform activity')
        stat_card('Pending Enquiries', stats.get('pending_enquiries', 0), 'mark_email_unread', 'Platform activity')

    with ui.card().classes('sc-card w-full'):
        card_title('Administration', 'Manage the SHECONNECT platform.')
        with ui.row().classes('gap-3 mt-2'):
            primary_button('User Management', lambda: navigate_page('User Management'), 'group')
            primary_button('Business Management', lambda: navigate_page('Business Management'), 'storefront')
            primary_button('Product Management', lambda: navigate_page('Product Management'), 'inventory_2')
            primary_button('Category Management', lambda: navigate_page('Category Management'), 'category')
            primary_button('Reports', lambda: navigate_page('Reports'), 'bar_chart')


# =====================================================================
# DISCOVER BUSINESSES
# =====================================================================

def businesses_page():
    page_heading('Discover Businesses', 'Explore women-led businesses and discover new opportunities.')

    sel = {'cat': 'All'}
    names = ['All'] + [c.get('category_name', 'Uncategorized') for c in load_categories()]

    def render_list(_=None):
        results.clear()
        rows = get_businesses((search.value or '').strip())
        if sel['cat'] != 'All':
            rows = [r for r in rows if r.get('category_name') == sel['cat']]
        with results:
            if not rows:
                empty_state('No businesses found. Try another search.', 'storefront')
                return
            ui.label(f'{len(rows)} businesses found').classes('text-sm sc-muted')
            for business in rows:
                business_card(business, on_change=render_list)

    search = search_bar('Search by business name, category or location...', render_list)

    ui.label('Explore by category').classes('text-lg font-bold mt-2')
    chips = ui.row().classes('sc-chips w-full no-wrap gap-2')

    def render_chips():
        chips.clear()
        with chips:
            for name in names:
                button = ui.button(name, on_click=lambda n=name: select(n)).props('unelevated no-caps dense').classes('sc-chip')
                if name == sel['cat']:
                    button.classes('sc-chip-active')

    def select(name):
        sel['cat'] = name
        render_chips()
        render_list()

    render_chips()

    ui.label('Featured Businesses').classes('text-lg font-bold mt-2')
    results = ui.column().classes('w-full gap-3')
    render_list()


def business_card(business, on_change=None):
    refresh = on_change or refresh_view
    business_id = business.get('business_id')
    saved = business_id in saved_ids()

    with ui.card().classes('sc-card w-full'):
        with ui.row().classes('w-full items-start no-wrap gap-4'):
            ui.label('♀').classes('sc-brand-icon sc-icon-soft')

            with ui.column().classes('flex-1 gap-1'):
                ui.label(business.get('business_name', 'Business')).classes('text-lg font-bold')
                ui.label(business.get('category_name', 'Uncategorized')).classes('text-sm font-bold').style(f'color:{PINK};')
                info_line('place', business.get('address') or 'Location not provided')
                if business.get('contact_number'):
                    info_line('call', str(business['contact_number']))
                if business.get('website'):
                    info_line('language', str(business['website']))
                ui.label(business.get('description') or 'No description available.').classes('text-sm leading-6 mt-1')

            with ui.column().classes('gap-2 items-stretch').style('min-width:120px;'):
                small_button('Saved' if saved else 'Save',
                             lambda bid=business_id: toggle_saved(bid, refresh),
                             'favorite' if saved else 'favorite_border')
                small_button('View', lambda item=business: view_business(item), 'visibility', 'primary')
                if current_role() == 'entrepreneur' and str(business.get('user_id')) == str(user_id()):
                    small_button('Edit', lambda item=business: open_business_form(item, refresh), 'edit')
                    small_button('Delete', lambda item=business: confirm_delete_business(item, refresh), 'delete', 'danger')


def toggle_saved(business_id, refresh):
    ids = saved_ids()
    if business_id in ids:
        ids.remove(business_id)
        notify_success('Business removed from Saved Businesses.')
    else:
        ids.add(business_id)
        notify_success('Business added to Saved Businesses.')
    set_saved(ids)
    refresh()


def view_business(business):
    dialog, card = make_dialog(700)
    with card:
        ui.label(business.get('business_name', 'Business details')).classes('text-2xl font-bold')
        ui.label(business.get('category_name', 'Business')).classes('font-bold').style(f'color:{PINK};')
        ui.label(business.get('description') or 'No description provided.').classes('leading-6')
        info_line('place', business.get('address') or 'Location not provided')
        if business.get('contact_number'):
            info_line('call', str(business['contact_number']))
        if business.get('website'):
            info_line('language', str(business['website']))

        ui.separator()
        card_title('Products & Services')

        status, products = api_request(f"/api/businesses/{business.get('business_id')}/products")
        if status == 200 and isinstance(products, list) and products:
            for product in products:
                with ui.row().classes('w-full items-center justify-between no-wrap'):
                    with ui.column().classes('gap-0'):
                        ui.label(product.get('product_name', 'Listing')).classes('font-bold')
                        ui.label(str(product.get('product_type', 'service')).title()).classes('text-xs sc-muted')
                    ui.label(money(product.get('price'))).classes('font-bold').style(f'color:{DARK_PINK};')
        elif status == 200:
            ui.label('No products or services listed yet.').classes('sc-muted')
        else:
            ui.label('Unable to load listings.').classes('sc-muted')

        with ui.row().classes('w-full justify-end gap-2 mt-3'):
            if current_role() == 'customer':
                def enquire():
                    dialog.close()
                    open_enquiry_form(business.get('business_id'), business.get('business_name', 'Business'))
                primary_button('Send Enquiry', enquire, 'mail')
            secondary_button('Close', dialog.close)
    dialog.open()


# =====================================================================
# MY BUSINESSES (entrepreneur)
# =====================================================================

def my_businesses_page():
    page_heading('My Businesses', 'Manage your business information, contact details and listings.')
    primary_button('Add Business', lambda: open_business_form(on_saved=refresh_view), 'add_business')

    status, rows = api_request(f'/api/users/{user_id()}/businesses/full')
    if status != 200:
        notify_error(rows)
        empty_state('Unable to load your businesses.', 'storefront')
        return
    if not isinstance(rows, list) or not rows:
        empty_state("You haven't added a business yet. Create your first profile.", 'storefront')
        return
    for business in rows:
        business_card(business)


def open_business_form(business=None, on_saved=None):
    editing = business is not None
    categories = load_categories()
    if not categories:
        notify_warning('No categories available. Ask the administrator to add one.')
        return

    after = on_saved or refresh_view
    options = {str(c['category_id']): c['category_name'] for c in categories}

    selected = str(categories[0]['category_id'])
    if editing:
        if business.get('category_id') is not None and str(business['category_id']) in options:
            selected = str(business['category_id'])
        else:
            for c in categories:
                if c['category_name'] == business.get('category_name'):
                    selected = str(c['category_id'])
                    break

    dialog, card = make_dialog(650)
    with card:
        ui.label('Edit Business' if editing else 'Add Business').classes('text-2xl font-bold')
        name = ui.input('Business name', value=business.get('business_name', '') if editing else '').classes('w-full').props('outlined dense')
        category = ui.select(options, value=selected, label='Business category').classes('w-full').props('outlined dense')
        desc = ui.textarea('Description', value=business.get('description', '') if editing else '').classes('w-full').props('outlined dense')
        contact = ui.input('Contact number', value=business.get('contact_number', '') if editing else '').classes('w-full').props('outlined dense')
        address = ui.input('Address / location', value=business.get('address', '') if editing else '').classes('w-full').props('outlined dense')
        website = ui.input('Website', value=business.get('website', '') if editing else '').classes('w-full').props('outlined dense')

        def save():
            business_name = (name.value or '').strip()
            if not business_name:
                notify_warning('Enter a business name.')
                return
            payload = {
                'user_id': user_id(),
                'business_name': business_name,
                'category_id': int(category.value),
                'description': (desc.value or '').strip(),
                'contact_number': (contact.value or '').strip(),
                'address': (address.value or '').strip(),
                'website': (website.value or '').strip(),
            }
            endpoint = f"/api/businesses/{business['business_id']}" if editing else '/api/businesses'
            status, data = api_request(endpoint, 'PUT' if editing else 'POST', payload)
            if status in (200, 201) and isinstance(data, dict) and data.get('success'):
                dialog.close()
                notify_success('Business updated successfully.' if editing else 'Business added successfully.')
                after()
            else:
                notify_error(data, 'Unable to save business.')

        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Business', save, 'save')
    dialog.open()


def confirm_delete_business(business, after):
    confirm_dialog(
        'Delete Business?',
        f"Are you sure you want to delete {business.get('business_name', 'this business')}?",
        'Delete',
        lambda: api_action(f"/api/businesses/{business['business_id']}", 'DELETE',
                           {'user_id': user_id()}, 'Business deleted successfully.'),
        after,
        note='Its products and services will also be removed.',
    )


# =====================================================================
# PRODUCTS & SERVICES
# =====================================================================

def products_page():
    page_heading('Products & Services', 'Explore products and services offered by women-led businesses.')

    def render_list(_=None):
        results.clear()
        rows = get_products((search.value or '').strip())
        with results:
            if not rows:
                empty_state('No products or services found.', 'inventory_2')
                return
            ui.label(f'{len(rows)} listings found').classes('text-sm sc-muted')
            for product in rows:
                product_card(product)

    search = search_bar('Search products or services...', render_list)
    ui.label('Available Listings').classes('text-lg font-bold mt-2')
    results = ui.column().classes('w-full gap-3')
    render_list()


def product_card(item):
    with ui.card().classes('sc-card w-full'):
        with ui.row().classes('w-full items-start no-wrap gap-4'):
            ui.label('▣').classes('sc-brand-icon sc-icon-soft')
            with ui.column().classes('flex-1 gap-1'):
                ui.label(item.get('product_name', 'Listing')).classes('text-lg font-bold')
                ui.label(item.get('business_name', 'Business')).classes('text-sm').style('color:#777078;')
                ui.label(str(item.get('product_type', 'service')).title()).classes('sc-pill')
                ui.label(item.get('description') or 'No description provided.').classes('text-sm leading-6 mt-1')
            with ui.column().classes('items-end gap-3'):
                ui.label(money(item.get('price'))).classes('text-lg font-bold').style(f'color:{PINK};')
                if current_role() == 'customer':
                    primary_button(
                        'Make Enquiry',
                        lambda p=item: open_enquiry_form(
                            p.get('business_id'), p.get('business_name', 'Business'), p.get('product_name', '')),
                        'mail',
                    )


def my_listings_page():
    page_heading('My Listings', 'Edit or remove your products and services whenever you need.')
    primary_button('Add Product / Service', lambda: open_product_form(on_saved=refresh_view), 'add')

    status, rows = api_request(f'/api/users/{user_id()}/products')
    if status != 200:
        notify_error(rows)
        empty_state('Unable to load your listings.', 'inventory_2')
        return
    if not isinstance(rows, list) or not rows:
        empty_state("You haven't added any products or services yet.", 'inventory_2')
        return

    for product in rows:
        with ui.card().classes('sc-card w-full'):
            with ui.row().classes('w-full items-center no-wrap gap-4'):
                ui.label('✦').classes('sc-brand-icon sc-icon-soft')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label(product.get('product_name', 'Listing')).classes('text-lg font-bold')
                    ui.label(f"{product.get('business_name', 'Business')}  •  {str(product.get('product_type', 'service')).title()}").classes('text-sm sc-muted')
                    ui.label(money(product.get('price'))).classes('font-bold').style(f'color:{PINK};')
                    ui.label(product.get('description') or 'No description.').classes('text-sm sc-muted')
                with ui.row().classes('gap-2 no-wrap'):
                    small_button('Edit', lambda item=product: open_product_form(item, refresh_view), 'edit', 'primary')
                    small_button('Delete', lambda item=product: confirm_delete_product(item, refresh_view), 'delete', 'danger')


def open_product_form(product=None, on_saved=None):
    editing = product is not None
    after = on_saved or refresh_view
    businesses = get_data(f'/api/users/{user_id()}/businesses')
    if not isinstance(businesses, list) or not businesses:
        notify_warning('Add a business profile before adding a product or service.')
        return

    options = {str(b['business_id']): b['business_name'] for b in businesses}
    selected = str(product.get('business_id')) if editing and str(product.get('business_id')) in options else str(businesses[0]['business_id'])

    dialog, card = make_dialog(650)
    with card:
        ui.label('Edit Product / Service' if editing else 'Add Product / Service').classes('text-2xl font-bold')
        business = ui.select(options, value=selected, label='Business').classes('w-full').props('outlined dense')
        if editing:
            business.props('readonly')
        name = ui.input('Product / service name', value=product.get('product_name', '') if editing else '').classes('w-full').props('outlined dense')
        kind = ui.select({'product': 'Product', 'service': 'Service'},
                         value=str(product.get('product_type', 'service')) if editing else 'service',
                         label='Listing type').classes('w-full').props('outlined dense')
        desc = ui.textarea('Description', value=product.get('description') or '' if editing else '').classes('w-full').props('outlined dense')
        price = ui.input('Price (₹)', value='' if not editing or product.get('price') is None else str(product.get('price'))).classes('w-full').props('outlined dense')

        def save():
            nm = (name.value or '').strip()
            raw = (price.value or '').strip()
            if not nm:
                notify_warning('Enter a listing name.')
                return
            if raw:
                try:
                    if float(raw) < 0:
                        raise ValueError
                except ValueError:
                    notify_warning('Enter a valid non-negative price.')
                    return
            payload = {
                'user_id': user_id(),
                'business_id': int(business.value),
                'product_name': nm,
                'description': (desc.value or '').strip(),
                'price': raw or None,
                'product_type': kind.value,
            }
            endpoint = f"/api/products/{product['product_id']}" if editing else '/api/products'
            status, data = api_request(endpoint, 'PUT' if editing else 'POST', payload)
            if status in (200, 201) and isinstance(data, dict) and data.get('success'):
                dialog.close()
                notify_success('Listing updated successfully.' if editing else 'Listing added successfully.')
                after()
            else:
                notify_error(data, 'Unable to save listing.')

        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Listing', save, 'save')
    dialog.open()


def confirm_delete_product(product, after):
    confirm_dialog(
        'Delete Listing?',
        f"Delete {product.get('product_name', 'this listing')}?",
        'Delete',
        lambda: api_action(f"/api/products/{product['product_id']}", 'DELETE',
                           {'user_id': user_id()}, 'Listing deleted successfully.'),
        after,
    )


# =====================================================================
# SAVED BUSINESSES
# =====================================================================

def saved_page():
    page_heading('Saved Businesses', 'Quickly access the businesses you are interested in.')
    ids = saved_ids()
    rows = [b for b in get_businesses() if b.get('business_id') in ids]

    if not rows:
        with ui.card().classes('sc-card w-full items-center'):
            empty_state('No saved businesses yet. Visit Discover Businesses and save the ones you like.', 'favorite_border')
            primary_button('Discover Businesses', lambda: navigate_page('Discover Businesses'), 'search')
        return

    for business in rows:
        business_card(business)


# =====================================================================
# ENQUIRIES
# =====================================================================

def enquiries_page():
    page_heading(
        'Enquiry Monitoring' if is_admin() else 'Enquiries',
        'Monitor customer enquiries across the platform.' if is_admin()
        else 'Manage customer enquiries and keep conversations organized.',
    )

    sel = {'status': 'all'}
    holder = ui.column().classes('w-full gap-4')

    def load(_=None):
        holder.clear()
        endpoint = ('/api/admin/enquiries' if is_admin() else '/api/enquiries') + user_query()
        status, rows = api_request(endpoint)
        with holder:
            if status != 200:
                notify_error(rows)
                empty_state('Unable to load enquiries.', 'mail')
                return
            if not isinstance(rows, list) or not rows:
                empty_state('No enquiries found yet.', 'mail')
                return

            counts = {s: sum(1 for r in rows if str(r.get('status', '')).lower() == s)
                      for s in ('pending', 'replied', 'closed')}
            with ui.row().classes('w-full gap-4'):
                stat_card('Pending', counts['pending'], 'mark_email_unread')
                stat_card('Replied', counts['replied'], 'mark_email_read')
                stat_card('Closed', counts['closed'], 'check_circle')

            def set_filter(e):
                sel['status'] = e.value
                load()

            ui.toggle(
                {'all': 'All', 'pending': 'Pending', 'replied': 'Replied', 'closed': 'Closed'},
                value=sel['status'], on_change=set_filter,
            ).props('no-caps unelevated toggle-color=primary color=white text-color=primary')

            shown = rows if sel['status'] == 'all' else [
                r for r in rows if str(r.get('status', '')).lower() == sel['status']]

            ui.label('Recent Enquiries').classes('text-lg font-bold')
            if not shown:
                empty_state('No enquiries in this status.', 'mail')
            for enquiry in shown:
                enquiry_card(enquiry, load)

    load()


def enquiry_card(e, after):
    status = str(e.get('status', 'pending')).lower()

    with ui.card().classes('sc-card w-full'):
        with ui.row().classes('w-full items-start no-wrap gap-3'):
            ui.label((e.get('customer_name') or 'C')[:1].upper()).classes('sc-avatar')

            with ui.column().classes('flex-1 gap-1'):
                with ui.row().classes('w-full items-center justify-between no-wrap'):
                    ui.label(e.get('subject') or 'Enquiry').classes('text-lg font-bold')
                    status_pill(status)

                ui.label(f"From: {e.get('customer_name', 'Customer')}").classes('text-sm sc-muted')
                ui.label(e.get('business_name', 'Business')).classes('text-sm font-bold').style(f'color:{PINK};')
                ui.label(e.get('message', '')).classes('text-sm leading-6')

                if e.get('reply_message'):
                    with ui.column().classes('gap-1 w-full').style(
                        f'background:{SOFT_PINK};padding:12px;border-radius:10px;'
                    ):
                        ui.label('Response').classes('font-bold text-sm').style(f'color:{DARK_PINK};')
                        ui.label(e['reply_message']).classes('text-sm')

                with ui.row().classes('gap-2 mt-2'):
                    small_button('View', lambda item=e: view_enquiry(item), 'visibility')

                    if is_admin():
                        small_button('Update Status', lambda item=e: admin_update_enquiry_dialog(item, after), 'edit', 'primary')
                        small_button('Delete', lambda item=e: confirm_delete_enquiry(item, after), 'delete', 'danger')
                    elif current_role() == 'entrepreneur':
                        if status != 'closed':
                            small_button('Reply', lambda item=e: reply_enquiry_dialog(item, after), 'reply', 'primary')
                            small_button('Close', lambda item=e: close_enquiry(item, after), 'check_circle')
                        small_button('Delete', lambda item=e: confirm_delete_enquiry(item, after), 'delete', 'danger')
                    else:
                        small_button('Edit', lambda item=e: edit_enquiry_dialog(item, after), 'edit', 'primary')
                        small_button('Delete', lambda item=e: confirm_delete_enquiry(item, after), 'delete', 'danger')


def view_enquiry(e):
    dialog, card = make_dialog(650)
    with card:
        ui.label(e.get('subject') or 'Enquiry Details').classes('text-2xl font-bold')
        ui.label('Business: ' + str(e.get('business_name', 'Business'))).classes('font-bold').style(f'color:{PINK};')
        ui.label('Customer: ' + str(e.get('customer_name', 'Customer'))).classes('text-sm sc-muted')
        status_pill(e.get('status'))
        ui.separator()
        card_title('Message')
        ui.label(e.get('message', '')).classes('leading-6')
        ui.separator()
        card_title('Entrepreneur Response')
        ui.label(e.get('reply_message') or 'No response yet.').classes('leading-6')
        if e.get('replied_at'):
            ui.label('Replied at: ' + str(e['replied_at'])).classes('text-xs sc-muted')
        if e.get('created_at'):
            ui.label('Created: ' + str(e['created_at'])).classes('text-xs sc-muted')
        with ui.row().classes('w-full justify-end'):
            secondary_button('Close', dialog.close)
    dialog.open()


def reply_enquiry_dialog(e, after):
    dialog, card = make_dialog(620)
    with card:
        ui.label('Reply to Customer').classes('text-2xl font-bold')
        ui.label(f"To: {e.get('customer_name', 'Customer')}  •  {e.get('business_name', 'Business')}").classes('text-sm').style(f'color:{PINK};')
        ui.label(e.get('subject', 'Enquiry')).classes('font-bold')
        ui.label(e.get('message', '')).classes('text-sm sc-muted')
        reply = ui.textarea('Your response', value=e.get('reply_message') or '').classes('w-full').props('outlined dense')

        def send():
            message = (reply.value or '').strip()
            if not message:
                notify_warning('Please type a response before sending.')
                return
            if api_action(f"/api/enquiries/{e['enquiry_id']}", 'PUT',
                          {'user_id': user_id(), 'status': 'replied', 'reply_message': message},
                          'Your response has been sent to the customer.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Send Reply', send, 'send')
    dialog.open()


def close_enquiry(e, after):
    dialog, card = make_dialog(420)
    with card:
        ui.label('Close Enquiry').classes('text-xl font-bold')
        ui.label('Are you sure you want to close this enquiry?')

        def go():
            if api_action(f"/api/enquiries/{e['enquiry_id']}", 'PUT',
                          {'user_id': user_id(), 'status': 'closed'}, 'Enquiry closed successfully.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Close Enquiry', go, 'check_circle')
    dialog.open()


def edit_enquiry_dialog(e, after):
    resets = bool(e.get('reply_message')) or str(e.get('status', '')).lower() in ('replied', 'closed')
    dialog, card = make_dialog(620)
    with card:
        ui.label('Edit Enquiry').classes('text-2xl font-bold')
        ui.label(e.get('business_name', 'Business')).classes('font-bold').style(f'color:{PINK};')
        subject = ui.input('Subject', value=e.get('subject') or '').classes('w-full').props('outlined dense')
        message = ui.textarea('Message', value=e.get('message') or '').classes('w-full').props('outlined dense')
        if resets:
            ui.label('This enquiry already has a response or is closed. Saving will clear the old '
                     'response and return it to Pending.').classes('text-xs').style(f'color:{WARNING};')

        def save():
            sub = (subject.value or '').strip()
            msg = (message.value or '').strip()
            if not sub or not msg:
                notify_warning('Please enter both a subject and message.')
                return
            if api_action(f"/api/enquiries/{e['enquiry_id']}", 'PUT',
                          {'user_id': user_id(), 'action': 'edit', 'subject': sub, 'message': msg},
                          'Enquiry updated successfully.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Changes', save, 'save')
    dialog.open()


def admin_update_enquiry_dialog(e, after):
    dialog, card = make_dialog(540)
    with card:
        ui.label('Update Enquiry Status').classes('text-xl font-bold')
        status_box = ui.select({'pending': 'Pending', 'replied': 'Replied', 'closed': 'Closed'},
                               value=str(e.get('status', 'pending')).lower(), label='Status').classes('w-full').props('outlined dense')
        reply = ui.textarea('Reply message (required when status is Replied)',
                            value=e.get('reply_message') or '').classes('w-full').props('outlined dense')

        def save():
            payload = {'user_id': user_id(), 'status': status_box.value}
            if status_box.value == 'replied':
                message = (reply.value or '').strip()
                if not message:
                    notify_warning('Enter a reply message when status is Replied.')
                    return
                payload['reply_message'] = message
            if api_action(f"/api/admin/enquiries/{e['enquiry_id']}", 'PUT', payload, 'Enquiry updated successfully.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Status', save, 'save')
    dialog.open()


def confirm_delete_enquiry(e, after):
    def action():
        endpoint = (f"/api/admin/enquiries/{e['enquiry_id']}" if is_admin()
                    else f"/api/enquiries/{e['enquiry_id']}?user_id={user_id()}")
        return api_action(endpoint, 'DELETE', {'user_id': user_id()}, 'Enquiry deleted successfully.')

    confirm_dialog('Delete Enquiry?', f"Delete '{e.get('subject', 'this enquiry')}'?",
                   'Delete', action, after, note='This action cannot be undone.')


def open_enquiry_form(business_id, business_name, product_name=''):
    if current_role() != 'customer':
        notify_warning('Please sign in as a customer to send an enquiry.')
        return

    dialog, card = make_dialog(600)
    with card:
        ui.label('Make an Enquiry').classes('text-2xl font-bold')
        ui.label(f'To: {business_name}').classes('font-bold').style(f'color:{PINK};')
        subject = ui.input('Subject', value=f'Enquiry about {product_name}' if product_name else 'Business enquiry').classes('w-full').props('outlined dense')
        message = ui.textarea('Message', placeholder='Write your enquiry...').classes('w-full').props('outlined dense')

        def send():
            sub = (subject.value or '').strip()
            msg = (message.value or '').strip()
            if not sub or not msg:
                notify_warning('Please enter both a subject and message.')
                return
            status, data = api_request('/api/enquiries', 'POST', {
                'customer_id': user_id(), 'business_id': business_id, 'subject': sub, 'message': msg,
            })
            if status in (200, 201) and isinstance(data, dict) and data.get('success'):
                dialog.close()
                notify_success('Your enquiry was sent successfully.')
                set_page('Enquiries')
                refresh_view()
            else:
                notify_error(data, 'Unable to send enquiry.')

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Send Enquiry', send, 'send')
    dialog.open()


# =====================================================================
# SETTINGS
# =====================================================================

def settings_page():
    page_heading('Settings', 'Manage your SHECONNECT account and application preferences.')
    user = current_user()

    def setting_card(icon, title, description, action):
        with ui.card().classes('sc-card w-full').style('max-width:900px;'):
            with ui.row().classes('w-full items-center no-wrap gap-4'):
                ui.icon(icon).classes('sc-brand-icon sc-icon-soft').style('font-size:26px;')
                with ui.column().classes('flex-1 gap-0'):
                    ui.label(title).classes('font-bold text-base')
                    ui.label(description).classes('text-sm sc-muted')
                secondary_button('Manage', action)

    setting_card('person', 'Account Information', f"{user.get('name', '')} • {user.get('email', '')}", edit_account_dialog)
    setting_card('badge', 'Account Type', str(user.get('role', 'customer')).title(), account_type_dialog)
    setting_card('lock', 'Privacy & Security', 'Change your password and keep your account secure.', change_password_dialog)
    setting_card('tune', 'Application Preferences', 'SHECONNECT web application settings.', preferences_dialog)

    with ui.card().classes('sc-card w-full').style('max-width:900px;'):
        card_title('Account Access', 'Sign out when you have finished using SHECONNECT.')
        secondary_button('Logout', logout, 'logout').classes('mt-2')


def edit_account_dialog():
    user = current_user()
    dialog, card = make_dialog(520)
    with card:
        ui.label('Edit Account Information').classes('text-2xl font-bold')
        ui.label('Update your name or email address.').classes('sc-muted')
        name = ui.input('Name', value=user.get('name', '')).classes('w-full').props('outlined dense')
        email = ui.input('Email', value=user.get('email', '')).classes('w-full').props('outlined dense')

        def save():
            new_name = (name.value or '').strip()
            new_email = (email.value or '').strip().lower()
            if not new_name or '@' not in new_email:
                notify_warning('Please enter a valid name and email address.')
                return
            status, data = api_request(f'/api/users/{user_id()}', 'PUT', {
                'request_user_id': user_id(), 'name': new_name, 'email': new_email,
            })
            if status == 200 and isinstance(data, dict) and data.get('success'):
                store()['user'] = data.get('user', user)
                dialog.close()
                notify_success('Your account information has been updated.')
                refresh_view()
            else:
                notify_error(data, 'Unable to update your account.')

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Changes', save, 'save')
    dialog.open()


def account_type_dialog():
    dialog, card = make_dialog(460)
    with card:
        ui.label('Account Type').classes('text-xl font-bold')
        ui.label(f"Your SHECONNECT account type is: {str(current_user().get('role', 'customer')).title()}")
        ui.label('Account type is controlled by the system and cannot be changed here.').classes('text-sm sc-muted')
        with ui.row().classes('w-full justify-end'):
            secondary_button('Close', dialog.close)
    dialog.open()


def preferences_dialog():
    dialog, card = make_dialog(460)
    with card:
        ui.label('Application Preferences').classes('text-xl font-bold')
        ui.label('Your professional pink SHECONNECT theme is currently active.')
        with ui.row().classes('w-full justify-end'):
            secondary_button('Close', dialog.close)
    dialog.open()


def change_password_dialog():
    user = current_user()
    dialog, card = make_dialog(520)
    with card:
        ui.label('Change Password').classes('text-2xl font-bold')
        ui.label('Enter your current password before choosing a new one.').classes('sc-muted')
        current = ui.input('Current Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense')
        new = ui.input('New Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense')
        confirm = ui.input('Confirm New Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense')

        def save():
            if not current.value or not new.value or not confirm.value:
                notify_warning('Please fill in all password fields.')
                return
            if len(new.value) < 6:
                notify_warning('New password must be at least 6 characters.')
                return
            if new.value != confirm.value:
                notify_warning('New passwords do not match.')
                return
            status, data = api_request(f'/api/users/{user_id()}', 'PUT', {
                'request_user_id': user_id(),
                'name': user.get('name', ''), 'email': user.get('email', ''),
                'current_password': current.value, 'new_password': new.value,
            })
            if status == 200 and isinstance(data, dict) and data.get('success'):
                dialog.close()
                notify_success('Your password has been changed successfully.')
            else:
                notify_error(data, 'Unable to change your password.')

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Update Password', save, 'lock')
    dialog.open()


# =====================================================================
# ADMIN: USER MANAGEMENT
# =====================================================================

def admin_users_page():
    page_heading('User Management', 'View and manage registered SHECONNECT accounts.')
    back_bar()

    holder = ui.column().classes('w-full gap-4')
    search_box = {'value': ''}

    def load(_=None):
        holder.clear()
        status, rows = api_request('/api/admin/users' + user_query())
        with holder:
            if status != 200 or not isinstance(rows, list):
                notify_error(rows)
                empty_state('Unable to load users.', 'group')
                return
            rows.sort(key=lambda u: int(u.get('user_id', 0) or 0))

            with ui.row().classes('w-full gap-4'):
                stat_card('Total Users', len(rows), 'group')
                stat_card('Entrepreneurs', sum(1 for u in rows if u.get('role') == 'entrepreneur'), 'business')
                stat_card('Customers', sum(1 for u in rows if u.get('role') == 'customer'), 'people')
                stat_card('Administrators', sum(1 for u in rows if u.get('role') == 'admin'), 'admin_panel_settings')

            term = search_box['value'].strip().lower()
            if term:
                rows = [u for u in rows if term in str(u.get('name', '')).lower() or term in str(u.get('email', '')).lower()]

            with ui.card().classes('sc-card w-full'):
                with ui.row().classes('w-full items-center justify-between no-wrap'):
                    ui.label(f'All Users ({len(rows)})').classes('text-lg font-bold')
                    secondary_button('Refresh', load, 'refresh')

                def on_search(e):
                    search_box['value'] = e.value or ''

                user_search = ui.input(placeholder='Search users by name or email...', value=search_box['value']).props('outlined dense').classes('w-full')
                user_search.on_value_change(on_search)
                user_search.on('keydown.enter', load)

                columns = 'grid-template-columns:70px 1.1fr 1.7fr 130px 170px 180px;'
                with ui.element('div').classes('sc-table-scroll'):
                    with ui.element('div').classes('sc-grid sc-grid-head').style(columns):
                        for heading in ('ID', 'Name', 'Email', 'Role', 'Created', 'Actions'):
                            ui.label(heading).classes('sc-cell')

                    if not rows:
                        ui.label('No users found.').classes('sc-muted p-6')

                    for u in rows:
                        with ui.element('div').classes('sc-grid sc-grid-row').style(columns):
                            ui.label(str(u.get('user_id', ''))).classes('sc-cell')
                            ui.label(u.get('name') or '—').classes('sc-cell font-bold')
                            ui.label(u.get('email') or '—').classes('sc-cell')
                            with ui.element('div').classes('sc-cell'):
                                ui.label(str(u.get('role', '')).title()).classes('sc-pill')
                            ui.label(str(u.get('created_at') or '—')).classes('sc-cell')
                            with ui.row().classes('sc-cell gap-1 no-wrap'):
                                if str(u.get('user_id')) == str(user_id()):
                                    ui.label('You').classes('sc-pill')
                                else:
                                    small_button('Edit', lambda x=u: admin_edit_user(x, load), 'edit', 'primary')
                                    small_button('Delete', lambda x=u: admin_delete_user(x, load), 'delete', 'danger')

    load()


def admin_edit_user(u, after):
    dialog, card = make_dialog(520)
    with card:
        ui.label('Edit User').classes('text-2xl font-bold')
        name = ui.input('Name', value=u.get('name', '')).classes('w-full').props('outlined dense')
        email = ui.input('Email', value=u.get('email', '')).classes('w-full').props('outlined dense')
        role = ui.select({'customer': 'Customer', 'entrepreneur': 'Entrepreneur', 'admin': 'Administrator'},
                         value=u.get('role', 'customer'), label='Role').classes('w-full').props('outlined dense')

        def save():
            nm = (name.value or '').strip()
            em = (email.value or '').strip().lower()
            if not nm or '@' not in em:
                notify_warning('Enter a valid name and email.')
                return
            if api_action(f"/api/admin/users/{u['user_id']}", 'PUT',
                          {'user_id': user_id(), 'name': nm, 'email': em, 'role': role.value},
                          'User updated successfully.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Changes', save, 'save')
    dialog.open()


def admin_delete_user(u, after):
    confirm_dialog(
        'Delete User Account?',
        f"Are you sure you want to delete {u.get('name', 'this user')}?",
        'Delete User',
        lambda: api_action(f"/api/admin/users/{u['user_id']}?user_id={user_id()}", 'DELETE',
                           None, 'User account deleted successfully.'),
        after,
        note='Their related data may also be removed.',
    )


# =====================================================================
# ADMIN: BUSINESS MANAGEMENT
# =====================================================================

def admin_businesses_page():
    page_heading('Business Management', 'Review and manage business listings on SHECONNECT.')
    back_bar()

    def load(_=None):
        results.clear()
        status, rows = api_request('/api/admin/businesses' + user_query())
        with results:
            if status != 200 or not isinstance(rows, list):
                notify_error(rows)
                empty_state('Unable to load businesses.', 'storefront')
                return
            term = (search.value or '').strip().lower()
            if term:
                rows = [b for b in rows if term in str(b.get('business_name', '')).lower()
                        or term in str(b.get('address', '')).lower()
                        or term in str(b.get('owner_name', '')).lower()
                        or term in str(b.get('category_name', '')).lower()]
            if not rows:
                empty_state('No business listings found.', 'storefront')
                return
            ui.label(f'Business Listings ({len(rows)})').classes('text-lg font-bold')
            for b in rows:
                with ui.card().classes('sc-card w-full'):
                    with ui.row().classes('w-full items-start no-wrap gap-4'):
                        ui.label('♀').classes('sc-brand-icon sc-icon-soft')
                        with ui.column().classes('flex-1 gap-1'):
                            ui.label(b.get('business_name', 'Business')).classes('text-lg font-bold').style(f'color:{DEEP_PINK};')
                            ui.label(f"Owner: {b.get('owner_name', '')}   |   Category: {b.get('category_name', '')}").classes('text-sm sc-muted')
                            info_line('place', b.get('address') or 'No address')
                            ui.label(b.get('description') or 'No description provided.').classes('text-sm')
                        with ui.row().classes('gap-2 no-wrap'):
                            small_button('View', lambda x=b: view_business(x), 'visibility')
                            small_button('Edit', lambda x=b: admin_edit_business(x, load), 'edit', 'primary')
                            small_button('Delete', lambda x=b: admin_delete_business(x, load), 'delete', 'danger')

    search = search_bar('Search businesses by name, owner, category or location...', load)
    results = ui.column().classes('w-full gap-3')
    load()


def admin_edit_business(b, after):
    categories = load_categories()
    if not categories:
        notify_warning('No categories available.')
        return
    options = {str(c['category_id']): c['category_name'] for c in categories}
    selected = next((str(c['category_id']) for c in categories if c['category_name'] == b.get('category_name')),
                    str(categories[0]['category_id']))

    dialog, card = make_dialog(650)
    with card:
        ui.label('Edit Business').classes('text-2xl font-bold')
        ui.label(f"Owner: {b.get('owner_name', '')}").classes('text-sm').style(f'color:{PINK};')
        name = ui.input('Business name', value=b.get('business_name', '')).classes('w-full').props('outlined dense')
        category = ui.select(options, value=selected, label='Category').classes('w-full').props('outlined dense')
        desc = ui.textarea('Description', value=b.get('description') or '').classes('w-full').props('outlined dense')
        contact = ui.input('Contact number', value=b.get('contact_number') or '').classes('w-full').props('outlined dense')
        address = ui.input('Address', value=b.get('address') or '').classes('w-full').props('outlined dense')
        website = ui.input('Website', value=b.get('website') or '').classes('w-full').props('outlined dense')

        def save():
            if not (name.value or '').strip():
                notify_warning('Business name is required.')
                return
            payload = {
                'user_id': user_id(),
                'business_name': name.value.strip(),
                'category_id': int(category.value),
                'description': (desc.value or '').strip(),
                'contact_number': (contact.value or '').strip(),
                'address': (address.value or '').strip(),
                'website': (website.value or '').strip(),
            }
            if api_action(f"/api/admin/businesses/{b['business_id']}", 'PUT', payload, 'Business updated successfully.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Changes', save, 'save')
    dialog.open()


def admin_delete_business(b, after):
    confirm_dialog(
        'Delete Business?',
        f"Delete business listing '{b.get('business_name', 'Business')}'?",
        'Delete Business',
        lambda: api_action(f"/api/admin/businesses/{b['business_id']}", 'DELETE',
                           {'user_id': user_id()}, 'Business deleted successfully.'),
        after,
        note='Its related products and enquiries may also be removed.',
    )


# =====================================================================
# ADMIN: PRODUCT MANAGEMENT
# =====================================================================

def admin_products_page():
    page_heading('Product Management', 'View, edit and delete every product or service on SHECONNECT.')
    back_bar()

    def load(_=None):
        results.clear()
        status, rows = api_request('/api/admin/products' + user_query())
        with results:
            if status != 200 or not isinstance(rows, list):
                notify_error(rows)
                empty_state('Unable to load products.', 'inventory_2')
                return
            term = (search.value or '').strip().lower()
            if term:
                rows = [p for p in rows if term in str(p.get('product_name', '')).lower()
                        or term in str(p.get('business_name', '')).lower()
                        or term in str(p.get('owner_name', '')).lower()
                        or term in str(p.get('product_type', '')).lower()]
            if not rows:
                empty_state('No products or services found.', 'inventory_2')
                return
            ui.label(f'All Products & Services ({len(rows)})').classes('text-lg font-bold')
            for p in rows:
                with ui.card().classes('sc-card w-full'):
                    with ui.row().classes('w-full items-center no-wrap gap-4'):
                        ui.label('✦').classes('sc-brand-icon sc-icon-soft')
                        with ui.column().classes('flex-1 gap-1'):
                            ui.label(p.get('product_name') or 'Unnamed Listing').classes('text-lg font-bold')
                            ui.label(f"Business: {p.get('business_name', '')}  •  Owner: {p.get('owner_name', '')}").classes('text-sm sc-muted')
                            ui.label(f"Type: {str(p.get('product_type', 'service')).title()}  •  Price: {money(p.get('price'))}").classes('text-sm font-bold').style(f'color:{PINK};')
                            ui.label((p.get('description') or 'No description')[:140]).classes('text-sm sc-muted')
                        with ui.row().classes('gap-2 no-wrap'):
                            small_button('View', lambda x=p: admin_view_product(x), 'visibility')
                            small_button('Edit', lambda x=p: admin_edit_product(x, load), 'edit', 'primary')
                            small_button('Delete', lambda x=p: admin_delete_product(x, load), 'delete', 'danger')

    search = search_bar('Search products, services, businesses or owners...', load)
    results = ui.column().classes('w-full gap-3')
    load()


def admin_view_product(p):
    dialog, card = make_dialog(560)
    with card:
        ui.label('Product / Service Details').classes('text-2xl font-bold')
        ui.label(p.get('product_name', '')).classes('text-lg font-bold').style(f'color:{PINK};')
        ui.label(f"Business: {p.get('business_name', '')}")
        ui.label(f"Owner: {p.get('owner_name', '')}")
        ui.label(f"Type: {str(p.get('product_type', 'service')).title()}")
        ui.label(f"Price: {money(p.get('price'))}").classes('font-bold')
        ui.label(p.get('description') or 'No description provided.').classes('sc-muted')
        with ui.row().classes('w-full justify-end'):
            secondary_button('Close', dialog.close)
    dialog.open()


def admin_edit_product(p, after):
    dialog, card = make_dialog(600)
    with card:
        ui.label('Edit Product / Service').classes('text-2xl font-bold')
        ui.label(f"Business: {p.get('business_name', 'Unknown Business')}").classes('text-sm').style(f'color:{PINK};')
        name = ui.input('Product / service name', value=p.get('product_name', '')).classes('w-full').props('outlined dense')
        kind = ui.select({'product': 'Product', 'service': 'Service'}, value=str(p.get('product_type') or 'service'),
                         label='Type').classes('w-full').props('outlined dense')
        desc = ui.textarea('Description', value=p.get('description') or '').classes('w-full').props('outlined dense')
        price = ui.input('Price (₹)', value='' if p.get('price') is None else str(p.get('price'))).classes('w-full').props('outlined dense')

        def save():
            nm = (name.value or '').strip()
            raw = (price.value or '').strip()
            if not nm:
                notify_warning('Product/service name is required.')
                return
            if raw:
                try:
                    if float(raw) < 0:
                        raise ValueError
                except ValueError:
                    notify_warning('Price must be a valid non-negative number.')
                    return
            payload = {'user_id': user_id(), 'product_name': nm, 'description': (desc.value or '').strip(),
                       'price': raw or None, 'product_type': kind.value}
            if api_action(f"/api/admin/products/{p['product_id']}", 'PUT', payload, 'Product/service updated successfully.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Changes', save, 'save')
    dialog.open()


def admin_delete_product(p, after):
    confirm_dialog(
        'Delete Listing?',
        f"Delete '{p.get('product_name', 'this listing')}'?",
        'Delete Listing',
        lambda: api_action(f"/api/admin/products/{p['product_id']}", 'DELETE',
                           {'user_id': user_id()}, 'Product/service deleted successfully.'),
        after,
        note='This cannot be undone.',
    )


# =====================================================================
# ADMIN: CATEGORY MANAGEMENT
# =====================================================================

def admin_categories_page():
    page_heading('Category Management', 'Add, edit and remove categories used for business listings.')
    back_bar()

    holder = ui.column().classes('w-full gap-4')

    def load(_=None):
        holder.clear()
        categories = load_categories()
        with holder:
            with ui.card().classes('sc-card w-full'):
                ui.label('Add New Category').classes('text-lg font-bold')
                with ui.row().classes('w-full items-center no-wrap gap-3'):
                    new_name = ui.input(placeholder='Category name').props('outlined dense').classes('flex-1')
                    new_desc = ui.input(placeholder='Description (optional)').props('outlined dense').classes('flex-1')

                    def add():
                        nm = (new_name.value or '').strip()
                        if not nm:
                            notify_warning('Enter a category name.')
                            return
                        if api_action('/api/admin/categories', 'POST',
                                      {'user_id': user_id(), 'category_name': nm,
                                       'description': (new_desc.value or '').strip()},
                                      'Category added successfully.'):
                            load()

                    primary_button('Add Category', add, 'add')

            ui.label(f'Existing Categories ({len(categories)})').classes('text-lg font-bold')
            if not categories:
                empty_state('No categories found.', 'category')
                return
            for c in categories:
                with ui.card().classes('sc-card w-full'):
                    with ui.row().classes('w-full items-center no-wrap gap-3'):
                        ui.label('▤').classes('sc-brand-icon')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label(c.get('category_name', 'Category')).classes('font-bold')
                            ui.label(c.get('description') or 'No description').classes('text-xs sc-muted')
                        small_button('Edit', lambda x=c: admin_edit_category(x, load), 'edit', 'primary')
                        small_button('Delete', lambda x=c: admin_delete_category(x, load), 'delete', 'danger')

    load()


def admin_edit_category(c, after):
    dialog, card = make_dialog(480)
    with card:
        ui.label('Edit Category').classes('text-xl font-bold')
        name = ui.input('Category name', value=c.get('category_name', '')).classes('w-full').props('outlined dense')
        desc = ui.input('Description', value=c.get('description') or '').classes('w-full').props('outlined dense')

        def save():
            nm = (name.value or '').strip()
            if not nm:
                notify_warning('Category name cannot be empty.')
                return
            if api_action(f"/api/admin/categories/{c['category_id']}", 'PUT',
                          {'user_id': user_id(), 'category_name': nm, 'description': (desc.value or '').strip()},
                          'Category updated successfully.'):
                dialog.close()
                after()

        with ui.row().classes('w-full justify-end gap-2'):
            secondary_button('Cancel', dialog.close)
            primary_button('Save Changes', save, 'save')
    dialog.open()


def admin_delete_category(c, after):
    confirm_dialog(
        'Delete Category?',
        f"Delete category '{c.get('category_name', 'Category')}'?",
        'Delete Category',
        lambda: api_action('/api/admin/categories', 'DELETE',
                           {'user_id': user_id(), 'category_id': c['category_id']},
                           'Category deleted successfully.'),
        after,
        note='A category used by a business cannot be deleted.',
    )


# =====================================================================
# ADMIN: REPORTS
# =====================================================================

def report_section(title, rows, key):
    with ui.card().classes('sc-card w-full'):
        ui.label(title).classes('text-lg font-bold')
        if not rows:
            ui.label('No data available.').classes('sc-muted')
            return
        top = max([int(r.get('total', 0) or 0) for r in rows] + [1])
        for r in rows:
            total = int(r.get('total', 0) or 0)
            label = str(r.get(key, 'Unknown'))
            if key != 'category_name':
                label = label.title()
            with ui.row().classes('w-full items-center no-wrap gap-3'):
                ui.label(label).classes('text-sm').style('min-width:160px;')
                ui.linear_progress(value=total / top, show_value=False).props(
                    'rounded size=10px color=primary track-color=pink-1').classes('flex-1')
                ui.label(str(total)).classes('font-bold').style('min-width:36px;text-align:right;')


def admin_reports_page():
    page_heading('Reports', 'Administrative reports for users, businesses, products and enquiries.')
    with ui.row().classes('gap-2'):
        back_bar()
        primary_button('Refresh Reports', refresh_view, 'refresh')

    status, data = api_request('/api/admin/reports' + user_query())
    if status != 200 or not isinstance(data, dict):
        notify_error(data)
        empty_state('Unable to load reports.', 'bar_chart')
        return

    with ui.row().classes('w-full gap-4'):
        stat_card('Total Users', data.get('total_users', 0), 'group')
        stat_card('Business Profiles', data.get('businesses', 0), 'storefront')
        stat_card('Products & Services', data.get('products_services', 0), 'inventory_2')
        stat_card('Total Enquiries', data.get('enquiries', 0), 'mail')

    report_section('Users by Role', data.get('users_by_role', []), 'role')
    report_section('Enquiries by Status', data.get('enquiries_by_status', []), 'status')
    report_section('Businesses by Category', data.get('businesses_by_category', []), 'category_name')


# =====================================================================
# START
# =====================================================================

if __name__ == '__main__':
    ui.run(
        title="SHECONNECT — Women's Business Hub",
        host='127.0.0.1',
        port=8080,
        reload=False,
        favicon='♀',
        storage_secret='sheconnect-pink-secret-key',
    )