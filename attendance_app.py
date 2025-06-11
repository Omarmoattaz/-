
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="تطبيق الحضور والانصراف", layout="wide")

st.title("📊 تطبيق حساب الحضور والانصراف من ملف البصمة")

uploaded_file = st.file_uploader("📂 ارفع ملف البصمة (Excel)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()

        required_columns = {"Name", "Date", "Time", "Status"}
        if not required_columns.issubset(df.columns):
            st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة: Name, Date, Time, Status")
        else:
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True).dt.date
            df["Time"] = pd.to_datetime(df["Time"]).dt.time
            df["Datetime"] = df.apply(lambda row: datetime.combine(row["Date"], row["Time"]), axis=1)

            grouped = df.groupby(["Name", "Date"])
            attendance_data = []

            summary = {}

            all_dates = sorted(df["Date"].unique())

            for (name, date), group in grouped:
                in_times = group[group["Status"] == "C/In"].sort_values("Datetime")["Time"].tolist()
                out_times = group[group["Status"] == "C/Out"].sort_values("Datetime")["Time"].tolist()

                first_in = in_times[0] if in_times else "--"
                last_out = out_times[-1] if out_times else "--"

                work_hours = "--"
                if first_in != "--" and last_out != "--":
                    in_dt = datetime.combine(date, first_in)
                    out_dt = datetime.combine(date, last_out)
                    diff = out_dt - in_dt
                    hours, remainder = divmod(diff.seconds, 3600)
                    minutes = remainder // 60
                    work_hours = f"{hours}س {minutes}د"

                    if name not in summary:
                        summary[name] = {
                            "total_seconds": 0,
                            "days": set(),
                            "in_count": 0,
                            "out_count": 0,
                            "dates": set(all_dates)
                        }
                    summary[name]["total_seconds"] += diff.total_seconds()
                    summary[name]["days"].add(date)

                if name in summary:
                    summary[name]["in_count"] += len(in_times)
                    summary[name]["out_count"] += len(out_times)

                attendance_data.append({
                    "الاسم": name,
                    "التاريخ": date.strftime("%Y-%m-%d"),
                    "أول حضور": first_in if first_in == "--" else first_in.strftime("%H:%M"),
                    "آخر انصراف": last_out if last_out == "--" else last_out.strftime("%H:%M"),
                    "ساعات العمل": work_hours
                })

            st.subheader("📅 جدول الحضور والانصراف")
            st.dataframe(attendance_data, use_container_width=True)

            st.subheader("📈 ملخص كل موظف")
            summary_table = []
            for name, data in summary.items():
                total_hours = int(data["total_seconds"] // 3600)
                total_minutes = int((data["total_seconds"] % 3600) // 60)
                missing_days = [d.strftime("%Y-%m-%d") for d in data["dates"] if d not in data["days"]]

                summary_table.append({
                    "الاسم": name,
                    "إجمالي ساعات العمل": f"{total_hours}س {total_minutes}د",
                    "عدد أيام الحضور": len(data["days"]),
                    "عدد مرات البصمة (دخول)": data["in_count"],
                    "عدد مرات البصمة (انصراف)": data["out_count"],
                    "أيام بدون حضور أو انصراف": ", ".join(missing_days) if missing_days else "لا يوجد"
                })

            st.dataframe(summary_table, use_container_width=True)

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {str(e)}")
