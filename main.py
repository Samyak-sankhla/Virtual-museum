
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from config import settings
from db import get_conn, fetch_all, fetch_one, execute
import os
from datetime import datetime

bp = Blueprint("main", __name__)

# -----------------------------
# Helpers
# -----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS

def save_image(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        flash("Unsupported image type.", "warning")
        return None
    filename = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(file_storage.filename)
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    dst = os.path.join(settings.UPLOAD_FOLDER, filename)
    file_storage.save(dst)
    # store relative path from /static
    return f"uploads/{filename}"

# -----------------------------
# Routes
# -----------------------------
@bp.get("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("auth.login_form"))
    return redirect(url_for("main.dashboard"))

@bp.get("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("auth.login_form"))
    role = session["role"]
    if role == "Admin":
        return admin_dashboard()
    elif role == "Artist":
        return artist_dashboard()
    else:
        return customer_dashboard()

# -----------------------------
# Admin Dashboard & Transactions
# -----------------------------
def admin_dashboard():
    with get_conn("Admin") as conn:
        artifacts = fetch_all(conn, """
            SELECT a.Artifact_ID, a.Title, a.Price, a.Type, a.Image, a.Quantity,
                   IFNULL(CONCAT(u.Fname,' ',u.Lname),'—') AS Artist_Name,
                   IFNULL(m.Name,'—') AS Museum_Name
            FROM Artifact a
            LEFT JOIN User u ON a.Artist_ID = u.User_ID
            LEFT JOIN Museum m ON a.M_ID = m.M_ID
            ORDER BY a.Created_At DESC
        """)
    return render_template("dash_admin.html", artifacts=artifacts)

@bp.get("/admin/transactions")
def admin_transactions():
    if session.get("role") != "Admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))
    with get_conn("Admin") as conn:
        tx = fetch_all(conn, "SELECT * FROM AdminTransactionRecords ORDER BY Purchase_Date DESC")
    return render_template("admin_transactions.html", transactions=tx)

# -----------------------------
# Artist Dashboard, Upload, Delete
# -----------------------------
def artist_dashboard():
    artist_id = session.get("user_id")
    search = request.args.get("search", "").strip()
    filter_type = request.args.get("filter_type", "").strip()

    params = {"aid": artist_id}
    sql = "SELECT * FROM Artifact WHERE Artist_ID = :aid"
    if search:
        sql += " AND Title LIKE :q"
        params["q"] = f"%{search}%"
    if filter_type:
        sql += " AND Type = :t"
        params["t"] = filter_type
    sql += " ORDER BY Created_At DESC"

    with get_conn("Artist") as conn:
        artifacts = fetch_all(conn, sql, params)
        types = [r["Type"] for r in fetch_all(conn, "SELECT DISTINCT Type FROM Artifact")]
        museums = fetch_all(conn, "SELECT M_ID, Name FROM Museum ORDER BY Name")

    return render_template(
        "dash_artist.html",
        artifacts=artifacts,
        types=types,
        museums=museums,  
    )

@bp.route("/upload_artifact", methods=["GET","POST"])
def upload_artifact():
    if session.get("role") != "Artist":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        title = request.form.get("title","").strip()
        description = request.form.get("description","").strip()
        type_ = request.form.get("type","Other")
        price = request.form.get("price") or 0
        quantity = request.form.get("quantity") or 0
        m_id = request.form.get("museum") or None
        image_rel = save_image(request.files.get("image"))

        with get_conn("Artist") as conn:
            execute(conn, """
                INSERT INTO Artifact (Artist_ID, M_ID, Title, Description, Type, Price, Quantity, Image)
                VALUES (:artist_id, :m_id, :title, :desc, :type, :price, :qty, :img)
            """, {
                "artist_id": session["user_id"],
                "m_id": m_id,
                "title": title,
                "desc": description,
                "type": type_,
                "price": price,
                "qty": quantity,
                "img": image_rel
            })
        flash("Artifact uploaded.", "success")
        return redirect(url_for("main.dashboard"))
    with get_conn('Artist') as conn:
        museums = fetch_all(conn, 'SELECT M_ID, Name FROM Museum ORDER BY Name')
    return render_template('upload_artifact.html', museums=museums)

@bp.post("/delete_artifact/<int:artifact_id>")
def delete_artifact(artifact_id):
    role = session.get("role")
    uid = session.get("user_id")

    with get_conn(role) as conn:
        art = fetch_one(conn, "SELECT Artifact_ID, Artist_ID, Image FROM Artifact WHERE Artifact_ID=:id", {"id": artifact_id})
        if not art:
            flash("Artifact not found.", "warning")
            return redirect(url_for("main.dashboard"))
        if role == "Artist" and art["Artist_ID"] != uid:
            flash("Unauthorized.", "danger")
            return redirect(url_for("main.dashboard"))

        # remove image file
        if art.get("Image"):
            img_path = os.path.join(settings.STATIC_DIR, art["Image"])
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception:
                pass

        # delete (FKs cascade)
        execute(conn, "DELETE FROM Artifact WHERE Artifact_ID=:id", {"id": artifact_id})

    flash("Artifact deleted.", "success")
    return redirect(url_for("main.dashboard"))

# -----------------------------
# Customer Dashboard
# -----------------------------
def customer_dashboard():
    search = request.args.get("search","").strip()
    ftype = request.args.get("filter_type","").strip()

    sql = "SELECT * FROM Artifact WHERE Quantity > 0"
    params = {}
    if search:
        sql += " AND Title LIKE :q"
        params["q"] = f"%{search}%"
    if ftype:
        sql += " AND Type = :t"
        params["t"] = ftype
    sql += " ORDER BY Created_At DESC"

    with get_conn("Customer") as conn:
        artifacts = fetch_all(conn, sql, params)
        exhibitions = fetch_all(conn, """
            SELECT e.Title, e.Theme, e.Start_Date, e.End_Date, e.Capacity, m.Name AS Museum_Name
            FROM Exhibition e
            LEFT JOIN Museum m ON e.M_ID = m.M_ID
            WHERE e.Start_Date >= CURRENT_DATE()
            ORDER BY e.Start_Date ASC
        """)
        types = [r["Type"] for r in fetch_all(conn, "SELECT DISTINCT Type FROM Artifact")]

    return render_template("dash_customer.html", artifacts=artifacts, exhibitions=exhibitions, types=types)

# -----------------------------
# Cart (Customer)
# -----------------------------
def _cart():
    return session.setdefault("cart", {})  # {artifact_id: qty}

@bp.post("/cart/add/<int:artifact_id>")
def cart_add(artifact_id):
    if session.get("role") != "Customer":
        flash("Only customers can add to cart.", "warning")
        return redirect(url_for("main.dashboard"))

    qty = max(1, int(request.form.get("qty", 1)))
    cart = _cart()
    cart[str(artifact_id)] = cart.get(str(artifact_id), 0) + qty
    session.modified = True
    flash("Added to cart.", "success")
    return redirect(url_for("main.dashboard"))

@bp.get("/cart")
def cart_view():
    if session.get("role") != "Customer":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))
    cart = _cart()
    items = []
    total = 0
    if cart:
        ids = [int(k) for k in cart.keys()]
        placeholders = ",".join([f":id{i}" for i in range(len(ids))])
        params = {f"id{i}": ids[i] for i in range(len(ids))}
        with get_conn("Customer") as conn:
            rows = fetch_all(conn, f"SELECT Artifact_ID, Title, Price, Image FROM Artifact WHERE Artifact_ID IN ({placeholders})", params)
        by_id = {r["Artifact_ID"]: r for r in rows}
        for aid_str, qty in cart.items():
            aid = int(aid_str)
            if aid in by_id:
                r = by_id[aid]
                line = {"Artifact_ID": aid, "Title": r["Title"], "Price": r["Price"], "Image": r.get("Image"), "Qty": qty, "Subtotal": float(r["Price"])*qty}
                items.append(line)
                total += line["Subtotal"]
    return render_template("cart.html", items=items, total=total)

@bp.post("/cart/update")
def cart_update():
    if session.get("role") != "Customer":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.cart_view"))
    cart = _cart()
    for key, val in request.form.items():
        if key.startswith("qty_"):
            aid = key.split("_",1)[1]
            try:
                q = int(val)
                if q <= 0:
                    cart.pop(aid, None)
                else:
                    cart[aid] = q
            except:
                pass
    session.modified = True
    flash("Cart updated.", "success")
    return redirect(url_for("main.cart_view"))

@bp.post("/cart/checkout")
def cart_checkout():
    if session.get("role") != "Customer":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))

    cart = session.get("cart") or {}
    cart = {str(aid): int(qty) for aid, qty in cart.items() if int(qty) > 0}
    if not cart:
        flash("Your cart is empty.", "info")
        return redirect(url_for("main.cart_view"))

    ids = list(cart.keys())
    placeholders = ",".join([f":id{k}" for k in ids])
    params = {f"id{k}": int(k) for k in ids}

    with get_conn("Customer") as conn:
        # 1️⃣ Lock and fetch artifacts for stock check
        rows = fetch_all(conn, f"""
            SELECT Artifact_ID, Title, Quantity AS Stock, Price
            FROM Artifact
            WHERE Artifact_ID IN ({placeholders})
            FOR UPDATE
        """, params)

        snapshot = {
            str(r["Artifact_ID"]): {
                "title": r["Title"],
                "stock": int(r["Stock"]),
                "price": float(r["Price"]),
            } for r in rows
        }

        # 2️⃣ Validate requested quantities
        problems = []
        for aid_str, qty in cart.items():
            info = snapshot.get(aid_str)
            if not info:
                problems.append(f"Artifact ID {aid_str} no longer exists.")
            elif qty > info["stock"]:
                problems.append(f"“{info['title']}” has only {info['stock']} left (you requested {qty}).")

        if problems:
            flash("Checkout failed: " + " ".join(problems), "danger")
            return redirect(url_for("main.cart_view"))

        # 3️⃣ Perform updates and inserts (connection context auto-commits)
        customer_id = session.get("user_id")
        if not customer_id:
            raise RuntimeError("Missing customer session.")

        for aid_str, qty in cart.items():
            aid = int(aid_str)
            price = snapshot[aid_str]["price"]
            total = round(price * qty, 2)

            # Decrement stock
            execute(conn, """
                UPDATE Artifact
                SET Quantity = Quantity - :q
                WHERE Artifact_ID = :aid
            """, {"aid": aid, "q": qty})

            # Add purchase record
            execute(conn, """
                INSERT INTO Purchase
                  (Customer_ID, Artifact_ID, Quantity, Total_Amount, Payment_Method)
                VALUES
                  (:cid, :aid, :q, :tot, :method)
            """, {
                "cid": customer_id,
                "aid": aid,
                "q": qty,
                "tot": total,
                "method": "Card"
            })

        # If no exception is raised, context auto-commits here

    # 4️⃣ Clear cart after success
    session["cart"] = {}
    session.modified = True
    flash("Purchase successful! Your cart has been cleared.", "success")
    return redirect(url_for("main.dashboard"))

