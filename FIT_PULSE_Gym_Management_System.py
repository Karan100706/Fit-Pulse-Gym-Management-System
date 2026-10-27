
import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd

DB = "fit_pulse.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, email TEXT, dob TEXT, address TEXT,
        emergency TEXT, joining_date TEXT, membership TEXT, trainer TEXT,
        fitness_goal TEXT, status TEXT DEFAULT 'Active'
    );
    CREATE TABLE IF NOT EXISTS memberships(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER, plan TEXT, start_date TEXT, expiry_date TEXT,
        amount REAL DEFAULT 0, discount REAL DEFAULT 0, status TEXT DEFAULT 'Active'
    );
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER, visit_date TEXT, check_in TEXT, method TEXT
    );
    CREATE TABLE IF NOT EXISTS trainers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, specialization TEXT, availability TEXT
    );
    CREATE TABLE IF NOT EXISTS workouts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER, trainer TEXT, exercise TEXT, sets TEXT,
        reps TEXT, weight TEXT, duration TEXT, workout_day TEXT, instructions TEXT
    );
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER, amount REAL, payment_date TEXT,
        method TEXT, status TEXT, transaction_id TEXT
    );
    CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT, interested_plan TEXT, source TEXT,
        followup_date TEXT, sales_person TEXT, status TEXT
    );
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER, trainer TEXT, appointment_date TEXT,
        appointment_time TEXT, status TEXT
    );
    CREATE TABLE IF NOT EXISTS equipment(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, equipment_id TEXT, purchase_date TEXT,
        warranty TEXT, maintenance_date TEXT, condition TEXT, repair_status TEXT
    );
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT, category TEXT, stock INTEGER, supplier TEXT, low_stock INTEGER
    );
    CREATE TABLE IF NOT EXISTS progress(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER, record_date TEXT, weight REAL, height REAL,
        bmi REAL, notes TEXT
    );
    CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT, action_time TEXT
    );
    """)
    con.commit()
    con.close()

def execute(sql, params=(), fetch=False):
    con = db()
    cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    con.commit()
    con.close()
    return rows

def audit(action):
    execute("INSERT INTO audit(action, action_time) VALUES(?,?)",
            (action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def df(sql, params=()):
    rows = execute(sql, params, True)
    return pd.DataFrame([dict(r) for r in rows])

def member_map():
    rows = execute("SELECT id,name FROM members ORDER BY name", fetch=True)
    return {f"{r['name']} (ID {r['id']})": r["id"] for r in rows}

init_db()

st.set_page_config(page_title="FIT PULSE", page_icon="💪", layout="wide")

st.sidebar.title("💪 FIT PULSE")
st.sidebar.caption("Gym Management System")
menu = st.sidebar.radio("Navigation", [
    "Dashboard", "Members", "Memberships", "Attendance", "Trainers",
    "Workout Plans", "Fitness Progress", "Payments", "Leads",
    "Appointments", "Equipment", "Inventory", "Reports", "Audit Log"
])

st.sidebar.divider()
st.sidebar.info("Production-oriented prototype with SQLite database. Modules can be expanded for payment gateways, WhatsApp/SMS, QR/RFID, biometrics and multi-branch deployment.")

# Dashboard
if menu == "Dashboard":
    st.title("FIT PULSE Dashboard")
    st.caption("Centralized view of gym operations")

    members = execute("SELECT COUNT(*) c FROM members", fetch=True)[0]["c"]
    active = execute("SELECT COUNT(*) c FROM members WHERE status='Active'", fetch=True)[0]["c"]
    trainers = execute("SELECT COUNT(*) c FROM trainers", fetch=True)[0]["c"]
    revenue = execute("SELECT COALESCE(SUM(amount),0) r FROM payments WHERE status='Paid'", fetch=True)[0]["r"]
    pending = execute("SELECT COALESCE(SUM(amount),0) r FROM payments WHERE status='Pending'", fetch=True)[0]["r"]
    leads = execute("SELECT COUNT(*) c FROM leads", fetch=True)[0]["c"]
    today_att = execute("SELECT COUNT(*) c FROM attendance WHERE visit_date=?", (str(date.today()),), True)[0]["c"]
    expiring = execute("""
        SELECT COUNT(*) c FROM memberships
        WHERE expiry_date BETWEEN ? AND ? AND status='Active'
    """, (str(date.today()), str(date.today()+timedelta(days=7))), True)[0]["c"]

    a,b,c,d = st.columns(4)
    a.metric("Total Members", members)
    b.metric("Active Members", active)
    c.metric("Today's Attendance", today_att)
    d.metric("Trainers", trainers)
    e,f,g,h = st.columns(4)
    e.metric("Total Revenue", f"₹{revenue:,.0f}")
    f.metric("Pending Payments", f"₹{pending:,.0f}")
    g.metric("New Leads", leads)
    h.metric("Expiring in 7 Days", expiring)

    st.subheader("Recent Activity")
    recent = df("SELECT action, action_time FROM audit ORDER BY id DESC LIMIT 10")
    st.dataframe(recent, use_container_width=True, hide_index=True)

    st.subheader("Membership Status")
    status_df = df("SELECT status, COUNT(*) count FROM memberships GROUP BY status")
    if not status_df.empty:
        st.bar_chart(status_df.set_index("status"))

# Members
elif menu == "Members":
    st.title("Member Registration & Profiles")
    with st.expander("➕ Register New Member", expanded=True):
        with st.form("member_form"):
            c1,c2,c3 = st.columns(3)
            name = c1.text_input("Full Name *")
            phone = c2.text_input("Phone")
            email = c3.text_input("Email")
            dob = c1.date_input("Date of Birth", value=date(2000,1,1))
            joining = c2.date_input("Joining Date", value=date.today())
            membership = c3.text_input("Membership Plan", value="Monthly")
            address = c1.text_area("Address")
            emergency = c2.text_input("Emergency Contact")
            trainer = c3.text_input("Assigned Trainer")
            goal = c1.text_input("Fitness Goal")
            status = c2.selectbox("Status", ["Active","Inactive"])
            submitted = st.form_submit_button("Save Member", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Name is required.")
                else:
                    execute("""INSERT INTO members
                    (name,phone,email,dob,address,emergency,joining_date,membership,trainer,fitness_goal,status)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (name,phone,email,str(dob),address,emergency,str(joining),membership,trainer,goal,status))
                    audit(f"Registered new member: {name}")
                    st.success("Member registered successfully.")
                    st.rerun()

    st.subheader("Member Directory")
    search = st.text_input("Search by name or phone")
    if search:
        data = df("SELECT * FROM members WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC",
                  (f"%{search}%",f"%{search}%"))
    else:
        data = df("SELECT * FROM members ORDER BY id DESC")
    st.dataframe(data, use_container_width=True, hide_index=True)

