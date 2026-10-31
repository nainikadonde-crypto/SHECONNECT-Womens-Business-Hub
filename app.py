from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

class Admin:
    """Admin domain class. Admins can view Entrepreneurs and Customers and manage platform data."""
    def __init__(self, user_id, name=None, email=None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = "admin"

    def can_manage_users(self):
        return True

    def can_view_entrepreneurs(self):
        return True

    def can_view_customers(self):
        return True


app = Flask(__name__)


def error_response(message="Unable to complete the request.", status=500):
    return jsonify({"error": message}), status


# ============================================================
# HOME / CONNECTION TEST
# ============================================================
@app.route("/")
def home():
    connection = None
    try:
        connection = get_db_connection()
        if connection.is_connected():
            return "SHECONNECT API — Flask and MySQL are running successfully."
        return "MySQL connection failed.", 500
    except Exception as error:
        print("HOME ERROR:", error)
        return "MySQL connection failed.", 500
    finally:
        if connection:
            connection.close()


# ============================================================
# REGISTER
# ============================================================
@app.route("/api/register", methods=["POST"])
def register():
    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        role = str(data.get("role", "customer")).strip().lower()

        if not name:
            return error_response("Name is required.", 400)
        if not email or "@" not in email:
            return error_response("Please enter a valid email address.", 400)
        if len(password) < 6:
            return error_response("Password must be at least 6 characters.", 400)
        if role not in ("customer", "entrepreneur", "admin"):
            return error_response("Invalid account type. Choose Customer, Entrepreneur, or Admin.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return error_response("An account with this email already exists.", 409)

        password_hash = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password_hash, role)
        )
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful.",
            "user_id": cursor.lastrowid,
            "name": name,
            "email": email,
            "role": role
        }), 201

    except Exception as error:
        if connection:
            connection.rollback()
        print("REGISTER ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# LOGIN
# ============================================================
@app.route("/api/login", methods=["POST"])
def login():
    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return error_response("Email and password are required.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, name, email, password, role FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            return error_response("Invalid email or password.", 401)

        stored_password = user.get("password") or ""
        valid = False

        try:
            valid = check_password_hash(stored_password, password)
        except (ValueError, TypeError):
            valid = stored_password == password

        if not valid:
            return error_response("Invalid email or password.", 401)

        # Upgrade an old plain-text password after successful login.
        if not stored_password.startswith(("scrypt:", "pbkdf2:")):
            cursor.execute(
                "UPDATE users SET password = %s WHERE user_id = %s",
                (generate_password_hash(password), user["user_id"])
            )
            connection.commit()

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "user": {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        })

    except Exception as error:
        if connection:
            connection.rollback()
        print("LOGIN ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# UPDATE USER ACCOUNT
# ============================================================
@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        current_password = str(data.get("current_password", ""))
        new_password = str(data.get("new_password", ""))

        if not name:
            return error_response("Name is required.", 400)
        if not email or "@" not in email:
            return error_response("Please enter a valid email address.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, name, email, password, role FROM users WHERE user_id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return error_response("User account not found.", 404)

        requested_user_id = data.get("request_user_id", user_id)
        try:
            requested_user_id = int(requested_user_id)
        except (TypeError, ValueError):
            return error_response("Invalid user account.", 400)

        if requested_user_id != user_id:
            return error_response("You can only update your own account.", 403)

        if email != user["email"]:
            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s AND user_id <> %s",
                (email, user_id)
            )
            if cursor.fetchone():
                return error_response("That email address is already in use.", 409)

        if new_password:
            if len(new_password) < 6:
                return error_response("New password must be at least 6 characters.", 400)
            if not current_password:
                return error_response("Enter your current password to change the password.", 400)

            stored_password = user.get("password") or ""
            try:
                password_valid = check_password_hash(stored_password, current_password)
            except (ValueError, TypeError):
                password_valid = stored_password == current_password

            if not password_valid:
                return error_response("Current password is incorrect.", 401)

            password_hash = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET name = %s, email = %s, password = %s WHERE user_id = %s",
                (name, email, password_hash, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET name = %s, email = %s WHERE user_id = %s",
                (name, email, user_id)
            )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Account information updated successfully.",
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": user["role"]
            }
        })

    except Exception as error:
        if connection:
            connection.rollback()
        print("UPDATE USER ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# DASHBOARD STATISTICS
# ============================================================
@app.route("/api/dashboard")
def dashboard():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM business_profiles")
        business_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]

        # Count only enquiries that belong to the currently logged-in user.
        # Customer: enquiries sent by that customer.
        # Entrepreneur: pending enquiries for that entrepreneur's businesses.
        # Admin/no user: all pending enquiries.
        user_id = request.args.get("user_id", type=int)

        if user_id:
            cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
            viewer = cursor.fetchone()

            if viewer and viewer[0] == "entrepreneur":
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM enquiries e
                    INNER JOIN business_profiles bp
                        ON e.business_id = bp.business_id
                    WHERE e.status = 'pending'
                      AND bp.user_id = %s
                """, (user_id,))
                enquiry_count = cursor.fetchone()[0]
            elif viewer and viewer[0] == "customer":
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM enquiries
                    WHERE status = 'pending'
                      AND customer_id = %s
                """, (user_id,))
                enquiry_count = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT COUNT(*) FROM enquiries WHERE status = 'pending'")
                enquiry_count = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM enquiries WHERE status = 'pending'")
            enquiry_count = cursor.fetchone()[0]

        return jsonify({
            "businesses": business_count,
            "products_services": product_count,
            "pending_enquiries": enquiry_count
        })

    except Exception as error:
        print("DASHBOARD ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# BUSINESSES
# ============================================================
@app.route("/api/businesses", methods=["GET", "POST"])
def businesses():
    if request.method == "GET":
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    bp.business_id,
                    bp.user_id,
                    bp.business_name,
                    bp.description,
                    bp.contact_number,
                    bp.address,
                    bp.website,
                    c.category_name
                FROM business_profiles bp
                INNER JOIN categories c ON bp.category_id = c.category_id
                ORDER BY bp.created_at DESC
            """)
            return jsonify(cursor.fetchall())
        except Exception as error:
            print("BUSINESS GET ERROR:", error)
            return error_response()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        category_id = data.get("category_id")
        business_name = str(data.get("business_name", "")).strip()
        description = str(data.get("description", "")).strip()
        contact_number = str(data.get("contact_number", "")).strip()
        address = str(data.get("address", "")).strip()
        website = str(data.get("website", "")).strip()

        if not user_id or not category_id or not business_name:
            return error_response("Business name, owner and category are required.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user or user["role"] != "entrepreneur":
            return error_response("Only entrepreneur accounts can add businesses.", 403)

        cursor.execute(
            "SELECT category_id FROM categories WHERE category_id = %s",
            (category_id,)
        )
        if not cursor.fetchone():
            return error_response("Selected category does not exist.", 400)

        cursor.execute("""
            INSERT INTO business_profiles
            (user_id, category_id, business_name, description,
             contact_number, address, website)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            category_id,
            business_name,
            description,
            contact_number,
            address,
            website
        ))

        connection.commit()
        return jsonify({
            "success": True,
            "business_id": cursor.lastrowid
        }), 201

    except Exception as error:
        if connection:
            connection.rollback()
        print("BUSINESS POST ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/api/businesses/search")