# Legacy admin path support to match /admin/artifact/delete/<id>
@bp.route("/admin/artifact/delete/<int:artifact_id>", methods=["POST","GET"])
def admin_delete_artifact(artifact_id):
    if session.get("role") != "Admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))
    from sqlalchemy.exc import IntegrityError
    with get_conn("Admin") as conn:
        try:
            execute(conn, "DELETE FROM Artifact WHERE Artifact_ID=:id", {"id": artifact_id})
            flash("Artifact deleted successfully.", "success")
        except IntegrityError:
            execute(conn, "UPDATE Artifact SET Quantity=0 WHERE Artifact_ID=:id", {"id": artifact_id})
            flash("Artifact has purchases; archived (Quantity set to 0).", "info")
        except Exception as e:
            flash(f"Error deleting artifact: {e}", "danger")
    return redirect(url_for("main.dashboard"))

@bp.route("/artist/exhibition/create", methods=["GET","POST"])
def create_exhibition():
    if session.get("role") != "Artist":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        title = request.form.get("title","").strip()
        theme = request.form.get("theme","").strip()
        start = request.form.get("start")
        end = request.form.get("end")
        capacity = int(request.form.get("capacity") or 0)
        museum_id = int(request.form.get("museum"))
        with get_conn("Artist") as conn:
            execute(conn, """
                INSERT INTO Exhibition (Title, Theme, Start_Date, End_Date, Capacity, M_ID, Artist_ID)
                VALUES (:t,:th,:sd,:ed,:cap,:mid,:aid)
            """, {"t": title, "th": theme, "sd": start, "ed": end, "cap": capacity, "mid": museum_id, "aid": session.get("user_id")})
        flash("Exhibition created.", "success")
        return redirect(url_for("main.dashboard"))
    with get_conn("Artist") as conn:
        museums = fetch_all(conn, "SELECT M_ID, Name FROM Museum ORDER BY Name")
    return render_template("create_exhibition.html", museums=museums)


