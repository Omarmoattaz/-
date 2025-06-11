import streamlit as st
import pandas as pd
from datetime import datetime

st.title("تطبيق حساب الحضور والانصراف")

uploaded_file = st.file_uploader("ارفع ملف البصمة (Excel)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # تأكد من الأعمدة
        required_columns = ["Name", "Date", "Time", "Status"]
        if not all(col in df.columns for col in required_columns):
            st.error("⚠️ تأكد أن ملفك يحتوي على الأعمدة التالية: Name, Date, Time, Status")
        else:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            df["Time"] = pd.to_datetime(df["Time"].astype(str)).dt.time

            # تجميع التاريخ والوقت في عمود واحد datetime كامل
            df["DateTime"] = df.apply(lambda row: datetime.combine(row["Date"], row["Time"]), axis=1)

            df.sort_values(["Name", "DateTime"], inplace=True)

            result = []

            grouped = df.groupby(["Name", "Date"])
            for (name, date), group in grouped:
                in_times = group[group["Status"] == "C/In"]["DateTime"]
                out_times = group[group["Status"] == "C/Out"]["DateTime"]

                first_in = in_times.min() if not in_times.empty else None
                last_out = out_times.max() if not out_times.empty else None

                if first_in and last_out and last_out > first_in:
                    duration = last_out - first_in
                    hours = duration.total_seconds() // 3600
                    minutes = (duration.total_seconds() % 3600) // 60
                    work_time = f"{int(hours)}س {int(minutes)}د"
                else:
                    work_time = "--"

                result.append({
                    "الموظف": name,
                    "التاريخ": date,
                    "أول دخول": first_in.time().strftime("%H:%M") if first_in else "--",
                    "آخر انصراف": last_out.time().strftime("%H:%M") if last_out else "--",
                    "ساعات العمل": work_time
                })

            result_df = pd.DataFrame(result)
            st.success("✅ تم تحليل الملف بنجاح")
            st.dataframe(result_df)

            # زر التصدير
            @st.cache_data
            def convert_df(df):
                return df.to_excel(index=False, engine="openpyxl")

            st.download_button(
                label="⬇️ تحميل النتائج Excel",
                data=convert_df(result_df),
                file_name="الحضور_والانصراف.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