# Memberships
elif menu == "Memberships":
    st.title("Membership & Subscription Management")
    mmap = member_map()
    if not mmap:
        st.warning("Add a member first.")
    else:
        with st.form("membership"):
            member = st.selectbox("Member", list(mmap))
            plan = st.selectbox("Plan", ["Monthly","Quarterly","Half-yearly","Annual","Personal Training","Custom"])
            start = st.date_input("Start Date", date.today())
            days = {"Monthly":30,"Quarterly":90,"Half-yearly":180,"Annual":365,
                    "Personal Training":30,"Custom":30}[plan]
            expiry = st.date_input("Expiry Date", start + timedelta(days=days))
            amount = st.number_input("Amount", min_value=0.0, step=500.0)
            discount = st.number_input("Discount", min_value=0.0, step=100.0)
            status = st.selectbox("Status", ["Active","Pending","Expired"])
            if st.form_submit_button("Save Membership", type="primary"):
                execute("""INSERT INTO memberships(member_id,plan,start_date,expiry_date,amount,discount,status)
                           VALUES(?,?,?,?,?,?,?)""",
                        (mmap[member],plan,str(start),str(expiry),amount,discount,status))
                audit(f"Created {plan} membership for {member}")
                st.success("Membership saved.")
                st.rerun()
    st.dataframe(df("""SELECT m.name, s.plan, s.start_date, s.expiry_date,
                       s.amount, s.discount, s.status
                       FROM memberships s JOIN members m ON m.id=s.member_id
                       ORDER BY s.id DESC"""), use_container_width=True, hide_index=True)

