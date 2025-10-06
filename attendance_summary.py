import os
import pandas as pd
import re
from datetime import datetime

# Folder containing the CSV files
folder_path = r"C:\\Users\\kokoj\\Downloads\\B5_Teams_Att"

# List to store all attendance records
records = []

# Convert duration string to seconds
def parse_duration(duration_str):
    match = re.match(r'(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?', duration_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    return 0

# Extract time from string
def extract_time(time_str):
    match = re.search(r'(\d{1,2}:\d{2}:\d{2})', time_str)
    if match:
        return match.group(1)
    match = re.search(r'(\d{1,2}:\d{2}:\d{2}\s*[APMapm]{2})', time_str)
    if match:
        try:
            return datetime.strptime(match.group(1), "%I:%M:%S %p").strftime("%H:%M:%S")
        except:
            return "Unknown"
    return "Unknown"

# Remove illegal characters for Excel
def clean_excel_string(value):
    if isinstance(value, str):
        return re.sub(r'[\x00-\x1F\x7F]', '', value)
    return value

# Process each CSV file
for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.replace('\x00', '') for line in f.readlines()]

        meeting_title = next((line.split('\t', 1)[1].strip().strip('"') for line in lines if line.lower().startswith("meeting title") and '\t' in line), "Unknown")
        start_time_str = next((line.split('\t', 1)[1].strip() for line in lines if line.lower().startswith("start time") and '\t' in line), "Unknown")
        end_time_str = next((line.split('\t', 1)[1].strip() for line in lines if line.lower().startswith("end time") and '\t' in line), "Unknown")

        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', start_time_str)
        if date_match:
            month, day, year = date_match.groups()
            year = '20' + year if len(year) == 2 else year
            try:
                date_obj = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
                date_str = date_obj.strftime("%d-%b-%Y")
            except:
                date_str = "Unknown"
        else:
            date_str = "Unknown"

        start_time = extract_time(start_time_str)
        end_time = extract_time(end_time_str)
        meeting_duration_str = next((line.split('\t', 1)[1].strip() for line in lines if line.lower().startswith("meeting duration") and '\t' in line), "Unknown")
        total_meeting_seconds = parse_duration(meeting_duration_str)

        start = next((i for i, line in enumerate(lines) if line.startswith("Name\tFirst Join")), None)
        if start is not None:
            for line in lines[start + 1:]:
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    student_name = parts[0]
                    grade_match = re.match(r'G(\d{1,2})', student_name)
                    grade = f"Grade {grade_match.group(1)}" if grade_match else "Unknown"
                    student_start_time = extract_time(parts[1]) if len(parts) > 1 else "Unknown"
                    student_end_time = extract_time(parts[2]) if len(parts) > 2 else "Unknown"
                    student_duration_str = parts[3]
                    student_seconds = parse_duration(student_duration_str)
                    duration_percent = f"{round((student_seconds / total_meeting_seconds) * 100)}%" if total_meeting_seconds > 0 else "0%"
                    records.append({
                        "Meeting Title": meeting_title,
                        "Date": date_str,
                        "Start time": start_time,
                        "End time": end_time,
                        "Meeting Duration": meeting_duration_str,
                        "Grade or Class": grade,
                        "Student Name": student_name,
                        "Email": parts[4],
                        "Student Start Time": student_start_time,
                        "Student End Time": student_end_time,
                        "Total Duration": student_duration_str,
                        "Duration %": duration_percent,
                        "Source File": filename
                    })

# Create DataFrame
df = pd.DataFrame(records)

# Reorder columns to place 'Meeting Duration' after 'End time'
column_order = [
    "Meeting Title", "Date", "Start time", "End time", "Meeting Duration",
    "Grade or Class", "Student Name", "Email",
    "Student Start Time", "Student End Time",
    "Total Duration", "Duration %", "Source File"
]
df = df[column_order]

# Clean illegal characters
df = df.applymap(clean_excel_string)

# Save to CSV
output_path = os.path.join(folder_path, "All_Attendance_Summary.csv")
df.to_csv(output_path, index=False)

print("✅ All attendance records have been saved to All_Attendance_Summary.csv.")