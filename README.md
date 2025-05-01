# Thermal Image SQL Database — Loyola LS Campus

This repository contains the SQLite database used to store thermal image data collected from windows on Loyola’s Lakeshore campus.

## Overview

The database consists of two tables:

- **`static`** — stores static window metadata (location, building, floor, side).  
- **`environment_logs`** — stores dynamic temperature readings and related information.

---

## Table: `static`

Stores static information about each window.

### Columns

| Column             | Type    | Description                                                            |
|--------------------|---------|------------------------------------------------------------------------|
| `location_id`      | TEXT    | Primary key (e.g., `ch_1_2` → Cuneo Hall, 1st floor, 3rd window).       |
| `building_name`    | TEXT    | Building name in lowercase with underscores (e.g., `cuneo_hall`).       |
| `floor_number`     | INTEGER | Floor number (`0` = basement, `1` = first floor, etc.).                |
| `side_of_building` | TEXT    | Cardinal direction in lowercase (e.g., `north`).                       |

---

## Table: `environment_logs`

Stores dynamic environmental readings linked to each window.

### Columns

| Column              | Type     | Description                                                                                  |
|---------------------|----------|----------------------------------------------------------------------------------------------|
| `log_id`            | INTEGER  | Auto-incremented unique ID for each log entry.                                               |
| `location_id`       | TEXT     | Foreign key referencing `static.location_id`.                                                |
| `outside_temp`      | REAL     | Outside temperature at the time of reading (°F).                                             |
| `min_temp`          | REAL     | Minimum temperature recorded on the window.                                                  |
| `max_temp`          | REAL     | Maximum temperature recorded on the window.                                                  |
| `time_taken_hours`  | INTEGER  | Hour of the day (0–23) when the reading was taken.                                           |
| `windows_opened`    | TEXT     | `'Y'` if the window was opened during logging; otherwise `'N'`.                              |
| `date`              | TEXT     | Date of the reading (`YYYY-MM-DD`).                                                          |
| `url_original`      | TEXT     | URL to the uncleaned thermal image in Google Drive.                                          |
| `url_clean`         | TEXT     | URL to the cleaned thermal image in Google Drive.                                            |

---

## Camera Setup Instructions

1. **Crosshair Settings**  
   Uncheck both boxes for **Rule** to remove red and blue crosshairs.

2. **Color Palette**  
   Select the palette without green (blue/purple on the left to yellow/white on the right).

3. **Measurement Settings**  
   - **Distance**: 10 m  
   - **Laser**: On  
   - **Unit**: Celsius  

4. **Branding**  
   Turn **Brand Logo** off.

---

## Uploading New Images

1. **Upload to Google Drive**  
   - Navigate to the folder for the respective building.  
   - Upload raw images (no renaming necessary if you know the `location_id`).

2. **Run `db_upload`**  
   - Execute the script to clean images and log temperature data.  
   - You will be prompted for `location_id`, `outside_temp`, `time_taken_hours`, and `windows_opened`.

---

## Requirements

- **Python 3.x**  
- Install dependencies:  
  ```bash
  pip install -r requirements.txt

- **Pytesseract**
- Add Tesseract to your system path (run the provided .exe in this repository).