# Attendance
elif menu == "Attendance":
    st.title("Digital Attendance")
    mmap = member_map()
    if mmap:
        with st.form("attendance"):
            member = st.selectbox("Member", list(mmap))
            visit = st.date_input("Visit Date", date.today())
            method = st.selectbox("Attendance Method", ["Manual","QR Code","Member ID","RFID","Biometric"])
            if st.form_submit_button("Mark Attendance", type="primary"):
                execute("INSERT INTO attendance(member_id,visit_date,check_in,method) VALUES(?,?,?,?)",
                        (mmap[member],str(visit),datetime.now().strftime("%H:%M:%S"),method))
                audit(f"Attendance marked for {member}")
                st.success("Attendance recorded.")
                st.rerun()
    else:
        st.warning("Add members first.")
    st.subheader("Attendance History")
    st.dataframe(df("""SELECT m.name, a.visit_date, a.check_in, a.method
                       FROM attendance a JOIN members m ON m.id=a.member_id
                       ORDER BY a.id DESC"""), use_container_width=True, hide_index=True)

# Trainers
elif menu == "Trainers":
    st.title("Trainer Management")
    with st.form("trainer"):
        name = st.text_input("Trainer Name")
        phone = st.text_input("Phone")
        spec = st.text_input("Specialization")
        availability = st.text_input("Availability", "Morning / Evening")
        if st.form_submit_button("Add Trainer", type="primary"):
            if name.strip():
                execute("INSERT INTO trainers(name,phone,specialization,availability) VALUES(?,?,?,?)",
                        (name,phone,spec,availability))
                audit(f"Added trainer: {name}")
                st.success("Trainer added.")
                st.rerun()
    st.dataframe(df("SELECT * FROM trainers ORDER BY id DESC"), use_container_width=True, hide_index=True)