def search_businesses():
    search = request.args.get("q", "").strip()
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        value = f"%{search}%"

        cursor.execute("""
            SELECT
                bp.business_id,
                bp.user_id,
                bp.business_name,
                bp.description,
                bp.contact_number,
                bp.address,
                bp.website,
                c.category_name
            FROM business_profiles bp
            INNER JOIN categories c ON bp.category_id = c.category_id
            WHERE bp.business_name LIKE %s
               OR bp.description LIKE %s
               OR c.category_name LIKE %s
               OR bp.address LIKE %s
            ORDER BY bp.business_name
        """, (value, value, value, value))

        return jsonify(cursor.fetchall())

    except Exception as error:
        print("BUSINESS SEARCH ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/api/users/<int:user_id>/businesses")
def user_businesses(user_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT business_id, business_name
            FROM business_profiles
            WHERE user_id = %s
            ORDER BY business_name
        """, (user_id,))
        return jsonify(cursor.fetchall())
    except Exception as error:
        print("USER BUSINESS ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/api/businesses/<int:business_id>/products")
def business_products(business_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                product_id,
                business_id,
                product_name,
                description,
                price,
                product_type
            FROM products
            WHERE business_id = %s
            ORDER BY created_at DESC
        """, (business_id,))

        products = cursor.fetchall()
        for product in products:
            if product["price"] is not None:
                product["price"] = float(product["price"])

        return jsonify(products)

    except Exception as error:
        print("BUSINESS PRODUCTS ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# CATEGORIES
# ============================================================
@app.route("/api/categories")
def get_categories():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT category_id, category_name, description
            FROM categories
            ORDER BY category_name
        """)
        return jsonify(cursor.fetchall())
    except Exception as error:
        print("CATEGORY ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# PRODUCTS / SERVICES
# ============================================================
@app.route("/api/products", methods=["GET", "POST"])
def products():
    if request.method == "GET":
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    p.product_id,
                    p.business_id,
                    p.product_name,
                    p.description,
                    p.price,
                    p.product_type,
                    bp.business_name
                FROM products p
                INNER JOIN business_profiles bp
                    ON p.business_id = bp.business_id
                ORDER BY p.created_at DESC
            """)

            rows = cursor.fetchall()
            for row in rows:
                if row["price"] is not None:
                    row["price"] = float(row["price"])

            return jsonify(rows)

        except Exception as error:
            print("PRODUCT GET ERROR:", error)
            return error_response()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        business_id = data.get("business_id")
        name = str(data.get("product_name", "")).strip()
        description = str(data.get("description", "")).strip()
        product_type = str(data.get("product_type", "service")).strip().lower()
        raw_price = data.get("price")

        if not business_id or not name:
            return error_response("Business and product/service name are required.", 400)

        if product_type not in ("product", "service"):
            return error_response("Invalid product type.", 400)

        price = None
        if raw_price not in (None, ""):
            try:
                price = float(raw_price)
                if price < 0:
                    raise ValueError
            except (TypeError, ValueError):
                return error_response(
                    "Price must be a valid non-negative number.",
                    400
                )

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id FROM business_profiles WHERE business_id = %s",
            (business_id,)
        )
        business = cursor.fetchone()

        if not business:
            return error_response("Business not found.", 404)

        cursor.execute(
            "SELECT role FROM users WHERE user_id = %s",
            (business["user_id"],)
        )
        owner = cursor.fetchone()

        if not owner or owner["role"] != "entrepreneur":
            return error_response("Only entrepreneur businesses can have listings.", 403)

        cursor.execute("""
            INSERT INTO products
            (business_id, product_name, description, price, product_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (business_id, name, description, price, product_type))

        connection.commit()

        return jsonify({
            "success": True,
            "product_id": cursor.lastrowid
        }), 201

    except Exception as error:
        if connection:
            connection.rollback()
        print("PRODUCT POST ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/api/products/search")
def search_products():
    search = request.args.get("q", "").strip()
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        value = f"%{search}%"

        cursor.execute("""
            SELECT
                p.product_id,
                p.business_id,
                p.product_name,
                p.description,
                p.price,
                p.product_type,
                bp.business_name
            FROM products p
            INNER JOIN business_profiles bp
                ON p.business_id = bp.business_id
            WHERE p.product_name LIKE %s
               OR p.description LIKE %s
               OR p.product_type LIKE %s
               OR bp.business_name LIKE %s
            ORDER BY p.product_name
        """, (value, value, value, value))

        rows = cursor.fetchall()
        for row in rows:
            if row["price"] is not None:
                row["price"] = float(row["price"])

        return jsonify(rows)

    except Exception as error:
        print("PRODUCT SEARCH ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# ENQUIRIES
# ============================================================
@app.route("/api/enquiries", methods=["GET", "POST"])
def enquiries():
    # --------------------------------------------------------
    # GET ENQUIRIES
    # --------------------------------------------------------
    if request.method == "GET":
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            user_id = request.args.get("user_id", type=int)

            if user_id:
                cursor.execute(
                    "SELECT role FROM users WHERE user_id = %s",
                    (user_id,)
                )
                viewer = cursor.fetchone()

                if not viewer:
                    return error_response("User not found.", 404)

                if viewer["role"] == "entrepreneur":
                    cursor.execute("""
                        SELECT
                            e.enquiry_id,
                            e.customer_id,
                            e.business_id,
                            e.subject,
                            e.message,
                            e.status,
                            e.reply_message,
                            e.replied_at,
                            e.created_at,
                            u.name AS customer_name,
                            bp.business_name
                        FROM enquiries e
                        INNER JOIN users u
                            ON e.customer_id = u.user_id
                        INNER JOIN business_profiles bp
                            ON e.business_id = bp.business_id
                        WHERE bp.user_id = %s
                        ORDER BY e.created_at DESC
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT
                            e.enquiry_id,
                            e.customer_id,
                            e.business_id,
                            e.subject,
                            e.message,
                            e.status,
                            e.reply_message,
                            e.replied_at,
                            e.created_at,
                            u.name AS customer_name,
                            bp.business_name
                        FROM enquiries e
                        INNER JOIN users u
                            ON e.customer_id = u.user_id
                        INNER JOIN business_profiles bp
                            ON e.business_id = bp.business_id
                        WHERE e.customer_id = %s
                        ORDER BY e.created_at DESC
                    """, (user_id,))
            else:
                cursor.execute("""
                    SELECT
                        e.enquiry_id,
                        e.customer_id,
                        e.business_id,
                        e.subject,
                        e.message,
                        e.status,
                        e.reply_message,
                        e.replied_at,
                        e.created_at,
                        u.name AS customer_name,
                        bp.business_name
                    FROM enquiries e
                    INNER JOIN users u
                        ON e.customer_id = u.user_id
                    INNER JOIN business_profiles bp
                        ON e.business_id = bp.business_id
                    ORDER BY e.created_at DESC
                """)

            rows = cursor.fetchall()

            for row in rows:
                if row["created_at"]:
                    row["created_at"] = row["created_at"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                if row.get("replied_at"):
                    row["replied_at"] = row["replied_at"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

            return jsonify(rows)

        except Exception as error:
            print("ENQUIRY GET ERROR:", error)
            return error_response()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # --------------------------------------------------------
    # POST NEW ENQUIRY
    # --------------------------------------------------------
    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        customer_id = data.get("customer_id")
        business_id = data.get("business_id")
        subject = str(data.get("subject", "")).strip()
        message = str(data.get("message", "")).strip()

        if not customer_id or not business_id or not subject or not message:
            return error_response(
                "Customer, business, subject and message are required.",
                400
            )

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT role FROM users WHERE user_id = %s",
            (customer_id,)
        )
        customer = cursor.fetchone()

        if not customer or customer["role"] != "customer":
            return error_response("Only customer accounts can send enquiries.", 403)

        cursor.execute(
            "SELECT business_id FROM business_profiles WHERE business_id = %s",
            (business_id,)
        )
        if not cursor.fetchone():
            return error_response("Business not found.", 404)

        cursor.execute("""
            INSERT INTO enquiries
            (customer_id, business_id, subject, message)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, business_id, subject, message))

        connection.commit()

        return jsonify({
            "success": True,
            "enquiry_id": cursor.lastrowid,
            "message": "Enquiry sent successfully."
        }), 201

    except Exception as error:
        if connection:
            connection.rollback()
        print("ENQUIRY POST ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# OWNER BUSINESS MANAGEMENT
# ============================================================
@app.route("/api/users/<int:user_id>/businesses/full")
def user_businesses_full(user_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                bp.business_id,
                bp.user_id,
                bp.category_id,
                bp.business_name,
                bp.description,
                bp.contact_number,
                bp.address,
                bp.website,
                c.category_name
            FROM business_profiles bp
            INNER JOIN categories c
                ON bp.category_id = c.category_id
            WHERE bp.user_id = %s
            ORDER BY bp.created_at DESC
        """, (user_id,))
        return jsonify(cursor.fetchall())
    except Exception as error:
        print("OWNER BUSINESS ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/api/businesses/<int:business_id>", methods=["PUT", "DELETE"])
def manage_business(business_id):
    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")

        if not user_id:
            return error_response("User information is required.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id FROM business_profiles WHERE business_id = %s",
            (business_id,)
        )
        business = cursor.fetchone()

        if not business:
            return error_response("Business not found.", 404)

        if int(business["user_id"]) != int(user_id):
            return error_response("You can manage only your own business.", 403)

        if request.method == "DELETE":
            cursor.execute(
                "DELETE FROM business_profiles WHERE business_id = %s",
                (business_id,)
            )
            connection.commit()
            return jsonify({
                "success": True,
                "message": "Business deleted successfully."
            })

        name = str(data.get("business_name", "")).strip()
        description = str(data.get("description", "")).strip()
        contact = str(data.get("contact_number", "")).strip()
        address = str(data.get("address", "")).strip()
        category_id = data.get("category_id")
        website = str(data.get("website", "")).strip()

        if not name or not category_id:
            return error_response(
                "Business name and category are required.",
                400
            )

        cursor.execute(
            "SELECT category_id FROM categories WHERE category_id = %s",
            (category_id,)
        )
        if not cursor.fetchone():
            return error_response("Selected category does not exist.", 400)

        cursor.execute("""
            UPDATE business_profiles
            SET
                category_id = %s,
                business_name = %s,
                description = %s,
                contact_number = %s,
                address = %s,
                website = %s
            WHERE business_id = %s
        """, (
            category_id,
            name,
            description,
            contact,
            address,
            website,
            business_id
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Business updated successfully."
        })

    except Exception as error:
        if connection:
            connection.rollback()
        print("BUSINESS MANAGEMENT ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# OWNER PRODUCT / SERVICE MANAGEMENT
# ============================================================
@app.route("/api/users/<int:user_id>/products")
def user_products(user_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                p.product_id,
                p.business_id,
                p.product_name,
                p.description,
                p.price,
                p.product_type,
                bp.business_name
            FROM products p
            INNER JOIN business_profiles bp
                ON p.business_id = bp.business_id
            WHERE bp.user_id = %s
            ORDER BY p.created_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        for row in rows:
            if row["price"] is not None:
                row["price"] = float(row["price"])

        return jsonify(rows)

    except Exception as error:
        print("OWNER PRODUCT ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/api/products/<int:product_id>", methods=["PUT", "DELETE"])
def manage_product(product_id):
    connection = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")

        if not user_id:
            return error_response("User information is required.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.product_id,
                bp.user_id
            FROM products p
            INNER JOIN business_profiles bp
                ON p.business_id = bp.business_id
            WHERE p.product_id = %s
        """, (product_id,))

        item = cursor.fetchone()

        if not item:
            return error_response("Product/service not found.", 404)

        if int(item["user_id"]) != int(user_id):
            return error_response("You can manage only your own listings.", 403)

        if request.method == "DELETE":
            cursor.execute(
                "DELETE FROM products WHERE product_id = %s",
                (product_id,)
            )
            connection.commit()
            return jsonify({
                "success": True,
                "message": "Listing deleted successfully."
            })

        name = str(data.get("product_name", "")).strip()
        description = str(data.get("description", "")).strip()
        product_type = str(data.get("product_type", "service")).strip().lower()
        raw_price = data.get("price")

        if not name:
            return error_response("Product/service name is required.", 400)

        if product_type not in ("product", "service"):
            return error_response("Invalid listing type.", 400)

        price = None
        if raw_price not in (None, ""):
            try:
                price = float(raw_price)
                if price < 0:
                    raise ValueError
            except (TypeError, ValueError):
                return error_response(
                    "Price must be a valid non-negative number.",
                    400
                )

        cursor.execute("""
            UPDATE products
            SET
                product_name = %s,
                description = %s,
                price = %s,
                product_type = %s
            WHERE product_id = %s
        """, (name, description, price, product_type, product_id))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Listing updated successfully."
        })

    except Exception as error:
        if connection:
            connection.rollback()
        print("PRODUCT MANAGEMENT ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# DELETE ENQUIRY
# ============================================================
@app.route("/api/enquiries/<int:enquiry_id>", methods=["DELETE"])
def delete_enquiry(enquiry_id):
    connection = None
    cursor = None

    try:
        # The Tkinter client sends user_id in the query string.
        user_id = request.args.get("user_id", type=int)

        # Also accept JSON user_id for compatibility.
        if not user_id:
            data = request.get_json(silent=True) or {}
            user_id = data.get("user_id")

        if not user_id:
            return error_response("User information is required.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Find the enquiry and the entrepreneur who owns its business.
        cursor.execute("""
            SELECT
                e.enquiry_id,
                e.customer_id,
                bp.user_id AS business_owner_id
            FROM enquiries e
            INNER JOIN business_profiles bp
                ON e.business_id = bp.business_id
            WHERE e.enquiry_id = %s
        """, (enquiry_id,))

        enquiry = cursor.fetchone()

        if not enquiry:
            return error_response("Enquiry not found.", 404)

        # A customer can delete their own enquiry.
        # An entrepreneur can delete an enquiry belonging to their business.
        allowed = (
            int(enquiry["customer_id"]) == int(user_id)
            or int(enquiry["business_owner_id"]) == int(user_id)
        )

        if not allowed:
            return error_response(
                "You are not allowed to delete this enquiry.",
                403
            )

        cursor.execute(
            "DELETE FROM enquiries WHERE enquiry_id = %s",
            (enquiry_id,)
        )
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Enquiry deleted successfully."
        })

    except Exception as error:
        if connection:
            connection.rollback()
        print("ENQUIRY DELETE ERROR:", error)
        return error_response()

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# ============================================================
# UPDATE ENQUIRY / REPLY TO CUSTOMER
# ============================================================
@app.route("/api/enquiries/<int:enquiry_id>", methods=["PUT"])
def update_enquiry(enquiry_id):
    connection = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}

        user_id = data.get("user_id")
        status_value = str(data.get("status", "")).strip().lower()
        reply_message = str(data.get("reply_message", "")).strip()

        if not user_id:
            return error_response("User information is required.", 400)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # CUSTOMER EDITS OWN ENQUIRY
        # ----------------------------------------------------
        if str(data.get("action", "")).lower() == "edit":
            new_subject = str(data.get("subject", "")).strip()
            new_message = str(data.get("message", "")).strip()

            if not new_subject or not new_message:
                return error_response("Subject and message are required.", 400)

            cursor.execute(
                "SELECT customer_id FROM enquiries WHERE enquiry_id = %s",
                (enquiry_id,)
            )
            row = cursor.fetchone()

            if not row:
                return error_response("Enquiry not found.", 404)

            if int(row["customer_id"]) != int(user_id):
                return error_response("You can edit only your own enquiries.", 403)

            cursor.execute("""
                UPDATE enquiries
                SET subject = %s,
                    message = %s,
                    status = 'pending',
                    reply_message = NULL,
                    replied_at = NULL
                WHERE enquiry_id = %s
            """, (new_subject, new_message, enquiry_id))

            connection.commit()

            return jsonify({
                "success": True,
                "message": "Enquiry updated successfully."
            })

        # ----------------------------------------------------
        # ENTREPRENEUR REPLY / CLOSE
        # ----------------------------------------------------
        if status_value not in ("pending", "replied", "closed"):
            return error_response("Invalid enquiry status.", 400)

        # Find the enquiry and the entrepreneur who owns its business.
        cursor.execute("""
            SELECT
                e.enquiry_id,
                e.customer_id,
                e.business_id,
                e.subject,
                e.message,
                e.status,
                bp.user_id AS business_owner_id
            FROM enquiries e
            INNER JOIN business_profiles bp
                ON e.business_id = bp.business_id
            WHERE e.enquiry_id = %s
        """, (enquiry_id,))

        enquiry = cursor.fetchone()

        if not enquiry:
            return error_response("Enquiry not found.", 404)

        # The person updating the enquiry must be the business owner.
        if int(enquiry["business_owner_id"]) != int(user_id):
            return error_response(
                "You can update enquiries for your own business only.",
                403
            )

        # Confirm that the owner is actually an entrepreneur.
        cursor.execute(
            "SELECT role FROM users WHERE user_id = %s",
            (user_id,)
        )
        owner = cursor.fetchone()

        if not owner or owner["role"] != "entrepreneur":
            return error_response(
                "Only entrepreneur accounts can reply to enquiries.",
                403
            )
        # ----------------------------------------------------
        # REPLY TO CUSTOMER
        # ----------------------------------------------------
        if status_value == "replied":
            if not reply_message:
                return error_response(
                    "Please enter a reply message.",
                    400
                )

            cursor.execute("""
                UPDATE enquiries
                SET
                    status = 'replied',
                    reply_message = %s,
                    replied_at = CURRENT_TIMESTAMP
                WHERE enquiry_id = %s
            """, (reply_message, enquiry_id))

            connection.commit()

            return jsonify({
                "success": True,
                "message": "Reply sent to the customer successfully."
            })

        # ----------------------------------------------------
        # CLOSE ENQUIRY
        # ----------------------------------------------------
        if status_value == "closed":
            cursor.execute("""
                UPDATE enquiries
                SET status = 'closed'
                WHERE enquiry_id = %s
            """, (enquiry_id,))

            connection.commit()

            return jsonify({
                "success": True,
                "message": "Enquiry closed successfully."
            })

        # ----------------------------------------------------
        # OTHER STATUS
        # ----------------------------------------------------
        cursor.execute("""
            UPDATE enquiries
            SET status = %s
            WHERE enquiry_id = %s
        """, (status_value, enquiry_id))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Enquiry status updated successfully."
        })

    except Exception as error:
        if connection:
            connection.rollback()
        print("ENQUIRY UPDATE ERROR:", error)
        return error_response()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