@bp.get("/admin/queries")
def admin_queries_home():
    if session.get("role") != "Admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))
    return render_template("admin_queries_home.html")

@bp.get("/admin/queries/run")
def admin_run_complex_query():
    if session.get("role") != "Admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("main.dashboard"))

    name = request.args.get("name", "")

    # All-inline, schema-safe queries (no views required).
    # If you DO have the views, these still work fine.
    queries = {
        "top_customers": (
            "Top Customers by Spend",
            """
            SELECT u.User_ID AS Customer_ID,
                   CONCAT(u.Fname,' ',u.Lname) AS Name,
                   SUM(p.Total_Amount) AS TotalSpent
            FROM Purchase p
            JOIN User u ON u.User_ID = p.Customer_ID
            GROUP BY u.User_ID, Name
            ORDER BY TotalSpent DESC
            LIMIT 10
            """
        ),

        "best_selling": (
            "Best Selling Artifacts",
            """
            SELECT a.Artifact_ID,
                   a.Title,
                   COALESCE(SUM(p.Quantity),0)     AS UnitsSold,
                   COALESCE(SUM(p.Total_Amount),0) AS Revenue
            FROM Artifact a
            LEFT JOIN Purchase p ON p.Artifact_ID = a.Artifact_ID
            GROUP BY a.Artifact_ID, a.Title
            ORDER BY UnitsSold DESC, Revenue DESC
            LIMIT 20
            """
        ),

        "above_avg_spend": (
            "Customers Above Average Spend",
            # Inline average (no view dependency)
            """
            WITH cust_spend AS (
                SELECT p.Customer_ID,
                       SUM(p.Total_Amount) AS TotalSpent
                FROM Purchase p
                GROUP BY p.Customer_ID
            ),
            avg_spend AS (
                SELECT AVG(TotalSpent) AS AvgSpent FROM cust_spend
            )
            SELECT u.User_ID AS Customer_ID,
                   CONCAT(u.Fname,' ',u.Lname) AS Name,
                   cs.TotalSpent
            FROM cust_spend cs
            JOIN avg_spend av
            JOIN User u ON u.User_ID = cs.Customer_ID
            WHERE cs.TotalSpent > av.AvgSpent
            ORDER BY cs.TotalSpent DESC
            LIMIT 50
            """
        ),

        "artist_revenue": (
            "Revenue by Artist",
            """
            SELECT a.Artist_ID,
                   CONCAT(u.Fname,' ',u.Lname) AS Artist_Name,
                   COALESCE(SUM(p.Total_Amount),0) AS Revenue
            FROM Artifact a
            JOIN User u ON u.User_ID = a.Artist_ID
            LEFT JOIN Purchase p ON p.Artifact_ID = a.Artifact_ID
            GROUP BY a.Artist_ID, Artist_Name
            ORDER BY Revenue DESC
            LIMIT 50
            """
        ),

        "low_stock": (
            "Low Stock Alerts",
            # No view needed; uses Quantity from Artifact
            """
            SELECT Artifact_ID, Title, Quantity
            FROM Artifact
            WHERE Quantity <= 3
            ORDER BY Quantity ASC, Title ASC
            """
        ),

        "upcoming_ex": (
            "Upcoming Exhibitions",
            # Keep it view-free and schema-safe:
            # Uses only Exhibition_ID, Title, Start_Date, End_Date
            """
            SELECT Exhibition_ID, Title, Start_Date, End_Date
            FROM Exhibition
            WHERE Start_Date >= CURRENT_DATE
            ORDER BY Start_Date ASC
            LIMIT 100
            """
        ),

        "type_max_price": (
            "Most Expensive Artifact per Type",
            # Inline windowing to avoid relying on a view
            """
            SELECT t.Type, t.Artifact_ID, t.Title, t.Price
            FROM (
                SELECT a.*,
                       ROW_NUMBER() OVER (PARTITION BY a.Type ORDER BY a.Price DESC, a.Artifact_ID) AS rn
                FROM Artifact a
            ) t
            WHERE t.rn = 1
            ORDER BY t.Type
            LIMIT 50
            """
        ),
    }

    if name not in queries:
        flash("Unknown query.", "warning")
        return redirect(url_for("main.admin_queries_home"))

    title, sql = queries[name]
    with get_conn("Admin") as conn:
        rows = fetch_all(conn, sql)

    return render_template("admin_query.html", rows=rows, qname=title)