# Workout
elif menu == "Workout Plans":
    st.title("Workout & Training Plan Management")
    mmap = member_map()
    if mmap:
        with st.form("workout"):
            member = st.selectbox("Member", list(mmap))
            trainer = st.text_input("Trainer")
            exercise = st.text_input("Exercise")
            c1,c2,c3 = st.columns(3)
            sets = c1.text_input("Sets")
            reps = c2.text_input("Repetitions")
            weight = c3.text_input("Weight")
            duration = c1.text_input("Duration")
            day = c2.selectbox("Workout Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
            instructions = c3.text_area("Trainer Instructions")
            if st.form_submit_button("Save Workout Plan", type="primary"):
                execute("""INSERT INTO workouts(member_id,trainer,exercise,sets,reps,weight,duration,workout_day,instructions)
                           VALUES(?,?,?,?,?,?,?,?,?)""",
                        (mmap[member],trainer,exercise,sets,reps,weight,duration,day,instructions))
                audit(f"Updated workout plan for {member}")
                st.success("Workout plan saved.")
                st.rerun()
    st.dataframe(df("""SELECT m.name, w.trainer,w.exercise,w.sets,w.reps,w.weight,w.duration,
                              w.workout_day,w.instructions
                       FROM workouts w JOIN members m ON m.id=w.member_id
                       ORDER BY w.id DESC"""), use_container_width=True, hide_index=True)

# Progress
elif menu == "Fitness Progress":
    st.title("Fitness Progress Tracking")
    mmap = member_map()
    if mmap:
        with st.form("progress"):
            member = st.selectbox("Member", list(mmap))
            record = st.date_input("Record Date", date.today())
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
            height = st.number_input("Height (cm)", min_value=0.0, step=0.1)
            bmi = (weight / ((height/100)**2)) if height > 0 else 0
            st.info(f"Calculated BMI: {bmi:.2f}")
            notes = st.text_area("Notes / Progress")
            if st.form_submit_button("Save Progress", type="primary"):
                execute("""INSERT INTO progress(member_id,record_date,weight,height,bmi,notes)
                           VALUES(?,?,?,?,?,?)""",
                        (mmap[member],str(record),weight,height,bmi,notes))
                audit(f"Added fitness progress for {member}")
                st.success("Progress saved.")
                st.rerun()
    st.dataframe(df("""SELECT m.name,p.record_date,p.weight,p.height,p.bmi,p.notes
                       FROM progress p JOIN members m ON m.id=p.member_id
                       ORDER BY p.id DESC"""), use_container_width=True, hide_index=True)

# Payments
elif menu == "Payments":
    st.title("Payments, Billing & Receipts")
    mmap = member_map()
    if mmap:
        with st.form("payment"):
            member = st.selectbox("Member", list(mmap))
            amount = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
            pdate = st.date_input("Payment Date", date.today())
            method = st.selectbox("Payment Method", ["Cash","UPI","Card","Bank Transfer","Online Gateway"])
            status = st.selectbox("Payment Status", ["Paid","Pending","Refunded"])
            tx = st.text_input("Transaction ID")
            if st.form_submit_button("Record Payment", type="primary"):
                execute("""INSERT INTO payments(member_id,amount,payment_date,method,status,transaction_id)
                           VALUES(?,?,?,?,?,?)""",
                        (mmap[member],amount,str(pdate),method,status,tx))
                audit(f"Payment recorded for {member}: ₹{amount}")
                st.success("Payment recorded and receipt data stored.")
                st.rerun()
    st.dataframe(df("""SELECT m.name,p.amount,p.payment_date,p.method,p.status,p.transaction_id
                       FROM payments p JOIN members m ON m.id=p.member_id
                       ORDER BY p.id DESC"""), use_container_width=True, hide_index=True)

# Leads
elif menu == "Leads":
    st.title("Lead & Enquiry Management")
    with st.form("lead"):
        c1,c2 = st.columns(2)
        name = c1.text_input("Customer Name")
        phone = c2.text_input("Phone")
        plan = c1.text_input("Interested Membership")
        source = c2.selectbox("Lead Source", ["Walk-in","Website","Instagram","Referral","Advertisement","Other"])
        follow = c1.date_input("Follow-up Date", date.today())
        sales = c2.text_input("Sales Representative")
        status = c1.selectbox("Status", ["New","Contacted","Gym Visit","Trial","Converted","Lost"])
        if st.form_submit_button("Add Lead", type="primary"):
            execute("""INSERT INTO leads(name,phone,interested_plan,source,followup_date,sales_person,status)
                       VALUES(?,?,?,?,?,?,?)""",
                    (name,phone,plan,source,str(follow),sales,status))
            audit(f"Added lead: {name}")
            st.success("Lead added.")
            st.rerun()
    st.dataframe(df("SELECT * FROM leads ORDER BY id DESC"), use_container_width=True, hide_index=True)

# Appointments
elif menu == "Appointments":
    st.title("Trainer Appointments")
    mmap = member_map()
    if mmap:
        with st.form("appointment"):
            member = st.selectbox("Member", list(mmap))
            trainer = st.text_input("Trainer")
            adate = st.date_input("Appointment Date", date.today())
            atime = st.time_input("Appointment Time")
            status = st.selectbox("Status", ["Booked","Completed","Cancelled","Rescheduled"])
            if st.form_submit_button("Book Appointment", type="primary"):
                execute("""INSERT INTO appointments(member_id,trainer,appointment_date,appointment_time,status)
                           VALUES(?,?,?,?,?)""",
                        (mmap[member],trainer,str(adate),str(atime),status))
                audit(f"Booked appointment for {member}")
                st.success("Appointment booked.")
                st.rerun()
    st.dataframe(df("""SELECT m.name,a.trainer,a.appointment_date,a.appointment_time,a.status
                       FROM appointments a JOIN members m ON m.id=a.member_id
                       ORDER BY a.id DESC"""), use_container_width=True, hide_index=True)

# Equipment
elif menu == "Equipment":
    st.title("Equipment & Maintenance")
    with st.form("equipment"):
        name = st.text_input("Equipment Name")
        eid = st.text_input("Equipment ID")
        purchase = st.date_input("Purchase Date", date.today())
        warranty = st.text_input("Warranty")
        maintenance = st.date_input("Next Maintenance Date", date.today()+timedelta(days=30))
        condition = st.selectbox("Condition", ["Excellent","Good","Needs Attention","Out of Service"])
        repair = st.selectbox("Repair Status", ["Not Required","Pending","In Progress","Completed"])
        if st.form_submit_button("Add Equipment", type="primary"):
            execute("""INSERT INTO equipment(name,equipment_id,purchase_date,warranty,maintenance_date,condition,repair_status)
                       VALUES(?,?,?,?,?,?,?)""",
                    (name,eid,str(purchase),warranty,str(maintenance),condition,repair))
            audit(f"Added equipment: {name}")
            st.success("Equipment added.")
            st.rerun()
    st.dataframe(df("SELECT * FROM equipment ORDER BY id DESC"), use_container_width=True, hide_index=True)

# Inventory
elif menu == "Inventory":
    st.title("Inventory Management")
    with st.form("inventory"):
        item = st.text_input("Item")
        category = st.text_input("Category", "Gym Accessories")
        stock = st.number_input("Current Stock", min_value=0, step=1)
        supplier = st.text_input("Supplier")
        low = st.number_input("Low-stock Alert Level", min_value=0, step=1, value=5)
        if st.form_submit_button("Save Inventory Item", type="primary"):
            execute("INSERT INTO inventory(item,category,stock,supplier,low_stock) VALUES(?,?,?,?,?)",
                    (item,category,stock,supplier,low))
            audit(f"Added inventory item: {item}")
            st.success("Inventory item saved.")
            st.rerun()
    inv = df("SELECT * FROM inventory ORDER BY id DESC")
    st.dataframe(inv, use_container_width=True, hide_index=True)
    if not inv.empty:
        low_items = inv[inv["stock"] <= inv["low_stock"]]
        if not low_items.empty:
            st.warning("Low-stock items detected.")
            st.dataframe(low_items, use_container_width=True, hide_index=True)

# Reports
elif menu == "Reports":
    st.title("Comprehensive Reports")
    report = st.selectbox("Choose Report", [
        "Member Report","Financial Report","Attendance Report",
        "Membership Report","Trainer Report","Lead Report","Equipment Report","Inventory Report"
    ])
    queries = {
        "Member Report":"SELECT * FROM members",
        "Financial Report":"SELECT m.name,p.amount,p.payment_date,p.method,p.status,p.transaction_id FROM payments p JOIN members m ON m.id=p.member_id",
        "Attendance Report":"SELECT m.name,a.visit_date,a.check_in,a.method FROM attendance a JOIN members m ON m.id=a.member_id",
        "Membership Report":"SELECT m.name,s.plan,s.start_date,s.expiry_date,s.amount,s.discount,s.status FROM memberships s JOIN members m ON m.id=s.member_id",
        "Trainer Report":"SELECT * FROM trainers",
        "Lead Report":"SELECT * FROM leads",
        "Equipment Report":"SELECT * FROM equipment",
        "Inventory Report":"SELECT * FROM inventory"
    }
    data = df(queries[report])
    st.dataframe(data, use_container_width=True, hide_index=True)
    if not data.empty:
        csv = data.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export Report as CSV", csv, f"{report.lower().replace(' ','_')}.csv", "text/csv")

# Audit
elif menu == "Audit Log":
    st.title("Audit & Activity Tracking")
    st.dataframe(df("SELECT action,action_time FROM audit ORDER BY id DESC"),
                 use_container_width=True, hide_index=True)

st.sidebar.divider()
st.sidebar.caption("FIT PULSE • Scalable Gym Management System")
