import pandas as pd
import datetime

# Load the uploaded Excel file
file_path = "/mnt/data/sample_attendance.xlsx.xlsx"
df = pd.read_excel(file_path)

# Ensure proper column names
df.columns = df.columns.str.strip()

# Rename columns to match expected names
df = df.rename(columns={
    "Name": "الاسم",
    "Date": "التاريخ",
    "Time": "الوقت",
    "Status": "النوع"
})

# Filter to only necessary columns
df = df[["الاسم", "التاريخ", "الوقت", "النوع"]]

# Convert التاريخ to datetime and الوقت to time
df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors='coerce').dt.date
df["الوقت"] = pd.to_datetime(df["الوقت"].astype(str), format='%H:%M:%S').dt.time

# Remove rows with invalid dates
df = df.dropna(subset=["التاريخ"])

# Sort by name and datetime
df = df.sort_values(by=["الاسم", "التاريخ", "الوقت"])

# Group by employee and date
grouped = df.groupby(["الاسم", "التاريخ"])

# Prepare daily summaries
daily_summary = []
for (name, date), group in grouped:
    ins = group[group["النوع"] == "C/In"]["الوقت"].tolist()
    outs = group[group["النوع"] == "C/Out"]["الوقت"].tolist()

    first_in = min(ins) if ins else None
    last_out = max(outs) if outs else None

    # Calculate working hours
    ساعات_العمل = "--"
    if first_in and last_out:
        dt_in = datetime.datetime.combine(date, first_in)
        dt_out = datetime.datetime.combine(date, last_out)
        diff = dt_out - dt_in
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        ساعات_العمل = f"{hours}س {minutes}د"

    daily_summary.append({
        "الاسم": name,
        "التاريخ": date,
        "الحضور": first_in.strftime('%H:%M:%S') if first_in else "--",
        "الانصراف": last_out.strftime('%H:%M:%S') if last_out else "--",
        "ساعات العمل": ساعات_العمل
    })

daily_df = pd.DataFrame(daily_summary)

# Prepare summary table
summary = []
for name, group in daily_df.groupby("الاسم"):
    total_days = group.shape[0]
    work_days = group[(group["الحضور"] != "--") & (group["الانصراف"] != "--")]
    total_work_days = work_days.shape[0]
    
    total_minutes = 0
    for row in work_days["ساعات العمل"]:
        if row != "--":
            parts = row.split("س ")
            hours = int(parts[0])
            minutes = int(parts[1].replace("د", "")) if len(parts) > 1 else 0
            total_minutes += hours * 60 + minutes
    total_hours = total_minutes // 60
    remaining_minutes = total_minutes % 60

    summary.append({
        "الاسم": name,
        "عدد الأيام": total_days,
        "أيام العمل": total_work_days,
        "إجمالي ساعات العمل": f"{total_hours}س {remaining_minutes}د"
    })

summary_df = pd.DataFrame(summary)

daily_df.head(), summary_df.head()


            st.download_button(
                label="⬇️ تحميل النتائج Excel",
                data=excel_data,
                file_name="الحضور_والانصراف.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
