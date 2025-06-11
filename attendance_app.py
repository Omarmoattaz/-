import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="تحليل الحضور والانصراف", layout="centered")

st.title("📊 نظام تحليل البصمة")
uploaded_file = st.file_uploader("📎 ارفع ملف Excel من جهاز البصمة", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # التحقق من الأعمدة المطلوبة
        expected_columns = ['Department', 'Name', 'No.', 'Date', 'Time', 'Status']
        if not all(col in df.columns for col in expected_columns):
            st.error("❌ تأكد أن الأعمدة في الملف هي: Department, Name, No., Date, Time, Status")
        else:
            # دمج التاريخ والوقت
            df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), errors='coerce')
            df.dropna(subset=['DateTime'], inplace=True)
            df['DateOnly'] = df['DateTime'].dt.date
            df['TimeOnly'] = df['DateTime'].dt.time

            # تجهيز البيانات
            attendance_summary = []
            grouped = df.groupby(['Name', 'DateOnly'])

            for (name, date), group in grouped:
                in_times = group[group['Status'] == 'C/In']['DateTime'].sort_values()
                out_times = group[group['Status'] == 'C/Out']['DateTime'].sort_values()

                first_in = in_times.iloc[0].time() if not in_times.empty else None
                last_out = out_times.iloc[-1].time() if not out_times.empty else None

                # حساب ساعات العمل
                work_duration = None
                if first_in and last_out:
                    in_dt = datetime.combine(date, first_in)
                    out_dt = datetime.combine(date, last_out)
                    work_duration = out_dt - in_dt

                attendance_summary.append({
                    'الاسم': name,
                    'التاريخ': date,
                    'الحضور': first_in.strftime("%H:%M:%S") if first_in else "--",
                    'الانصراف': last_out.strftime("%H:%M:%S") if last_out else "--",
                    'ساعات العمل': f"{work_duration.seconds // 3600}س {(work_duration.seconds % 3600) // 60}د" if work_duration else "--",
                    'المدة': work_duration if work_duration else timedelta(0)
                })

            summary_df = pd.DataFrame(attendance_summary)

            # عرض الجدول اليومي
            st.subheader("📅 الجدول اليومي")
            st.dataframe(summary_df.drop(columns=['المدة']))

            # ملخص إجمالي لكل موظف
            st.subheader("📌 ملخص لكل موظف")
            final_summary = summary_df.groupby('الاسم').agg({
                'التاريخ': 'count',
                'المدة': 'sum'
            }).reset_index()
            final_summary.rename(columns={
                'التاريخ': 'عدد أيام العمل',
                'المدة': 'إجمالي الساعات'
            }, inplace=True)

            # تنسيق مدة الوقت
            def format_timedelta(td):
                total_minutes = int(td.total_seconds() // 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                return f"{hours}س {minutes}د"

            final_summary['إجمالي الساعات'] = final_summary['إجمالي الساعات'].apply(format_timedelta)
            st.dataframe(final_summary)

            # تحميل النتائج
            output_file = pd.ExcelWriter("تحليل_الحضور.xlsx", engine="openpyxl")
            summary_df.drop(columns=['المدة']).to_excel(output_file, sheet_name="الحضور اليومي", index=False)
            final_summary.to_excel(output_file, sheet_name="ملخص الموظف", index=False)
            output_file.close()

            with open("تحليل_الحضور.xlsx", "rb") as file:
                st.download_button("⬇️ تحميل النتيجة كـ Excel", file.read(), file_name="تحليل_الحضور.xlsx")

    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء قراءة الملف: {e}")
