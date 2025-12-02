from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask import session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

from config import Config
import os

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    print("DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])


    db.init_app(app)
    Migrate(app, db)

    class Wish(db.Model):
        __tablename__ = "wishes"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        message = db.Column(db.Text, nullable=False)
        created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

        def __repr__(self):
            return f"<Wish {self.name}>"

    app.Wish = Wish

    class Invite(db.Model):
        __tablename__ = "invites"

        id = db.Column(db.Integer, primary_key=True)
        person_name = db.Column(db.String(120), nullable=False)
        village_name = db.Column(db.String(120), nullable=False)
        total_people = db.Column(db.Integer, nullable=False, default=1)
        created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    app.Invite = Invite

    # Ensure tables exist when the app starts (works with Flask CLI factory)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("Failed to create tables:", e)

    @app.route("/", methods=["GET", "POST"])
    def index():
        drive_link = "https://drive.google.com/drive/folders/DUMMY_FOLDER_ID"

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            message = request.form.get("message", "").strip()

            if not name or not message:
                flash("Please fill in both Name and Message.", "error")
            else:
                new_wish = Wish(name=name, message=message)
                db.session.add(new_wish)
                db.session.commit()
                flash("Thank you for your wishes! 💌", "success")
                return redirect(url_for("index"))

        wishes = Wish.query.order_by(Wish.created_at.desc()).all()

        barat_date_text = "28 March 2026"
        barat_time_text = "8:00 PM"
        barat_venue_text = "Haji Jamil Akhter's home"

        walima_date_text = "30 March 2026"
        walima_time_text = "12:00 PM"
        walima_venue_text = "Haji Jamil Akhter's home"

        # Prefer a project-local background image at `static/images/background.jpg`.
        # If not present, do not set a background so templates can render without it.
        static_bg_rel = os.path.join("static", "images", "background.jpg")
        static_bg_abs = os.path.join(app.root_path, "static", "images", "background.jpg")
        if os.path.exists(static_bg_abs):
            background_image_url = url_for('static', filename='images/background.jpg')
        else:
            background_image_url = None

        return render_template(
            "index.html",
            barat_date=barat_date_text,
            barat_time=barat_time_text,
            venue=barat_venue_text,
            walima_date=walima_date_text,
            walima_time=walima_time_text,
            walima_venue=walima_venue_text,
            drive_link=drive_link,
            wishes=wishes,
            background_image_url=background_image_url,
        )

    # NOTE: legacy dynamic background route removed in favor of serving
    # `static/images/background.jpg` when present. Template will not apply
    # a background if that file is missing.

    @app.cli.command("init-db")
    def init_db_command():
        """Initialize the database tables."""
        with app.app_context():
            db.create_all()
            print("✅ Database tables created.")

    @app.cli.command("upgrade-db")
    def upgrade_db_command():
        """Run migrations (alias for `flask db upgrade`)."""
        # Provides a friendly alias; actual migration commands via Flask-Migrate CLI.
        print("Use: flask db init; flask db migrate -m 'msg'; flask db upgrade")

    @app.cli.command("test-db")
    def test_db_command():
        """Simple connectivity test: attempts SELECT 1."""
        from sqlalchemy import text
        with app.app_context():
            try:
                result = db.session.execute(text("SELECT 1"))
                print("✅ DB connectivity OK:", list(result.fetchall()))
            except Exception as e:
                print("❌ DB connectivity failed:", repr(e))
                # Surface full URI minus password for clarity
                uri = app.config.get("SQLALCHEMY_DATABASE_URI", "<none>")
                # Mask password portion for safety
                if "@" in uri and ":" in uri.split("@", 1)[0]:
                    # user:password@
                    prefix, rest = uri.split("@", 1)
                    user = prefix.split(":", 1)[0]
                    masked = f"{user}:***@{rest}"
                    print("URI:", masked)
                else:
                    print("URI:", uri)

    @app.cli.command("fix-invites-schema")
    def fix_invites_schema():
        """Make the `invites.code` column nullable/default NULL so inserts don't fail.

        This command is idempotent and safe to run on local/dev databases.
        It inspects the `information_schema` column metadata and alters the
        column only if it's present and non-nullable.
        """
        from sqlalchemy import text
        with app.app_context():
            try:
                db_name = app.config.get("MYSQL_DB") or app.config.get("DATABASE") or app.config.get("SQLALCHEMY_DATABASE_URI")
                # Prefer the explicit DB name from config
                if isinstance(db_name, str) and "://" in db_name:
                    # fallback: extract DB name from URI path
                    try:
                        db_name = app.config.get("MYSQL_DB")
                    except Exception:
                        db_name = None

                if not db_name:
                    print("Could not determine database name from config; set MYSQL_DB env or ensure SQLALCHEMY_DATABASE_URI contains DB name.")
                    return

                q = text(
                    "SELECT IS_NULLABLE FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = 'invites' AND COLUMN_NAME = 'code'"
                )
                row = db.session.execute(q, {"schema": db_name}).fetchone()
                if not row:
                    print("Column 'code' not found on table 'invites' — nothing to do.")
                    return
                is_nullable = row[0]
                if is_nullable == 'YES':
                    print("Column 'code' is already nullable — nothing to change.")
                    return

                print("Altering 'invites.code' to be NULLABLE (DEFAULT NULL)...")
                db.session.execute(text("ALTER TABLE invites MODIFY COLUMN code VARCHAR(64) NULL DEFAULT NULL;"))
                db.session.commit()
                print("✅ Updated 'invites.code' to allow NULL values.")
                # Now ensure `created_by` is nullable as well to avoid insert errors
                q2 = text(
                    "SELECT IS_NULLABLE FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = 'invites' AND COLUMN_NAME = 'created_by'"
                )
                row2 = db.session.execute(q2, {"schema": db_name}).fetchone()
                if not row2:
                    print("Column 'created_by' not found on table 'invites' — nothing to do for created_by.")
                    return
                is_nullable2 = row2[0]
                if is_nullable2 == 'YES':
                    print("Column 'created_by' is already nullable — nothing to change.")
                    return

                print("Altering 'invites.created_by' to be NULLABLE (DEFAULT NULL)...")
                db.session.execute(text("ALTER TABLE invites MODIFY COLUMN created_by INT NULL DEFAULT NULL;"))
                db.session.commit()
                print("✅ Updated 'invites.created_by' to allow NULL values.")
            except Exception as e:
                print("Failed to alter invites.code:", repr(e))

    # --- Simple root login and admin invite management ---
    def is_logged_in():
        return session.get("root_logged_in") is True

    @app.route("/login", methods=["GET", "POST"])
    def login():
        # If already logged in, go straight to admin page
        if is_logged_in():
            return redirect(url_for("admin_invites"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            # Simple check: allow configurable root username/password via env
            expected_user = app.config.get("ROOT_USER", "root")
            valid_user = username.lower() == expected_user.lower()
            expected = app.config.get("ROOT_PASSWORD", "rootpass")
            if valid_user and password == expected:
                session.permanent = True  # use configured PERMANENT_SESSION_LIFETIME
                session["root_logged_in"] = True
                flash("Logged in successfully.", "success")
                return redirect(url_for("admin_invites"))
            else:
                flash("Invalid credentials.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.pop("root_logged_in", None)
        flash("Logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/admin/invites", methods=["GET", "POST"])
    def admin_invites():
        if not is_logged_in():
            return redirect(url_for("login"))

        if request.method == "POST":
            person_name = request.form.get("person_name", "").strip()
            village_name = request.form.get("village_name", "").strip()
            total_people = request.form.get("total_people", "1").strip()
            try:
                total_people = int(total_people)
            except ValueError:
                total_people = 1

            if not person_name or not village_name or total_people < 1:
                flash("Please provide valid details.", "error")
            else:
                inv = Invite(person_name=person_name, village_name=village_name, total_people=total_people)
                db.session.add(inv)
                db.session.commit()
                flash("Invite saved.", "success")
                return redirect(url_for("admin_invites"))

        invites = Invite.query.order_by(Invite.created_at.desc()).all()
        total_invited_people = sum(i.total_people for i in invites)
        return render_template("admin_invites.html", invites=invites, total_invited_people=total_invited_people)

    @app.route("/admin/invites/<int:invite_id>/delete", methods=["GET"])  # simple GET to keep UI minimal
    def delete_invite(invite_id):
        if not is_logged_in():
            return redirect(url_for("login"))
        inv = Invite.query.get(invite_id)
        if not inv:
            flash("Invite not found.", "error")
            return redirect(url_for("admin_invites"))
        db.session.delete(inv)
        db.session.commit()
        flash("Invite deleted.", "success")
        return redirect(url_for("admin_invites"))

    @app.route("/admin/invites/<int:invite_id>/edit", methods=["POST"])  # update via modal form submit
    def edit_invite(invite_id):
        if not is_logged_in():
            return redirect(url_for("login"))
        inv = Invite.query.get(invite_id)
        if not inv:
            flash("Invite not found.", "error")
            return redirect(url_for("admin_invites"))
        person_name = request.form.get("person_name", inv.person_name).strip()
        village_name = request.form.get("village_name", inv.village_name).strip()
        total_people = request.form.get("total_people", str(inv.total_people)).strip()
        try:
            total_people = int(total_people)
        except ValueError:
            total_people = inv.total_people
        if not person_name or not village_name or total_people < 1:
            flash("Please provide valid details.", "error")
            return redirect(url_for("admin_invites"))
        inv.person_name = person_name
        inv.village_name = village_name
        inv.total_people = total_people
        db.session.commit()
        flash("Invite updated.", "success")
        return redirect(url_for("admin_invites"))

    @app.route("/admin/invites/export.csv")
    def export_invites_csv():
        if not is_logged_in():
            return redirect(url_for("login"))
        from io import StringIO
        import csv
        invites = Invite.query.order_by(Invite.created_at.asc()).all()
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Person Name", "Village", "Total", "Created At"])
        for inv in invites:
            writer.writerow([inv.person_name, inv.village_name, inv.total_people, inv.created_at.isoformat()])
        buf.seek(0)
        return app.response_class(buf.read(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=invites.csv'})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