# ============================================================
# ADMIN APIs
# ============================================================
def require_admin(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT user_id, name, email, role FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close(); connection.close()
    return user if user and user["role"] == "admin" else None

@app.route("/api/admin/stats")
def admin_stats():
    user_id = request.args.get("user_id", type=int)
    if not user_id or not require_admin(user_id):
        return error_response("Admin access required.", 403)
    connection = None; cursor = None
    try:
        connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()["total_users"]
        cursor.execute("SELECT COUNT(*) AS entrepreneurs FROM users WHERE role='entrepreneur'")
        entrepreneurs = cursor.fetchone()["entrepreneurs"]
        cursor.execute("SELECT COUNT(*) AS customers FROM users WHERE role='customer'")
        customers = cursor.fetchone()["customers"]
        cursor.execute("SELECT COUNT(*) AS businesses FROM business_profiles")
        businesses = cursor.fetchone()["businesses"]
        cursor.execute("SELECT COUNT(*) AS products_services FROM products")
        products_services = cursor.fetchone()["products_services"]
        cursor.execute("SELECT COUNT(*) AS enquiries FROM enquiries")
        enquiries = cursor.fetchone()["enquiries"]
        cursor.execute("SELECT COUNT(*) AS pending_enquiries FROM enquiries WHERE status='pending'")
        pending = cursor.fetchone()["pending_enquiries"]
        return jsonify({"total_users": total_users, "entrepreneurs": entrepreneurs, "customers": customers, "businesses": businesses, "products_services": products_services, "enquiries": enquiries, "pending_enquiries": pending})
    except Exception as error:
        print("ADMIN STATS ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/users")
def admin_users():
    user_id = request.args.get("user_id", type=int)
    if not user_id or not require_admin(user_id): return error_response("Admin access required.", 403)
    connection=None; cursor=None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute("SELECT user_id, name, email, role, created_at FROM users ORDER BY created_at DESC")
        rows=cursor.fetchall()
        for row in rows:
            if row.get("created_at"): row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(rows)
    except Exception as error:
        print("ADMIN USERS ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/users/<int:target_user_id>", methods=["DELETE"])
def admin_delete_user(target_user_id):
    admin_id = request.args.get("user_id", type=int)
    if not admin_id or not require_admin(admin_id):
        return error_response("Admin access required.", 403)
    if admin_id == target_user_id:
        return error_response("You cannot delete your own administrator account.", 400)
    connection = None; cursor = None
    try:
        connection = get_db_connection(); cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (target_user_id,))
        if not cursor.fetchone():
            return error_response("User not found.", 404)
        cursor.execute("DELETE FROM users WHERE user_id=%s", (target_user_id,))
        connection.commit()
        return jsonify({"success": True, "message": "User deleted successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN DELETE USER ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/businesses")
def admin_businesses():
    user_id = request.args.get("user_id", type=int)
    if not user_id or not require_admin(user_id): return error_response("Admin access required.", 403)
    connection=None; cursor=None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute("""SELECT bp.business_id, bp.business_name, bp.description, bp.contact_number, bp.address, bp.website, c.category_name, u.name AS owner_name, u.email AS owner_email FROM business_profiles bp INNER JOIN users u ON bp.user_id=u.user_id INNER JOIN categories c ON bp.category_id=c.category_id ORDER BY bp.created_at DESC""")
        return jsonify(cursor.fetchall())
    except Exception as error:
        print("ADMIN BUSINESSES ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/businesses/<int:business_id>", methods=["DELETE"])
def admin_delete_business(business_id):
    data = request.get_json(silent=True) or {}
    admin_id = data.get("user_id") or request.args.get("user_id", type=int)
    if not admin_id or not require_admin(int(admin_id)):
        return error_response("Admin access required.", 403)
    connection = None; cursor = None
    try:
        connection = get_db_connection(); cursor = connection.cursor()
        cursor.execute("SELECT business_id FROM business_profiles WHERE business_id=%s", (business_id,))
        if not cursor.fetchone():
            return error_response("Business not found.", 404)
        cursor.execute("DELETE FROM business_profiles WHERE business_id=%s", (business_id,))
        connection.commit()
        return jsonify({"success": True, "message": "Business deleted successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN DELETE BUSINESS ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/categories", methods=["POST", "DELETE"])
def admin_categories():
    data=request.get_json(silent=True) or {}
    user_id=data.get("user_id")
    if not user_id or not require_admin(int(user_id)): return error_response("Admin access required.",403)
    connection=None; cursor=None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        if request.method=="POST":
            name=str(data.get("category_name","")).strip(); description=str(data.get("description","")).strip()
            if not name: return error_response("Category name is required.",400)
            cursor.execute("INSERT INTO categories (category_name, description) VALUES (%s,%s)",(name,description)); connection.commit()
            return jsonify({"success":True,"message":"Category added successfully.","category_id":cursor.lastrowid}),201
        category_id=data.get("category_id")
        if not category_id: return error_response("Category ID is required.",400)
        cursor.execute("SELECT COUNT(*) AS total FROM business_profiles WHERE category_id=%s",(category_id,))
        if cursor.fetchone()["total"]>0: return error_response("This category is used by a business and cannot be deleted.",409)
        cursor.execute("DELETE FROM categories WHERE category_id=%s",(category_id,)); connection.commit()
        return jsonify({"success":True,"message":"Category deleted successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN CATEGORY ERROR:",error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/reports")
def admin_reports():
    user_id = request.args.get("user_id", type=int)
    if not user_id or not require_admin(user_id):
        return error_response("Admin access required.", 403)
    connection = None; cursor = None
    try:
        connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
        reports = {}
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        reports["total_users"] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM business_profiles")
        reports["businesses"] = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM enquiries")
        reports["enquiries"] = cursor.fetchone()["total"]
        cursor.execute("SELECT role, COUNT(*) AS total FROM users GROUP BY role")
        reports["users_by_role"] = cursor.fetchall()
        cursor.execute("SELECT status, COUNT(*) AS total FROM enquiries GROUP BY status")
        reports["enquiries_by_status"] = cursor.fetchall()
        cursor.execute("SELECT c.category_name, COUNT(bp.business_id) AS total FROM categories c LEFT JOIN business_profiles bp ON c.category_id=bp.category_id GROUP BY c.category_id, c.category_name ORDER BY total DESC, c.category_name")
        reports["businesses_by_category"] = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) AS total FROM products")
        reports["products_services"] = cursor.fetchone()["total"]
        return jsonify(reports)
    except Exception as error:
        print("ADMIN REPORTS ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/enquiries")
def admin_enquiries():
    user_id=request.args.get("user_id",type=int)
    if not user_id or not require_admin(user_id): return error_response("Admin access required.",403)
    connection=None; cursor=None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute("""SELECT e.enquiry_id,e.subject,e.message,e.status,e.reply_message,e.created_at,u.name AS customer_name,bp.business_name FROM enquiries e INNER JOIN users u ON e.customer_id=u.user_id INNER JOIN business_profiles bp ON e.business_id=bp.business_id ORDER BY e.created_at DESC""")
        rows=cursor.fetchall()
        for row in rows:
            if row.get("created_at"): row["created_at"]=row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(rows)
    except Exception as error:
        print("ADMIN ENQUIRIES ERROR:",error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()



# ============================================================
# COMPLETE ADMIN MANAGEMENT APIs
# ============================================================
@app.route("/api/admin/users/<int:target_user_id>", methods=["PUT"])
def admin_update_user(target_user_id):
    data = request.get_json(silent=True) or {}
    admin_id = data.get("user_id")
    if not admin_id or not require_admin(int(admin_id)):
        return error_response("Admin access required.", 403)
    if int(admin_id) == target_user_id:
        return error_response("You cannot change your own administrator role here.", 400)
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    role = str(data.get("role", "")).strip().lower()
    if not name or not email or "@" not in email:
        return error_response("Name and a valid email are required.", 400)
    if role not in ("customer", "entrepreneur", "admin"):
        return error_response("Invalid role.", 400)
    connection = cursor = None
    try:
        connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (target_user_id,))
        if not cursor.fetchone(): return error_response("User not found.", 404)
        cursor.execute("SELECT user_id FROM users WHERE email=%s AND user_id<>%s", (email, target_user_id))
        if cursor.fetchone(): return error_response("That email is already in use.", 409)
        cursor.execute("UPDATE users SET name=%s, email=%s, role=%s WHERE user_id=%s", (name, email, role, target_user_id))
        connection.commit()
        return jsonify({"success": True, "message": "User updated successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN UPDATE USER ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/businesses/<int:business_id>", methods=["PUT"])
def admin_update_business(business_id):
    data = request.get_json(silent=True) or {}
    admin_id = data.get("user_id")
    if not admin_id or not require_admin(int(admin_id)):
        return error_response("Admin access required.", 403)
    name = str(data.get("business_name", "")).strip()
    description = str(data.get("description", "")).strip()
    contact = str(data.get("contact_number", "")).strip()
    address = str(data.get("address", "")).strip()
    website = str(data.get("website", "")).strip()
    category_id = data.get("category_id")
    if not name: return error_response("Business name is required.", 400)
    if not category_id: return error_response("Category is required.", 400)
    connection = cursor = None
    try:
        connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT business_id FROM business_profiles WHERE business_id=%s", (business_id,))
        if not cursor.fetchone(): return error_response("Business not found.", 404)
        cursor.execute("SELECT category_id FROM categories WHERE category_id=%s", (category_id,))
        if not cursor.fetchone(): return error_response("Category not found.", 404)
        cursor.execute("""UPDATE business_profiles SET business_name=%s, description=%s, contact_number=%s, address=%s, website=%s, category_id=%s WHERE business_id=%s""", (name,description,contact,address,website,category_id,business_id))
        connection.commit()
        return jsonify({"success": True, "message": "Business updated successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN UPDATE BUSINESS ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/products")
def admin_products():
    admin_id = request.args.get("user_id", type=int)
    if not admin_id or not require_admin(admin_id): return error_response("Admin access required.", 403)
    connection = cursor = None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute("""SELECT p.product_id,p.business_id,p.product_name,p.description,p.price,p.product_type,p.created_at,bp.business_name,u.name AS owner_name FROM products p INNER JOIN business_profiles bp ON p.business_id=bp.business_id INNER JOIN users u ON bp.user_id=u.user_id ORDER BY p.created_at DESC, p.product_id DESC""")
        rows=cursor.fetchall()
        for row in rows:
            if row.get("price") is not None: row["price"]=float(row["price"])
            if row.get("created_at"): row["created_at"]=row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(rows)
    except Exception as error:
        print("ADMIN PRODUCTS ERROR:", error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/products/<int:product_id>", methods=["PUT","DELETE"])
def admin_manage_product(product_id):
    data=request.get_json(silent=True) or {}
    admin_id=data.get("user_id") or request.args.get("user_id", type=int)
    if not admin_id or not require_admin(int(admin_id)): return error_response("Admin access required.",403)
    connection=cursor=None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute("SELECT product_id FROM products WHERE product_id=%s",(product_id,))
        if not cursor.fetchone(): return error_response("Product/service not found.",404)
        if request.method=="DELETE":
            cursor.execute("DELETE FROM products WHERE product_id=%s",(product_id,)); connection.commit()
            return jsonify({"success":True,"message":"Product/service deleted successfully."})
        name=str(data.get("product_name","")).strip(); description=str(data.get("description","")).strip(); ptype=str(data.get("product_type","service")).strip().lower(); raw=data.get("price")
        if not name: return error_response("Product/service name is required.",400)
        if ptype not in ("product","service"): return error_response("Invalid listing type.",400)
        price=None
        if raw not in (None,""):
            try: price=float(raw); assert price>=0
            except Exception: return error_response("Price must be a valid non-negative number.",400)
        cursor.execute("UPDATE products SET product_name=%s,description=%s,price=%s,product_type=%s WHERE product_id=%s",(name,description,price,ptype,product_id)); connection.commit()
        return jsonify({"success":True,"message":"Product/service updated successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN PRODUCT MANAGEMENT ERROR:",error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/categories/<int:category_id>", methods=["PUT"])
def admin_update_category(category_id):
    data=request.get_json(silent=True) or {}
    admin_id=data.get("user_id")
    if not admin_id or not require_admin(int(admin_id)): return error_response("Admin access required.",403)
    name=str(data.get("category_name","")).strip(); description=str(data.get("description","")).strip()
    if not name: return error_response("Category name is required.",400)
    connection=cursor=None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute("SELECT category_id FROM categories WHERE category_id=%s",(category_id,))
        if not cursor.fetchone(): return error_response("Category not found.",404)
        cursor.execute("SELECT category_id FROM categories WHERE category_name=%s AND category_id<>%s",(name,category_id))
        if cursor.fetchone(): return error_response("A category with this name already exists.",409)
        cursor.execute("UPDATE categories SET category_name=%s,description=%s WHERE category_id=%s",(name,description,category_id)); connection.commit()
        return jsonify({"success":True,"message":"Category updated successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN UPDATE CATEGORY ERROR:",error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route("/api/admin/enquiries/<int:enquiry_id>", methods=["PUT","DELETE"])
def admin_manage_enquiry(enquiry_id):
    data=request.get_json(silent=True) or {}
    admin_id=data.get("user_id") or request.args.get("user_id", type=int)
    if not admin_id or not require_admin(int(admin_id)): return error_response("Admin access required.",403)
    connection=cursor=None
    try:
        connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute("SELECT enquiry_id FROM enquiries WHERE enquiry_id=%s",(enquiry_id,))
        if not cursor.fetchone(): return error_response("Enquiry not found.",404)
        if request.method=="DELETE":
            cursor.execute("DELETE FROM enquiries WHERE enquiry_id=%s",(enquiry_id,)); connection.commit()
            return jsonify({"success":True,"message":"Enquiry deleted successfully."})
        status_value=str(data.get("status","pending")).strip().lower()
        reply=str(data.get("reply_message","")).strip()
        if status_value not in ("pending","replied","closed"): return error_response("Invalid enquiry status.",400)
        if status_value=="replied" and not reply: return error_response("Reply message is required.",400)
        if status_value=="replied":
            cursor.execute("UPDATE enquiries SET status='replied',reply_message=%s,replied_at=CURRENT_TIMESTAMP WHERE enquiry_id=%s",(reply,enquiry_id))
        elif status_value=="closed":
            cursor.execute("UPDATE enquiries SET status='closed' WHERE enquiry_id=%s",(enquiry_id,))
        else:
            cursor.execute("UPDATE enquiries SET status='pending',reply_message=NULL,replied_at=NULL WHERE enquiry_id=%s",(enquiry_id,))
        connection.commit(); return jsonify({"success":True,"message":"Enquiry updated successfully."})
    except Exception as error:
        if connection: connection.rollback()
        print("ADMIN ENQUIRY MANAGEMENT ERROR:",error); return error_response()
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


# ============================================================
# RUN APPLICATION
# ============================================================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
